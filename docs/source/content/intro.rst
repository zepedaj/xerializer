
Motivation
-----------

The serialization protocols implemented by this module have the following aims:

* **Readability** / ease of **manual editing** of serialized format.
* Ease of **extensibility** with minimal coding overhead - Most classes can become serializable simply by decorating them with :class:`@serializable() <xerializer.serializable>`. More flexibility can be obtained by deriving from :class:`~xerializer.Serializable`.
* **Code unobstrusiveness** - Custom objects can also be made serializable by instead implementing a stand-alone :class:`~xerializer.TypeSerializer`, setting :attr:`~xerializer.TypeSerializer.handled_type` to the class to make serializable -- this approach offers the most flexibility. 
* **Syntax unobtrusiveness** - JSON/YAML-compatible base types (numeric types, ``str``, ``list``, ``dict``) are converted to serializable objects without any added verbosity :ref:`[1] <Syntax Overhead>`. Custom serializable types are serialized as dictionaries with a ``__type__`` key.
* **Builtin type** (``tuple``, ``set``, ``slice``) support out-of-the-box.
* **Numpy** support (``numpy.dtype``,  ``numpy.ndarray``, ``numpy.datetime64``), including (nested and/or shaped) structured dtypes out-of-the-box.
* **Safety** - Only :class:`~xerializer.Serializable` objects or those with a :class:`~xerializer.TypeSerializer` will be deserialized into objects by :class:`~xerializer.Serializer`, and users have fine-grained control of enabled third-party and builtin plugins.

.. todo:: Document numpy support, including the `_as_bytes` options and how to enable them.

Syntax
========

See :ref:`Examples` for example serializations of various builtin Python types.

.. _Syntax Overhead:

Syntax Overhead
================

JSON/YAML-compatible base types are converted to serializable objects without any added verbosity. The exception is dictionaries that contain the key ``__type__``. Such dictionaries are represented in the following more verbose form:

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

.. testcode:: get_started
   :hide:

   my_object_str = my_object_str.replace('"set2", "set1"', '"set1", "set2"')
   
.. testcode:: get_started

   assert my_object == serializer.deserialize(my_object_str)
   print(my_object_str)   
   
.. testoutput:: get_started
   
   [{"key1": "val1", "key2": [1, 2, 3]}, {"__type__": "tuple", "value": ["tuple1", "tuple2"]}, {"__type__": "set", "value": ["set1", "set2"]}, {"__type__": "slice", "stop": 30}]   


Examples of all builtin-types can be found in :ref:`Examples`.
    


Serializing custom types
---------------------------

.. todo:: Change intro to reflect ``@serializable`` discussion. Move this discussion to the top of the list.

There are two approaches to support custom types: By having the custom type derive from :class:`~xerializer.Serializable` -- this requires modifying the source code for that class. Or by creating a stand-alone :class:`~xerializer.TypeSerializer` -- a less obtrusive approach.

Regardless of the approach, the user is responsible for implementing a method :meth:`as_serializable` that maps the custom class to a dictionary with values that are builtin or custom serializable types. By default, this dictionary is used as keyword arguments for method :meth:`from_serializable` which is, by default, the handled type's :meth:`__init__`.


... by making the class a :class:`~xerializer.Serializable`
============================================================

A custom type can be made serializable by inheriting from :class:`xerializer.Serializable` and implementing method :meth:`~xerializer.Serializable.as_serializable`. Optionally, the custom class can also implement class method :meth:`~xerializer.Serializable.from_serializable` and set class attributes :attr:`~xerializer.Serializable.signature` and :attr:`~xerializer.Serializable.register`.

.. testcode::

    # CREATING A SERIALIZABLE CLASS 

    #############################################################
    # An new class that derives `Serializable` 
    #############################################################

    from xerializer import Serializable
    
    class MySerializable(Serializable):
        def __init__(self, arg1, arg2):
            self.arg1 = arg1
            self.arg2 = arg2

	############################
        # Required
	############################

        def as_serializable(self):
            return {'arg1': self.arg1, 'arg2': self.arg2}

	############################
        # Optional (defaults shown)
	############################

        @classmethod
        def from_serializable(cls, **kwargs):
            return cls(**kwargs)

        signature = '<module name>:MySerializable'

        register = True

    ###################################################
    # To serialize a type,  `MySerializable` needs to 
    # be declared before `Serializer` is instantiated.
    ###################################################
    
    from xerializer import Serializer
    print(Serializer().serialize(MySerializable(1,2)))

.. testoutput::

    {"__type__": "my_serializable_module.MySerializable", "arg1": 1, "arg2": 2}


.. _stand-alone TypeSerializer:

... with a stand-alone :class:`~xerializer.TypeSerializer`
=================================================================

For classes that already exist, one can instead create a standalone type serializer without needing to modify the original source code:

.. testcode::

    # CREATING A STANDALONE TYPE SERIALIZER FOR AN EXISTING CLASS

    #############################################################
    # An existing class that cannot be modified 
    # in module `my_package.my_non_serializable_module`
    #############################################################

    class MyNonSerializable:
        def __init__(self, arg1, arg2):
            self.arg1 = arg1
            self.arg2 = arg2


    ####################################################
    # A type serializer to handle `MyNonSerializable`
    # in module `_my_xerializer`
    ####################################################

    # from my_package.my_non_serializable_module import MyNonSerializable
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
        signature = 'my_non_serializable_module:MyNonSerializable'
        register = True

	
    ####################################
    # Serializing the custom type    
    ####################################

    # To serialize a type, the custom module containing MyClassSerializer needs to be imported
    # before the Serializer is instantiated. Importing the module declares the class,
    # which automatically registers it

    # import _my_xerializer
    from xerializer import Serializer
    print(Serializer().serialize(MyNonSerializable(1,2)))

.. testoutput::

    {"__type__": "my_non_serializable_module.MyNonSerializable", "arg1": 1, "arg2": 2}

.. _Serializable decorator:

... with the ``serializable`` class decorator
=================================================

The module also exposes an :meth:`@serializable() <xerializer.serializable>` class decorator that greatly simplifies the process of making custom types serializables for the special case of classes that 

#. are initialized only with serializable arguments and 
#. have initializer signature that are all introspectable with `inspect.signature <https://docs.python.org/3/library/inspect.html#inspect.signature>`_ -- this includes the vast majority of methods, including those with ``*args`` and ``**kwargs`` arguments.

Classes decorated with :meth:`@serializable() <xerializer.serializable>` will have the ``__init__`` method wrapped in a function that appends an attribute ``_xerializable_params`` to the instantiated object. The decorator can also be used as a stand-alone function to make an existing class serializable -- note that this also modifies the class initializer and needs to be done before instantiating the class.

Unlike classes deriving from :class:`xerializer.Serializable`, classes derived from :meth:`@serializable() <xerializer.serializable>`-decorated classes do not inherit the serializable quality.


.. rubric:: Example: Using ``serializable`` as a decorator

:func:`serializable` can be used as a class, method or function decorator, automatically making instances of these objects serializable, and calls to these methods or functions de-serializable.

.. testcode::

   from xerializer import Serializer, serializable

   #####################################################
   # Using serializable as a decorator.
   # `signature` optional, defaults to fully qualified
   # class name.
   #####################################################
   @serializable(signature='MyClass1') 
   class MyClass1:
     def __init__(self, a, b=2):
       self.a = a
       self.b = b
     def __eq__(self, x):
       return self.a == x.a and self.b == x.b      

.. testcode::

   ###########################
   # Serializing/deserializing
   ###########################

   # The `serializable`-decorated class declaration needs to happen before `Serializer` is instantiated.
   >>> srlzr = Serializer()

   >>> mc1 = MyClass1(1)
   >>> mc1_srlzd = srlzr.serialize(mc1)
   >>> assert mc1 == srlzr.deserialize(mc1_srlzd)   
   >>> print(mc1_srlzd)
   {"__type__": "MyClass1", "a": 1, "b": 2}

.. rubric:: Example: Using ``serializable`` as a function

Using ``serializable`` as a function makes it possible to register classes without modifying their source code, similarly to the approach that uses a :ref:`stand-alone type serializer <stand-alone TypeSerializer>`.

.. testcode:: 

   #########################################
   # The target class to make serializable.
   #########################################

   class MyClass2(MyClass1): 
     def __init__(self, a, *args, b=2, **kwargs):
       self.a = a
       self.b = b

   #########################################
   # Using `serializable` as a function
   #########################################

   # Setting explicit_defaults=False means that defaults such as b=2 are
   # not serialized. 
   # The default is explicit_defaults=True.

   MyClass2 = serializable(explicit_defaults=False, signature='MyClass2')(MyClass2) 

.. testcode::

   ###########################
   # Serializing/deserializing
   ###########################

   # The `serializable` call needs to happen before `Serializer` is instantiated.
   >>> srlzr = Serializer()
   #
   >>> mc2 = MyClass2(3)
   >>> mc2_srlzd = srlzr.serialize(mc2)
   >>> assert mc2 == srlzr.deserialize(mc2_srlzd)
   >>> print(mc2_srlzd)
   {"__type__": "MyClass2", "a": 3}
   

.. _Decorator serialization syntax:

.. rubric:: Decorator serialization syntax

Type serializers generated automatically with the ``@serializable`` decorator will attempt to produce serializations that are compact and human-readable:

.. testcode::

  print(srlzr.serialize(MyClass2(1, 2, 3, b=10, c=20, d=30)))

.. testoutput::

   {"__type__": "MyClass2", "a": 1, "args": [2, 3], "b": 10, "c": 20, "d": 30}

.. todo:: Won't this clashes also happen if a keyword arg has the name ``kwargs``?

This syntax will create name clashes when one of the variable keywords has the same name ``'args'`` as the variable positional argument ``*args``, a situation that is detected automatically and addressed with a more verbose syntax:

.. testcode::  

  # The keyword 'args' has the same name as the variable positional 
  # argument '*args' in the signature of MyClass2.__init__
  print(srlzr.serialize(MyClass2(1, 2, 3, b=10, c=20, d=30, args=40)))

.. testoutput::

   {"__type__": "MyClass2", "a": 1, "args": [2, 3], "b": 10, "kwargs": {"c": 20, "d": 30, "args": 40}}

The :meth:`~xerializer.serializable` decorator takes a ``kwargs_level`` argument that can be used to explicitly choose the more compact syntax (``kwargs_level='root'``) in situations where the user is sure no clashes will occur (detected name clashes will raise an exception). The more verbose but safe syntax can also be set explicitly (``kwargs_level='safe'``). By default, the choice is done automatically on-the-fly (``kwargs_level='auto'``).



Registering custom types
-------------------------

By default, all non-abstract class derived from :class:`~xerializer.TypeSerializer` (including those generated automatically for non-abstract :class:`~xerializer.Serializable` derived types, and those decorated with :meth:`~xerializer.serializable`) are automatically registered by module :mod:`xerializer`. This means that any :class:`Serializer` instantiated after their definition will by default include those plugins.

This behavior can be customized (except for the decorator syntax) using class variable ``register`` and metaclass variable ``register_meta``. Both variables can be used when deriving from either :class:`~xerializer.Serializable` or :class:`~xerializer.TypeSerializer`.


Using the ``register`` class variable
========================================
	    
Class variable ``register`` specifies whether a given class and all its derived children classes are registered (only non-abstract :class:`~xerializer.Serializable` or :class:`~xerializer.TypeSerializer`-derived classes are registered):

.. testcode:: register,register_meta

   from xerializer import TypeSerializer, get_registered_serializers
	      
   class MyClass:
     pass

.. testcode:: register,register_meta
   :hide:

   from xerializer import clear_registered_serializers
   clear_registered_serializers()     

   
.. testcode:: register
   
   class MyTypeSerializer(TypeSerializer):
     """
     This and all derived classes are registered automatically because
     they are non-abstract and TypeSerializer.register=True.
     """     
     handled_type = MyClass
     def as_serializable(self):
       pass

   class MyTypeSerializerUnregistered(MyTypeSerializer):
     """
     This and all derived classes are not registered automatically despite
     being non-abstract since register=False.
     """
     register = False

   print(get_registered_serializers())

.. testoutput:: register

   {'as_serializable': [<class 'MyTypeSerializer'>], 'from_serializable': [<class 'MyTypeSerializer'>]}

Using the ``register_meta`` keyword
===============================================

Metaclass keyword ``register_meta`` is passed in as a class definition keyword argument and can be one of ``None, True, False``. If ``None`` (the default), it has no effect. If ``True`` or ``False``, it overrides the ``register`` class variable but only affects the class being defined and not its children:

.. testcode:: register_meta
   :hide:

   from xerializer import clear_registered_serializers
   clear_registered_serializers()


.. testcode:: register_meta

   class MyChildSerializer(TypeSerializer, register_meta=False):
     """
     This class is not registered despite being non-abstract since register_meta is False.
     All derived classes will be registered since register=True.
     """
     register = True
     handled_type = MyClass
     def as_serializable(self):
       pass

   class MyGrandchildSerializer(MyChildSerializer):
     """
     This class is registered since its parent has register=True.
     """
     pass

   print(get_registered_serializers())

.. testoutput:: register_meta

   {'as_serializable': [<class 'MyGrandchildSerializer'>], 'from_serializable': [<class 'MyGrandchildSerializer'>]}


Using ``register_meta=True`` is also a good way to debug class registration issues, as it will force class registration or fail with a descriptive error message:

.. testcode:: register_meta

   try:
     class AbstractTypeSerializer(TypeSerializer, register_meta=True):
       pass
   except Exception as err:
     assert str(err) == "Cannot register abstract class <class 'AbstractTypeSerializer'>."
