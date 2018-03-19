from flask import Response, Flask, request, jsonify
from flask_restful import Resource, reqparse, abort
from werkzeug.datastructures import FileStorage
from shapely.geometry import Point, shape
import matplotlib.pyplot as plt
from fiona.crs import from_epsg
from osgeo import ogr, osr
import geopandas as geo
import urllib.request
from zipfile import *
import pandas as pd
import requests
import shutil
import json
import time
import uuid
import sys
import os

parser = reqparse.RequestParser()
parser.add_argument('huc_8_num')
parser.add_argument('huc_12_num')
parser.add_argument('com_id_num')
parser.add_argument('filename', location='files', type=FileStorage)

class getPercentArea(Resource):
	'''
	User sends Catchment ID (CommID) and HUC8 number to get % area of each NLDAS/GLDAS cell covered by the catchment
	Sample usage:
	http://127.0.0.1:5000/gis/rest/hms/percentage/?huc_8_num=01060002&com_id_num=9311911
	http://127.0.0.1:5000/gis/rest/hms/percentage/?huc_8_num=01060002
	http://127.0.0.1:5000/gis/rest/hms/percentage/?huc_12_num=020100050107
	'''
	def get(self):
		args = parser.parse_args()
		huc_8_num = args.huc_8_num
		huc_12_num = args.huc_12_num
		com_id_num = args.com_id_num
		if(huc_8_num and com_id_num):
			tab = calculations(huc_8_num, None, com_id_num, None)
		elif(huc_12_num):
			tab = calculations(None, huc_12_num[0:8], None, None)	#Huc12s are catalogued on ftp server by huc8 numbers
		elif(huc_8_num):
			tab = calculations(huc_8_num, None, None, None)
		return jsonify(tab)

	'''
	User uploads catchment or NHDPlus shapefile
	Sample usage:
	curl -X POST -F 'filename=@file.geojson' http://127.0.0.1:5000/gis/rest/hms/percentage/
	'''
	def post(self):
		args = parser.parse_args()
		if(args.filename is not None):		#Using curl
			tab = calculations(None, None, None, args.filename.read())
		else:
			return Response("{'posting error': 'POST operation failed'}")
		return jsonify(tab)


def calculations(huc8, huc12, com, in_file):
	start = time.time()
	table = []
	colNames = []
	GUID = str(uuid.uuid4())
	if(in_file):
		sfile = in_file
	elif(huc8):
		url = 'ftp://newftp.epa.gov/exposure/BasinsData/NHDPlus21/NHDPlus' + str(huc8) + '.zip'
		shapefile = urllib.request.urlretrieve(url, GUID + 'shape.zip')
		with ZipFile(GUID + 'shape.zip') as myzip:
			myzip.extractall(GUID)
		sfile = GUID + '/NHDPlus' + str(huc8) + '/Drainage/Catchment.shp'
	elif(huc12):
		url = 'ftp://newftp.epa.gov/exposure/NHDV1/HUC12_Boundries/' + str(huc12) + '.zip'
		shapefile = urllib.request.urlretrieve(url, GUID + 'shape.zip')
		with ZipFile(GUID + 'shape.zip') as myzip:
			myzip.extractall(GUID)
		sfile = GUID + '/' + str(huc12) + '/huc12.shp'
	nldasurl = 'https://ldas.gsfc.nasa.gov/nldas/gis/NLDAS_Grid_Reference.zip'
	gridfile = urllib.request.urlretrieve(nldasurl, GUID + 'grid.zip')
	with ZipFile(GUID + 'grid.zip') as myzip:
		myzip.extractall(GUID + 'NLDAS')
	gfile = GUID + 'NLDAS/NLDAS_Grid_Reference.shp'
	print("FINISHED UNZIPPING: ", time.time() - start)
	shape = ogr.Open(sfile)
	nldas = ogr.Open(gfile)
	shapeLayer = shape.GetLayer()
	nldasLayer = nldas.GetLayer()
	# Getting data for reprojection
	shapeProj = shapeLayer.GetSpatialRef()
	nldasProj = nldasLayer.GetSpatialRef()
	coordTrans = osr.CoordinateTransformation(shapeProj, nldasProj)
	# Getting features from shapefile
	colLayer = shape.GetLayer(0).GetLayerDefn()
	for i in range(colLayer.GetFieldCount()):
		colNames.append(colLayer.GetFieldDefn(i).GetName())
	coms, huc8s, huc12s = [], [], []
	overlap, polygons = [], []
	if ('COMID' in colNames):
		huc12s = [None] * len(shapeLayer)  # No huc 12s
		for feature in shapeLayer:
			if(com):
				if (feature.GetField('COMID') == int(com)):  # Only focusing on the given catchment argument
					polygons.append(feature)
					coms.append(feature.GetField('COMID'))
					huc8s.append(feature.GetField('HUC8'))
					#break #Since only one catchment is needed
			else:
				polygons.append(feature)
				coms.append(feature.GetField('COMID'))
				huc8s.append(feature.GetField('HUC8'))
	elif ('HUC_8' in colNames):
		coms = [None] * len(shapeLayer)  # No catchments
		for feature in shapeLayer:
			polygons.append(feature)
			huc8s.append(feature.GetField('HUC_8'))
			huc12s.append(feature.GetField('HUC_12'))
	# Reproject geometries from shapefile
	totalPoly = ogr.Geometry(ogr.wkbMultiPolygon)
	#Treat all polygons as one larger one since we are just finding overlapping cells
	for polygon in polygons:
		poly = polygon.GetGeometryRef()
		poly.Transform(coordTrans)
		totalPoly.AddGeometry(poly)
	totalPoly = totalPoly.UnionCascaded()
	# Calculate cells that contain polygons ahead of time to make intersections faster
	# This block of code should be parallelized if possible
	for feature in nldasLayer:
		cell = feature.GetGeometryRef()
		if (totalPoly.Intersects(cell) and feature not in overlap):
			overlap.append(feature)
	# Iterate through smaller list of overlapping cells to calculate data
	huc8table = [{"HUC 8 ID": huc8s[0]}]
	i = 0;
	for polygon in polygons:
		poly = polygon.GetGeometryRef()
		huc12table = []
		huc12table.append({"HUC 12 ID": huc12s[i]})
		huc12table.append({"Catchment ID": coms[i]})
		for feature in overlap:
			cell = feature.GetGeometryRef()
			interArea = 0
			squareArea = cell.Area()
			if (poly.Intersects(cell)):
				inter = poly.Intersection(cell)
				interArea += inter.Area()
				percentArea = (interArea / squareArea) * 100
				catchtable = {"latitude": cell.Centroid().GetX(),
							  "longitude": cell.Centroid().GetY(),
							  "cellArea": squareArea,
							  "containedArea": interArea,
							  "percentArea": percentArea}
				huc12table.append(catchtable)
		huc8table.append(huc12table)
		i += 1
	table.append(huc8table)
	# Delete zipfiles and extracted shapefiles
	shape = None
	nldas = None
	if(in_file):
		os.remove(GUID + 'grid.zip')
		shutil.rmtree(GUID + 'NLDAS')
	else:
		os.remove(GUID + 'grid.zip')
		os.remove(GUID + 'shape.zip')
		shutil.rmtree(GUID + 'NLDAS')
		shutil.rmtree(GUID)
	#jsonOut = json.dumps(table)
	# write json to file?
	#print(jsonOut)
	end = time.time()
	print(end - start)
	return table