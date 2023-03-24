Serializer example

Start looking at [requests-example.http](https://github.com/jiadar/serializer-example/blob/main/requests-example.http) for a view of how the data is structured. More detail in the [models](https://github.com/jiadar/serializer-example/blob/main/server/propertymanager/models.py) file which is pretty standard.

The API schema is defined separate from the model in the [views](https://github.com/jiadar/serializer-example/blob/main/server/propertymanager/views.py) file. This uses [marshmallow schemas](https://marshmallow.readthedocs.io/en/stable/). Pay attention to the nesting.

In those views, if you don't want the default behavior from [MarshmallowViewset](https://github.com/jiadar/serializer-example/blob/main/server/marshmallow_viewset.py) you can override the DRF methods. Otherwise, it will let you add objects with arbitrary nesting from a root object. 

Most of the magic is in the [tree Node](https://github.com/jiadar/serializer-example/blob/main/server/node.py), which maps between the django ORM objects, marshmallow schemas, and recursively handles nesting.
