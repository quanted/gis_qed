from flask import Flask
from flask_cors import CORS
from flask_restful_swagger_2 import Api
import os

# Import modules
from modules.hms import ncdc_stations
from modules.hms import percent_area

app = Flask(__name__)
CORS(app)
app.config.update(
    DEBUG=True
)

api = Api(app, api_version='0.1', api_spec_url='/api/swagger')

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
os.environ.update({
    'PROJECT_ROOT': PROJECT_ROOT
})

print('GIS QED at http://localhost:7888 started')

# HMS endpoints
# TODO: add endpoint for get after converting post endpoint to celery function
api.add_resource(ncdc_stations.HMSNcdcStations, '/gis/rest/hms/ncdc/stations/')
api.add_resource(percent_area.getPercentArea, '/gis/rest/hms/percentage/')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
