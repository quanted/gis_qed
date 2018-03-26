from flask import Flask, Response
# from flask_cors import CORS
from flask_restful import Api, Resource
import os

# Import modules
from modules.hms import ncdc_stations
from modules.hms import percent_area

app = Flask(__name__)
# CORS(app)
app.config.update(
    DEBUG=True
)

api = Api(app)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
os.environ.update({
    'PROJECT_ROOT': PROJECT_ROOT
})


class StatusTest(Resource):
    def get(self):
        return {"status": "GIS_QED up and running."}


print('GIS QED at http://localhost:7888 started')
api.add_resource(StatusTest, '/gis/rest/test/')

# HMS endpoints
# TODO: add endpoint for get after converting post endpoint to celery function
api.add_resource(ncdc_stations.HMSNcdcStations, '/gis/rest/hms/ncdc/stations/')
api.add_resource(percent_area.getPercentArea, '/gis/rest/hms/percentage/')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
