#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import os.path
import sys
import timeit
import json
import struct
import requests
from subprocess import Popen,PIPE,STDOUT,call

from osgeo import ogr, osr
from osgeo import gdal

ogr.UseExceptions()

S_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=600000 +y_0=200000 +towgs84=674.374,15.056,405.346 +units=m +units=m +k_0=1 +nadgrids=./chenyx06/chenyx06a.gsb"
T_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=2600000 +y_0=1200000 +towgs84=674.374,15.056,405.346 +units=m +k_0=1 +nadgrids=@null"

NTV2 = "./chenyx06/ntv2_diff.tif"

SWISSTOPO_URL = "http://geodesy.geo.admin.ch/reframe/lv03tolv95?format=json"

LAYERNAME = "tileindex"
TEMP_DIR = "/tmp/"

#TILEINDEX = "/home/stefan/tmp/lidar_verifikation/lv03/tileindex.gpkg"
#LV03_DIR = "/home/stefan/tmp/lidar_verifikation/lv03/"
#LV95_DIR = "/home/stefan/tmp/lidar_verifikation/lv95/"
TILEINDEX = "/home/stefan/Projekte/brw_lidar/tileindex/tileindex.gpkg"
LV03_DIR = "/home/stefan/mr_candie_nas/Geodaten/ch/so/agi/hoehen/2014/lidar/"
LV95_DIR = "/home/stefan/mr_candie_nas/Geodaten/ch/so/agi/hoehen/2014/lidar_lv95/"

def lv03_to_lv95(point):
    source = osr.SpatialReference()
    source.ImportFromProj4(S_SRS)

    target = osr.SpatialReference()
    target.ImportFromProj4(T_SRS)

    transform = osr.CoordinateTransformation(source, target)

    point_n = ogr.Geometry(ogr.wkbPolygon)
    point_n = point.Clone()

    point_n.Transform(transform)
    return point_n

def get_ntv2_accuracy(point):
    ds = gdal.Open(NTV2)
    gt = ds.GetGeoTransform()
    rb = ds.GetRasterBand(1)

    mx = point.GetX()
    my = point.GetY()


    px = int((mx - gt[0]) / gt[1]) #x pixel
    py = int((my - gt[3]) / gt[5]) #y pixel

    if px < 0 or py < 0:
        return
    else:
        structval = rb.ReadRaster(px, py, 1, 1, buf_type = gdal.GDT_Float32)
        # Is this THE way to handle out of range errors correctly?
        # It still throws an error on console...
        if structval:
            tuple_of_floats = struct.unpack('f', structval)
            fs_mm = float(tuple_of_floats[0])
            # This is a bit heuristic since it depends on how you set no-data value.
            if fs_mm <= 0:
                return
            return fs_mm / 10
        else:
            return

def main():
    gpkg = ogr.Open(TILEINDEX)
    lyr = gpkg.GetLayerByName(LAYERNAME)

    start = timeit.default_timer()

    for feat in lyr:
        cmd = "rm " + os.path.join(TEMP_DIR, "*.las")
        #os.system(cmd)

        filename = feat.GetField("location")
        #print "*** " + os.path.basename(filename) + " ***"

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

        # Create a point geometry in EPSG:21781 in the middle of the LV03 tile.
        x = (max_x - min_x) / 2 + min_x
        y = (max_y - min_y) / 2 + min_y

        point_lv03 = ogr.Geometry(ogr.wkbPoint)
        point_lv03.AddPoint(x, y)

        # We need the very same point in EPSG:2056.
        # We have to use the same transformation method as we used
        # for transforming the lidar stuff.
        point_lv95 = lv03_to_lv95(point_lv03)

        # Dump 10 nearest lidar points in LV03.
        info_file_lv03 = os.path.join(TEMP_DIR, "info_lv03.json")
        query = str(point_lv03.GetX()) + "," + str(point_lv03.GetY()) + "/10"
        cmd = 'pdal info --query ' + query + ' ' + filename_lv03
        proc = Popen(cmd, shell=True, stdout=PIPE)
        output = proc.communicate()[0]
        map_lv03 = json.loads(output)['unnamed']

        # Dump 10 nearest lidar points in LV95.
        info_file_lv95 = os.path.join(TEMP_DIR, "info_lv95.json")
        query = str(point_lv95.GetX()) + "," + str(point_lv95.GetY()) + "/10"
        cmd = 'pdal info --query ' + query + ' ' + filename_lv95
        proc = Popen(cmd, shell=True, stdout=PIPE)
        output = proc.communicate()[0]
        map_lv95 = json.loads(output)['unnamed']

        # Loop through dicts and compare the points.
        # for-for... not very smart.
        k = 0
        for i in map_lv03:
            gpstime_lv03 = map_lv03[i]['GpsTime']
            intensity_lv03 = map_lv03[i]['Intensity']
            classification_lv03 = map_lv03[i]['Classification']

            x_lv03 = float(map_lv03[i]['X'])
            y_lv03 = float(map_lv03[i]['Y'])
            z_lv03 = map_lv03[i]['Z']

            for j in map_lv95:
                gpstime_lv95 = map_lv95[j]['GpsTime']
                intensity_lv95 = map_lv95[j]['Intensity']
                classification_lv95 = map_lv95[j]['Classification']

                x_lv95 = float(map_lv95[i]['X'])
                y_lv95 = float(map_lv95[i]['Y'])
                z_lv95 = map_lv95[i]['Z']

                # Try to identify the same point in LV03 and LV95.
                # Since there is no real unique identifier (?) we use different
                # attributes (and even the heigth).
                # If we found the same point (actually it should be one point only!)
                # we can transform LV03 to LV95 and compare the coordinates.
                if gpstime_lv03 == gpstime_lv95 and intensity_lv03 == intensity_lv95 and classification_lv03 == classification_lv95 and z_lv03 == z_lv95:
                    point_lv03 = ogr.Geometry(ogr.wkbPoint)
                    point_lv03.AddPoint(x_lv03, y_lv03)

                    point_lv95_trans = lv03_to_lv95(point_lv03)
                    x_lv95_trans = point_lv95_trans.GetX()
                    y_lv95_trans = point_lv95_trans.GetY()

                    # The coordinates from the LV95 las file uses a 0.01 scale (=cm).
                    # The transformed coordinates from LV03 are floats.
                    # We round the floats to the same decimal scale.
                    # And the diffs should be zero (since it is the same transformation algorithm).
                    dx_cm = (x_lv95 - round(x_lv95_trans, 2)) * 100
                    dy_cm = (y_lv95 - round(y_lv95_trans, 2)) * 100

                    # We can double check the transformation with the swisstopo rest transformation service.
                    # It uses the 'real' transformation method with triangles. Hence we will get some differences.
                    # How to check if this is still ok?
                    # Get the accuracy of the ntv2 transformation from a 100m x 100m raster file which we used
                    # for the accuracy map.

                    # fs_cm is None if the point is outside the ntv2 accuracy map (or in a no_data area).
                    fs_cm = get_ntv2_accuracy(point_lv95)
                    if not fs_cm:
                        fs_cm = -9999

                    # Make the LV03 -> LV95 request.
                    url = SWISSTOPO_URL + "&easting="+str(x_lv03)+"&northing="+str(y_lv03)
                    response = requests.get(url)
                    data = response.json()
                    x_lv95_swisstopo = float(data['easting'])
                    y_lv95_swisstopo = float(data['northing'])

                    # Calculate the difference between swisstopo LV95 and lidar LV95_trans.
                    # We use the lidar LV95 transformed coordinate to compare it with the
                    # ntv2 accuracy.
                    dx_cm_swisstopo = (x_lv95_trans - x_lv95_swisstopo) * 100
                    dy_cm_swisstopo = (y_lv95_trans - y_lv95_swisstopo) * 100

                    # Print all the results to STDOUT
                    print "%s, %s, %s, %s, %s, %f, %f, %f, %f, %f, %f, %.1f, %.1f, %.1f, %.1f, %.1f" % (os.path.basename(filename), gpstime_lv03, intensity_lv03, classification_lv03, z_lv03, x_lv95, y_lv95, x_lv95_trans, y_lv95_trans, x_lv95_swisstopo, y_lv95_swisstopo, dx_cm, dy_cm, dx_cm_swisstopo, dy_cm_swisstopo, fs_cm)
                    k += 1

        # If k <> 10 we either have some false identification (> 10) or we did not found some points.
        if k <> 10:
            print "WARNING: Identified %u points. Should be 10." % (k)

        stop = timeit.default_timer()
        print stop - start
            
if __name__ == '__main__':
    sys.exit(main())
