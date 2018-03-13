# GIS QED MANUAL
*Last updated 03/13/2018*

gis_qed is a Docker container for handling GIS/GDAL focused processes. The container API endpoints are implemented using Flask and Flask_Resful. 

### Processing Stack
Entrypoint is implemented with Flask, a lightweight api framework.
Flask_Restful is added for the additional functionality provided by the package.
Specific python applications are added to the modules directory.


### Adding new endpoints
##### flask_gdal.py
Each endpoint is listed in [root-directory]/flask_gdal.py
The module, 'controller', is imported into flask_gdal.py where a new endpoint is added to the list of existing endpoints. Add the following to create a new endpoint:
```code
api.add_resource(IMPORTED_MODULE.CLASS, '/new/endpoint/url')
```
##### New module
Inside your new module class, have the following imports
```code
from flask import Response
from flask_restful import Resource, reqparse
```
To parse the arguments from your request, use reqparse
```code
parser = reqparse.RequestParser()
parser.add_argument('ARGUMENT1')
parser.add_argument('ARGUMENT2')
```
Your class must accept the flask_restful Resource imported earlier
```code
class MyNewClass(Resource):
```
For each HTTP method you wish your new endpoint to accept, add the appropriate function inside the class.
These functions are the equivalent of C# web controllers.
```code
def post(self):
   """ Accept POST requests """
   """ POST request code goes here """

def get(self):
   """ Accept GET requests """
   """ GET request code goes here """
   
def put(self):
   """ Accept PUT requests """
   """ PUT request code goes here """
   
def delete(self):
   """ Accept DELETE requests """
   """ DELETE request code here """
```

### Future Additions
In the near future, celery, redis and mongoDB will be added to the technology stack. These features will slightly alter the setup of these API endpoints. Each API endpoint will require two request endpoints, one for triggering the calculation (which will return a jobID) and another for retrieving the results of the calculation (by providing the jobID). Incorporating these additional packages will provide complete scalability in processing and requests, limit would be determined by the limits set by kubernetes or docker swarm settings.

Process steps of these additions:
1. Request will remain the same (coming into the flask endpoint)
2. Module class may not need to be updated (depends on the structure of the class)
3. Inside the module the function that executes the core calculation will be decorated with the appropriate celery tags.
   a. A tagged function call adds a function request to the redis queue for the celery worker, a separate docker container. This returns a celery job ID, which would be the returned response for the endpoint.
   b. Once an open core is available, the function will be run asynchronously from the request in the celery container.
   c. The current status of this celery process is available in the redis database.
   d. Results of the function will be stored in a mongoDB.
4. The second endpoint is used to retrieve the data in the database for the specified jobID, or returns the current status of the celery task if the data is not yet available.

Examples of this process will be coming soon.

### Packages
Installed GIS python packages
  - fiona
  - geopandas
  - pyproj
  - pyshp
  - shapely
  
Installed numerical python packages:
  - numpy
  - pandas
  - scipy
  
Database python packages:
  - pymongo
  - redis
  
Additional python packages:
  - google-api-python-client
  - earthengine-api
  - celery

