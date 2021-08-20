import functools
from .abstract_type_serializer import TypeSerializer as _TypeSerializer
import inspect
from pglib.validation import checked_get_single


def _serializable_init_wrapper(cls_init, apply_defaults):

    @functools.wraps(cls_init)
    def wrapper(self, *args, **kwargs):
        sgntr = inspect.signature(cls_init)
        bound = sgntr.bind(self, *args, **kwargs)
        if apply_defaults:
            bound.apply_defaults()
        cls_init(self, *args, **kwargs)
        self._xerializable_params = {'sgntr': sgntr, 'bound': bound}

    return wrapper


class _DecoratedTypeSerializer(_TypeSerializer):
    kwargs_level = 'auto'

    def as_serializable(self, obj):
        out = []

        parameter_defs = obj._xerializable_params['sgntr'].parameters

        # Check if the args name is in the kwargs.
        args_param = checked_get_single(
            [_p for _p in parameter_defs.values() if _p.kind is inspect.Parameter.VAR_POSITIONAL] or
            [None])
        kwargs_param = checked_get_single(
            [_p for _p in parameter_defs.values() if _p.kind is inspect.Parameter.VAR_KEYWORD] or
            [None])
        kwargs_args_name_crash_detected = (
            args_param and kwargs_param and
            args_param.name in obj._xerializable_params['bound'].arguments and
            kwargs_param.name in obj._xerializable_params['bound'].arguments and
            args_param.name in obj._xerializable_params['bound'].arguments[kwargs_param.name])
        if kwargs_args_name_crash_detected and self.kwargs_level == 'root':
            raise Exception(
                f'Option kwargs_level=\'root\' is not compatible with variable positional arg name {args_param.name} of same name as a variable keyword arg. '
                f'Use one of \'safe\' or \'auto\' instead.')

        # Append each argument one at a time.
        for param_num, (bound_name, value) in enumerate(
                obj._xerializable_params['bound'].arguments.items()):

            # Skip self argument
            if param_num == 0:
                continue

            # Do not serialize empty positional / keyword arg lists.
            param = parameter_defs[bound_name]
            if (
                    (param.kind is inspect.Parameter.VAR_POSITIONAL and value == tuple()) or
                    (param.kind is inspect.Parameter.VAR_KEYWORD and value == {})):
                continue

            # Serialize variable arguments as a list
            if param.kind is inspect.Parameter.VAR_POSITIONAL:
                value = list(value)

            # Append dereferenced **kwargs
            if (param.kind is inspect.Parameter.VAR_KEYWORD and
                self.kwargs_level in ['auto', 'root'] and
                    not kwargs_args_name_crash_detected):
                out.extend(list(value.items()))

            # Append other values
            else:
                out.append((bound_name, value))

        return dict(out)

    def from_serializable(self, **kwargs):
        sgntr = inspect.signature(self.handled_type.__init__)

        # Collect VAR_KEYWORD args
        if self.kwargs_level in ['auto', 'root'] and (var_kw_param := [
                _p for _p in sgntr.parameters.values()
                if _p.kind is inspect.Parameter.VAR_KEYWORD]):
            var_keywords = {key: kwargs.pop(key) for key in list(kwargs) if
                            key not in sgntr.parameters.keys()}
        else:
            var_keywords = None

        # Bind parameters
        params = sgntr.bind_partial(None)  # Temporarily set self
        params.arguments.update(kwargs)
        if var_keywords:
            params.arguments.setdefault(var_kw_param[0].name, {}).update(
                var_keywords)

        # Return instantiated object.
        return self.handled_type(*params.args[1:], **params.kwargs)

    @classmethod
    def create_derived_class(cls, handled_type, name=None, **attributes):
        name = name or (f'_{handled_type.__name__}_DecoratedTypeSerializer')
        return type(
            name,
            (cls,),
            {
                'handled_type': handled_type,
                '__module__': __name__,
                **attributes

            })


def serializable(explicit_defaults: bool = True, signature=None, kwargs_level='auto'):
    """
    Class decorator that makes the class serializable. See discussion in :ref:`Serializable decorator <Serializable decorator>`.

    :param explicit_defaults: [True] Serialize default values explicitly.
    :param signature: [Fully-qualified class name] The xerializable signature -- a human readable global string specifier for the class.
    :param kwargs_level: ['auto'] Whether to place kwargs (``kwargs_level = 'root'``) at the root level of the serializable or (``kwargs_level='safe'``) within their own field named like the variable keywords parameter of the decorated class's initializer. By default (``kwargs_level = 'auto'``) the root level will be used when possible, and a dedicated level will be used otherwise. See the discussion in XXX.
    """

    def fxn(obj):
        # Class serializable
        if isinstance(obj, type):
            obj.__init__ = _serializable_init_wrapper(
                obj.__init__, apply_defaults=explicit_defaults)
            attributes = {'signature': signature} if signature else {}
            _DecoratedTypeSerializer.create_derived_class(obj, **attributes)
        else:
            raise Exception('Type {type(obj)} not currently supported.')

        return obj

    return fxn
