#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import os.path
import sys
import timeit
import json

from osgeo import ogr, osr
from pprint import pprint

ogr.UseExceptions()

LAYERNAME = "tileindex"
TEMP_DIR = "/tmp/"

TILEINDEX = "/home/stefan/tmp/lidar_verifikation/lv03/tileindex.gpkg"
LV03_DIR = "/home/stefan/tmp/lidar_verifikation/lv03/"
LV95_DIR = "/home/stefan/tmp/lidar_verifikation/lv95/"
OUT_DIR = "/home/stefan/tmp/"

BUFFER = 2

def lv03_to_lv95(point):
    S_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=600000 +y_0=200000 +towgs84=674.374,15.056,405.346 +units=m +units=m +k_0=1 +nadgrids=./chenyx06/chenyx06a.gsb"
    T_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=2600000 +y_0=1200000 +towgs84=674.374,15.056,405.346 +units=m +k_0=1 +nadgrids=@null"

    source = osr.SpatialReference()
    source.ImportFromProj4(S_SRS)

    target = osr.SpatialReference()
    target.ImportFromProj4(T_SRS)

    transform = osr.CoordinateTransformation(source, target)

    point_n = ogr.Geometry(ogr.wkbPolygon)
    point_n = point.Clone()

    point_n.Transform(transform)
    return point_n

def json_to_map(filename):
    json_data = open(filename).read()

    # return only
    data = json.loads(json_data)['unnamed'] # root element/key is named 'unnamed'
    return data

def main():
    gpkg = ogr.Open(TILEINDEX)
    lyr = gpkg.GetLayerByName(LAYERNAME)

    start = timeit.default_timer()

    for feat in lyr:
        cmd = "rm " + os.path.join(TEMP_DIR, "*.las")
        os.system(cmd)

        cmd = "rm " + os.path.join(TEMP_DIR, "*.laz")
        os.system(cmd)

        filename = feat.GetField("location")
        print "*** " + os.path.basename(filename) + " ***"

        env = feat.GetGeometryRef().GetEnvelope()
        min_x = int(env[0] + 0.001)
        min_y = int(env[2] + 0.001)
        max_x = int(env[1] + 0.001)
        max_y = int(env[3] + 0.001)

        # Create our own filenames for LV03 and LV95 las files.
        # We want to be more flexible since the filename
        # in the tileindex is an absolute path (which seems
        # be a bug).
        filename_lv03 = os.path.join(LV03_DIR, os.path.basename(filename))

        filename_lv95 = "LAS_" + str(min_x/1000 + 2000) + "_" + str(min_y/1000 + 1000) + ".laz"
        filename_lv95 = os.path.join(LV95_DIR, filename_lv95)

        # Create the point geometry in EPSG:21781
        x = (max_x - min_x) / 2 + min_x
        y = (max_y - min_y) / 2 + min_y

        point_lv03 = ogr.Geometry(ogr.wkbPoint)
        point_lv03.AddPoint(x, y)

        # We need the very same point in EPSG:2056.
        # We have to use the same transformation method as we used
        # for transforming the lidar stuff.
        point_lv95 = lv03_to_lv95(point_lv03)
        print point_lv95

        # Dump 10 nearest lidar points in LV03.
        info_file_lv03 = os.path.join(TEMP_DIR, "info_lv03.json")
        query = str(point_lv03.GetX()) + "," + str(point_lv03.GetY()) + "/10"
        cmd = 'pdal info --query ' + query + ' ' + filename_lv03 + ' > ' + info_file_lv03
        print cmd
        #os.system(cmd)

        # Dump 10 nearest lidar points in LV95.
        info_file_lv95 = os.path.join(TEMP_DIR, "info_lv95.json")
        query = str(point_lv95.GetX()) + "," + str(point_lv95.GetY()) + "/10"
        cmd = 'pdal info --query ' + query + ' ' + filename_lv95 + ' > ' + info_file_lv95
        print cmd
        #os.system(cmd)

        # Read the json dumps and put the result in dicts.
        map_lv03 = json_to_map(info_file_lv03)
        map_lv95 = json_to_map(info_file_lv95)

        print map_lv95

        # Loop through dicts and compare the points.
        # for-for... not very smart.
        for i in map_lv03:
            gpstime_lv03 = map_lv03[i]['GpsTime']
            intensity_lv03 = map_lv03[i]['Intensity']
            classification_lv03 = map_lv03[i]['Classification']

            x_lv03 = map_lv03[i]['X']
            y_lv03 = map_lv03[i]['Y']
            z_lv03 = map_lv03[i]['Z']
            print gpstime_lv03

            for j in map_lv95:
                gpstime_lv95 = map_lv95[j]['GpsTime']
                intensity_lv95 = map_lv95[j]['Intensity']
                classification_lv95 = map_lv95[j]['Classification']

                x_lv95 = map_lv95[i]['X']
                y_lv95 = map_lv95[i]['Y']
                z_lv95 = map_lv95[i]['Z']

                # Try to identify the same point in LV03 and LV95.
                # Since there is no real unique identifier (?) we use different
                # attributes (and even the heigth).
                # If we found the same point (actually it should be one point only!)
                # we can transform LV03 to LV95 and compare the coordinates.
                if gpstime_lv03 == gpstime_lv95 and intensity_lv03 == intensity_lv95 and classification_lv03 == classification_lv95 and z_lv03 == z_lv95:
point_lv03 = ogr.Geometry(ogr.wkbPoint)
point_lv03.AddPoint(x, y)

# We need the very same point in EPSG:2056.
# We have to use the same transformation method as we used
# for transforming the lidar stuff.
point_lv95 = lv03_to_lv95(point_lv03)
print point_lv95






        break

    print "Hallo Stefan."

if __name__ == '__main__':
    sys.exit(main())
