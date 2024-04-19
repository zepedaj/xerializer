import functools
from .abstract_type_serializer import TypeSerializer as _TypeSerializer
import inspect
from jztools.validation import checked_get_single
from jztools.py import entity_name
from typing import Union, Type, Callable


def _serializable_init_wrapper(cls_init, apply_defaults):
    @functools.wraps(cls_init)
    def wrapper(self, *args, **kwargs):
        sgntr = inspect.signature(cls_init)
        if not hasattr(self, "_xerializable_params"):
            # Will only execute for the child-most class.
            bound = sgntr.bind(self, *args, **kwargs)
            if apply_defaults:
                bound.apply_defaults()
            self._xerializable_params = {"sgntr": sgntr, "bound": bound}
        cls_init(self, *args, **kwargs)

    return wrapper


class _DecoratedTypeSerializer(_TypeSerializer):
    kwargs_level = "auto"

    def as_serializable(self, obj):
        out = []

        parameter_defs = obj._xerializable_params["sgntr"].parameters

        # Check if the args name is in the kwargs.
        args_param = checked_get_single(
            [
                _p
                for _p in parameter_defs.values()
                if _p.kind is inspect.Parameter.VAR_POSITIONAL
            ]
            or [None]
        )
        kwargs_param = checked_get_single(
            [
                _p
                for _p in parameter_defs.values()
                if _p.kind is inspect.Parameter.VAR_KEYWORD
            ]
            or [None]
        )
        kwargs_args_name_crash_detected = (
            args_param
            and kwargs_param
            and args_param.name in obj._xerializable_params["bound"].arguments
            and kwargs_param.name in obj._xerializable_params["bound"].arguments
            and args_param.name
            in obj._xerializable_params["bound"].arguments[kwargs_param.name]
        )
        if kwargs_args_name_crash_detected and self.kwargs_level == "root":
            raise Exception(
                f"Option kwargs_level='root' is not compatible with variable positional arg name {args_param.name} of same name as a variable keyword arg. "
                f"Use one of 'safe' or 'auto' instead."
            )

        # Append each argument one at a time.
        for param_num, (bound_name, value) in enumerate(
            obj._xerializable_params["bound"].arguments.items()
        ):

            # Skip self argument
            if param_num == 0:
                continue

            # Do not serialize empty positional / keyword arg lists.
            param = parameter_defs[bound_name]
            if (
                param.kind is inspect.Parameter.VAR_POSITIONAL and value == tuple()
            ) or (param.kind is inspect.Parameter.VAR_KEYWORD and value == {}):
                continue

            # Serialize variable arguments as a list
            if param.kind is inspect.Parameter.VAR_POSITIONAL:
                value = list(value)

            # Append dereferenced **kwargs
            if (
                param.kind is inspect.Parameter.VAR_KEYWORD
                and self.kwargs_level in ["auto", "root"]
                and not kwargs_args_name_crash_detected
            ):
                out.extend(list(value.items()))

            # Append other values
            else:
                out.append((bound_name, value))

        return dict(out)

    def from_serializable(self, **kwargs):
        # TODO: Bug, does not raise an error if kwargs contains invalid argument names
        sgntr = inspect.signature(self.handled_type)

        # Collect VAR_KEYWORD args
        if self.kwargs_level in ["auto", "root"] and (
            var_kw_param := [
                _p
                for _p in sgntr.parameters.values()
                if _p.kind is inspect.Parameter.VAR_KEYWORD
            ]
        ):
            var_keywords = {
                key: kwargs.pop(key)
                for key in list(kwargs)
                if key not in sgntr.parameters.keys()
            }
        else:
            var_keywords = None

        # Bind parameters
        params = sgntr.bind_partial()  # (None)  # Temporarily set self
        params.arguments.update(kwargs)
        if var_keywords:
            params.arguments.setdefault(var_kw_param[0].name, {}).update(var_keywords)

        # Return instantiated object.
        return self.handled_type(*params.args, **params.kwargs)

    @classmethod
    def create_derived_class(cls, handled_type, name=None, **attributes):
        name = name or (f"_{handled_type.__name__}_DecoratedTypeSerializer")
        return type(
            name,
            (cls,),
            {"handled_type": handled_type, "__module__": __name__, **attributes},
        )


def serializable(
    _wrapped=None,
    *,
    explicit_defaults: bool = True,
    signature=None,
    kwargs_level="auto",
) -> Union[Type, Callable]:
    """

    Decorator that makes a class serializable, or a callable (includes class methods) de-serializable.

    .. note:: Class methods need to have the ``@serializable`` decorator outside the ``@classmethod`` decorator to avoid a ``TypeError: [classmethod name] missing 1 required position argument: '[class argument name]'`` error. The restriction does not apply to ``@staticmethod``-decorated methods.

    .. todo:: Add examples for callables in intro, including functions, bound classmethods and instance methods.

    See discussion in :ref:`Serializable decorator <Serializable decorator>`.

    :param explicit_defaults: [True] Serialize default values explicitly.
    :param signature: [Fully-qualified class name] The xerializable signature -- a human readable global string specifier for the class.
    :param kwargs_level: ['auto'] Whether to place kwargs (``kwargs_level = 'root'``) at the root level of the serializable or (``kwargs_level='safe'``) within their own field named like the variable keywords parameter of the decorated class's initializer. By default (``kwargs_level = 'auto'``) the root level will be used when possible, and a dedicated level will be used otherwise. See the discussion in :ref:`Decorator serialization syntax`.
    """

    def fxn(obj):

        if isinstance(obj, type):
            # Class serializable
            obj.__init__ = _serializable_init_wrapper(
                obj.__init__, apply_defaults=explicit_defaults
            )
            attributes = {"kwargs_level": kwargs_level}
            if signature:
                attributes["signature"] = signature
            _DecoratedTypeSerializer.create_derived_class(obj, **attributes)
            return obj

        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            # Function and static method serializable
            attributes = {"signature": signature or entity_name(obj)}
            _DecoratedCallableDeserializer.create_derived_class(
                functools.wraps(obj)(staticmethod(obj)), **attributes
            )
            return obj

        elif isinstance(obj, (classmethod, staticmethod)):
            # @classmethod serializable
            return _serializable_classmethod(signature=signature)(obj)

        else:
            raise Exception(
                f"Type {type(obj)} not currently supported by @serializable decorator."
            )

    if _wrapped is not None:
        return fxn(_wrapped)
    else:
        return fxn


class _DecoratedCallableDeserializer(_DecoratedTypeSerializer):
    as_serializable = None


class _serializable_classmethod:
    def __init__(self, signature=None):
        self.signature = signature

    def __call__(self, fn):
        self.fn = fn
        return self

    def __set_name__(self, owner, name):

        setattr(owner, name, self.fn)  # Binding happens here.
        bound_method = getattr(owner, name)
        obj = bound_method

        attributes = {"signature": self.signature or entity_name(obj)}
        _DecoratedCallableDeserializer.create_derived_class(
            functools.wraps(obj)(staticmethod(obj)), **attributes
        )
