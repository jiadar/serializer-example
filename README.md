# Serializer example

## Running the project
You can run the postgres docker container from the docker-compose.yml, just run docker-compose up from the root. Be sure you don't have other postgres running. 

This project uses poetry. To install, run `poetry install` in the server directory. Then run `poetry shell` then `python manage.py migrate` then `python manage.py runserver`

When debugging, a [handy script](https://github.com/jiadar/serializer-example/blob/main/server/propertymanager/management/commands/resetdb.py) will delete data from your database tables so you can continue to insert the same data (poor man's fixtures). You will have to update the path as it's hardcoded. `python manage.py resetdb`

You will need to add a user with id `1f8be170-f711-64d4-a807-6a7d91c80bc9` for the big query to work. Do this with psql or make a post request.

## Interesting Details
Start looking at [requests-example.http](https://github.com/jiadar/serializer-example/blob/main/requests-example.http) for a view of how the data is structured. This has four levels of nesting but infinite nesting is supported. More detail in the [models](https://github.com/jiadar/serializer-example/blob/main/server/propertymanager/models.py) file which is pretty standard.

The API schema is defined separate from the model in the [views](https://github.com/jiadar/serializer-example/blob/main/server/propertymanager/views.py) file. This uses [marshmallow schemas](https://marshmallow.readthedocs.io/en/stable/). Pay attention to the nesting.

In those views, if you don't want the default behavior from the custom [MarshmallowViewset](https://github.com/jiadar/serializer-example/blob/main/server/marshmallow_viewset.py) you can override the DRF methods. Otherwise, it will let you add objects with arbitrary nesting from a root object. 

Most of the magic is in the  [Node]s(https://github.com/jiadar/serializer-example/blob/main/server/node.py) that make up the nested tree of object relations. This maps between the django ORM objects, marshmallow schemas, and recursively handles nesting.


