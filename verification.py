#!/usr/bin/python
# -*- coding: utf-8 -*-
import os.path
import timeit

from osgeo import ogr, osr
import os
import sys

ogr.UseExceptions()

S_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=600000 +y_0=200000 +towgs84=674.374,15.056,405.346 +units=m +units=m +k_0=1 +nadgrids=./chenyx06/chenyx06a.gsb"
T_SRS = "+proj=somerc +lat_0=46.952405555555555N +lon_0=7.439583333333333E +ellps=bessel +x_0=2600000 +y_0=1200000 +towgs84=674.374,15.056,405.346 +units=m +k_0=1 +nadgrids=@null"

LAYERNAME = "tileindex"
TEMP_DIR = "/tmp/"

TILEINDEX = "/home/stefan/tmp/lidar_verifikation/lv03/tileindex.gpkg"
LV03_DIR = "/home/stefan/tmp/lidar_verifikation/lv03/"
LV95_DIR = "/home/stefan/tmp/lidar_verifikation/lv95/"
OUT_DIR = "/home/stefan/tmp/"

BUFFER = 2

#TILEINDEX = "/home/stefan/tmp/lidar/srs/tileindex.gpkg"
#OUTDIR = "/home/stefan/tmp/"

#TILEINDEX = "/home/stefan/Projekte/brw_lidar/tileindex/tileindex.gpkg"
#OUTDIR = "/home/stefan/mr_candie_nas/Geodaten/ch/so/agi/hoehen/2014/lidar_lv95/"

gpkg = ogr.Open(TILEINDEX)
lyr = gpkg.GetLayerByName(LAYERNAME)

start = timeit.default_timer()

for feat in lyr:
    #cmd = "rm " + os.path.join(TEMPDIR, "*.las")
    #os.system(cmd)

    #cmd = "rm " + os.path.join(TEMPDIR, "*.laz")
    #os.system(cmd)

    filename = feat.GetField("location")
    print "*** " + os.path.basename(filename) + " ***"

    env = feat.GetGeometryRef().GetEnvelope()
    min_x = int(env[0] + 0.001)
    min_y = int(env[2] + 0.001)
    max_x = int(env[1] + 0.001)
    max_y = int(env[3] + 0.001)

    # Create the clip geometry in EPSG:21781
    x = (max_x - min_x) / 2 + min_x
    y = (max_y - min_y) / 2 + min_y

    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(x, y)

    clip_lv03 = point.Buffer(BUFFER,1)

    # We need the very same area in EPSG:2056.
    # We have to use the same transformation method as we used
    # for transforming the lidar stuff.
    source = osr.SpatialReference()
    source.ImportFromProj4(S_SRS)

    target = osr.SpatialReference()
    target.ImportFromProj4(T_SRS)

    transform = osr.CoordinateTransformation(source, target)

    clip_lv95 = ogr.Geometry(ogr.wkbPolygon)
    clip_lv95 = clip_lv03.Clone()

    clip_lv95.Transform(transform)
    print clip_lv03
    print clip_lv95

    # Now we clip the las file in both reference frames
    # and afterwards we convert the clipped las to a geopackage.

    # Multipoint -> difference. Minimal Buffern, dh. 1-5mm oder so.



    break

    # Create new file name.
    filename_lv95 = "LAS_" + str(min_x/1000 + 2000) + "_" + str(min_y/1000 + 1000) + ".laz"
    filename_lv95 = os.path.join(TEMP_DIR, filename_lv95)
    print filename_lv95
