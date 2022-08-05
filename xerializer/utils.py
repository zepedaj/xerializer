"""
Pickling and |Process| parameter passing support. Use wrapper :class:`AsPickleable` to make the pickled representation of the object be the xerializer serialization of the object. Use :class:`AsProcessParam` to pass parameters to |Process| objects using :class:`AsPickleable` when pickling is required.
"""

from .serializer import Serializer

from multiprocessing import Process, get_start_method


class AsPickleable:
    """
    Takes a serializable object and returns a new object that pickles using xerializer serialization, and unpickles to the deserialized object.

    The pickled object will include the original serializer.

    .. warning:: This class relies on accepts an input |Serializer| that is itself serialized using the |Serializer| in class attribute :attr:`bootstrap_serializer`.

    .. warning:: The standard pickle safety warnings apply.

    """

    bootstrap_serializer = Serializer()
    """
    Used to serialize the input serializer.
    """

    process = Process()

    def __init__(self, obj, serializer: Serializer = None):
        self.serialized_serializer = self.bootstrap_serializer.serialize(
            serializer := (serializer or Serializer())
        )
        self.serialized_obj = serializer.serialize(obj)

    @classmethod
    def _restore(cls, serialized_obj, serialized_serializer):
        serializer = cls.bootstrap_serializer.deserialize(serialized_serializer)
        obj = serializer.deserialize(serialized_obj)
        return obj

    def __reduce__(self):
        out = self._restore, (self.serialized_obj, self.serialized_serializer)
        return out


class AsProcessParam(AsPickleable):
    """
    When sending parameters to a |Process| object, whether these are pickled or not depends on the `process start method <https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods>`_. See `this stackoverflow answer <https://stackoverflow.com/a/26026069>`_ .

    This wrapper abstracts away this behavior, relying on :class:`AsPickleable` when pickling is involved, and behaving as a no-op when it is not.

    .. note:: Parameters are always pickled when using `ProcessPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor>`_ instances -- you hence need to use class :class:`AsPickleable` instead of :class:`AsProcessParam` when using that process management method.

    .. warning:: Instantiating this class calls `multiprocessing.get_start_method() <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.get_start_method>`_ with ``allow_none=False`` and hence implicitly fixes the process start method (if it has not been set before) to the platform-dependent default.

    .. warning:: The returned object will be stateless when :class:`AsPickleable` is used under the hood -- the unpickled object will be a newly-instantiated instance. When it is not (e.g., when forking), the state of the object will be preserved, as an exact copy of the process is created by the forking operation.

    """

    def __new__(cls, obj, *args, **kwargs):

        start_method = get_start_method()
        if start_method in ["fork", "forkserver"]:
            return obj
        elif start_method == "spawn":
            return super.__new__(cls, *args, **kwargs)
        else:
            raise Exception("Unexpected case.")
