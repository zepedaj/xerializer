import functools
from .abstract_type_serializer import TypeSerializer as _TypeSerializer
import inspect


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
    def as_serializable(self, obj):
        out = []

        parameter_defs = obj._xerializable_params['sgntr'].parameters

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
                pass

            # Append argument
            out.append((bound_name, value))

        return dict(out)

    def from_serializable(self, **kwargs):
        sgntr = inspect.signature(self.handled_type.__init__)
        params = sgntr.bind_partial(None)  # Temporarily set self
        params.arguments.update(kwargs)
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


def serializable(explicit_defaults: bool = True, signature=None):
    """
    Class decorator that makes the class serializable. See discussion in :ref:`Serializable decorator <Serializable decorator>`.

    :param explicit_defaults: [True] Serialize default values explicitly.
    :param signature: The xerializable signature -- a human readable global string specifier for the class. Defaults to the fully-qualified class name.
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
