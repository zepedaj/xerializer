TODO List
=========

.. todo::
   
   * Add a hydra-like or command-line argument processing extension.
     * Should support creation of meta variables that are not passed to the program: {@meta: {input_dimension: 100}}
     * Should have an @import command to import configs from other files or variables: {train: {db:{@from:db/, @default:mysql}
     * Should support substition using e.g, {{var.x}}
     * Nested variables can be specified using filesystem directories or links within the same file. E.g., train.data@from(data,@global): imagenet should assign to the train.data structure the data.imagenet structure.
   * Add the hydra cli module from jzf_train to xerializer       
   * xerializer.abstract_type_serializer -> Rename to xerializer.abstract_types
   * Add the concept of namespaces to manages third-party plugin groups. Make it possible for these to support extending existing namespaces by just having their string name in the list of plugins.
   * Make it possible to call functions and other callables using the same syntax.   
   * Support tuple-of-string signatures that register the class as from_serializable for various signatures.
   * Deploy to github


Possible syntaxes:

.. code-block:: yaml
   
   {@meta: {input_dimension: 100, randomization: True}}

   {train: {db:{@from:db/, @default:mysql}

   db/ to define a path, db to define a variable in the file. Or db for both, and give precedence to local vars and then file system.
