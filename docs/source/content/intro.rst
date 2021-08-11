
Motivation
-----------

The serialization protocols implemented by this module have the following aims:

* **Readability** / ease of **manual editing** of serialized format.
* Ease of **extensibility** with minimal coding overhead - Classes can become serializable by deriving from :class:`~xerializer.Serializable` and implementing :meth:`~xerializer.Serializable.as_serializable` and optionally :meth:`~xerializer.Serializable.from_serializable`.
* **Code unobstrusiveness** - Custom objects can also be made serializable by instead implementing a stand-alone :class:`~xerializer.TypeSerializer`, setting :attr:`~xerializer.TypeSerializer.handled_type` to the class to make serializable.
* **Syntax unobtrusiveness** - JSON/YAML-compatible base types (numeric types, ``list``, ``dict``) are converted to serializable objects without any added verbosity :ref:`[1]<Syntax Overhead>` . Custom serializable types are serialized as dictionaries with a ``__type__``.
* **Builtin type** (``tuple``, ``set``, ``slice``) support out-of-the-box.
* **Numpy** support (``numpy.dtype``,  ``numpy.ndarray``), including (nested and/or shaped) structured dtypes out-of-the-box.
* **Safety** - Only :class:`~xerializer.Serializable` objects or those with a :class:`~xerializer.TypeSerializer` will be deserialized into objects by :class:`~xerializer.Serializer`, and users have fine-grained control of enabled third-party and builtin plugins.

Syntax
========
The contents or :attr:`__args__` and :attr:`__kwargs__` can be any serializable type. When pre-fixed by ``'@py:'``, they can also be string representation of standard python objects (``byte``, ``tring``, ``int``, ``float``, ``list``, ``tuple``, ``set``, ``dict``, and any other supported by python's :meth:`ast.literal_eval`).

Syntax Overhead
================
JSON/YAML-compatible base types are converted to serializable objects without any added verbosity. The exception is dictionaries that contain the key ``__type__``. Such dictinoaries are represented in the following more verbose form:

.. code-block::

  {'__type__': 'dict',
   'value': <original dictionary>}



Composibility
===============


Getting started
----------------

.. testcode:: get_started

   from xerializer import Serializer
   serializer = Serializer()

   # Get a human-readable string representation of a supported object
   my_object = [{'key1':'val1', 'key2':[1,2,3]}, 
                ('tuple1', 'tuple2'), 
                {'set1', 'set2'}, 
		slice(None,30)]
   my_object_str = serializer.serialize(my_object)
   print(my_object_str)
   
.. testoutput:: get_started
   
   [{"key1": "val1", "key2": [1, 2, 3]}, {"__type__": "tuple", "value": ["tuple1", "tuple2"]}, {"__type__": "set", "value": ["set2", "set1"]}, {"__type__": "slice", "stop": 30}]   

.. testcode:: get_started
   
   print(my_object == serializer.deserialize(my_object_str))

.. testoutput:: get_started

   True


Examples of all builtin-types can be found in :ref:`Examples`.
    


Serializing custom types
---------------------------

There are two approaches to support custom types: By having the custom type derive from :class:`~xerializer.Serializable` -- this requires modifying the source code for that class. Or by creating a stand-alone :class:`~xerializer.TypeSerializer` -- a less obtrusive approach.

Regardless of the approach, the user is responsible for implementing a method :meth:`as_serializable` that maps the custom class to a dictionary with values that are builtin or custom serializable types. By default, this dictionary is used as keyword arguments for method :meth:`from_serializable` which is, by default, the handled type's :meth:`__init__`.


... by making the class a :class:`~xerializer.Serializable`
============================================================

A custom type can be made serializable by inheriting from :class:`xerializer.Serializable` and implementing method :meth:`~xerializer.Serializable.as_serializable`. Optionally, the custom class can also implement class method :meth:`~xerializer.Serializable.from_serializable` and set class attributes :attr:`~xerializer.Serializable.signature` and :attr:`~xerializer.Serializable.register`.

.. testcode::

    # CREATING A SERIALIZABLE CLASS 

    # Contents of 'my_serializable_module.py'
    from xerializer import Serializable
    
    class MySerializable(Serializable):
        def __init__(self, arg1, arg2):
            self.arg1 = arg1
            self.arg2 = arg2

        # Required
        def as_serializable(self):
            return {'arg1': self.arg1, 'arg2': self.arg2}

        # Optional (defaults shown)
        # (Serializer.from_serializable is a **class** method)
        @classmethod
        def from_serializable(cls, **kwargs):
            return cls(**kwargs)
        signature = 'my_serializable_module.MySerializable'
        register = True

    # To serialize a type, the Serializable needs to be declared before 
    # Serializer is instantiated.
    from xerializer import Serializer
    print(Serializer().serialize(MySerializable(1,2)))

.. testoutput::

    {"__type__": "my_serializable_module.MySerializable", "arg1": 1, "arg2": 2}


... with a stand-alone :class:`~xerializer.TypeSerializer`
=================================================================

For classes that already exist, one can instead create a standalone type serializer without needing to modify the original source code:

.. testcode::

    # CREATING A STANDALONE TYPE SERIALIZER FOR AN EXISTING CLASS

    # An existing class in module 'my_non_serializable_module.py'
    class MyNonSerializable:
        def __init__(self, arg1, arg2):
            self.arg1 = arg1
            self.arg2 = arg2


    # A type serializer that handles MyNonSerializable
    from xerializer import TypeSerializer
    
    class MyClassSerializer(TypeSerializer):

        # Required
        handled_type = MyNonSerializable
        def as_serializable(self, obj):
            return {'arg1': obj.arg1, 'arg2': obj.arg2}

        # Optional (defaults shown)
        # (TypeSerializer.from_serializable is a regular **instance** method)
        def from_serializable(cls, **kwargs):
            return cls(**kwargs)
        signature = 'my_non_serializable_module.MyNonSerializable'
        register = True

    # To serialize a type, the custom TypeSerializer needs to be declared
    # before the Serializer is instantiated.
    from xerializer import Serializer
    print(Serializer().serialize(MyNonSerializable(1,2)))

.. testoutput::

    {"__type__": "my_non_serializable_module.MyNonSerializable", "arg1": 1, "arg2": 2}

