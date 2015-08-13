#!/usr/bin/python
# -*- coding: utf-8 -*-
import os.path

from osgeo import ogr, osr
import os
import sys

ogr.UseExceptions()

TILEINDEX = "/home/stefan/Projekte/brw_lidar/tileindex/tileindex.gpkg"
LAYERNAME = "tileindex"
TEMPDIR = "/tmp/"
BUFFER = 2

gpkg = ogr.Open(TILEINDEX)
lyr = gpkg.GetLayerByName(LAYERNAME)

for feat in lyr:
    filename = feat.GetField("location")
    print "*** " + os.path.basename(filename) + " ***"

    env = feat.GetGeometryRef().GetEnvelope()
    print env
    min_x = int(env[0] + 0.001) # ? not needed anymore?
    min_y = int(env[2] + 0.001)
    max_x = int(env[1] + 0.001)
    max_y = int(env[3] + 0.001)

    polygon = feat.GetGeometryRef().Buffer(2,5).ExportToWkt()


    #bounds = '"('+str(min_x-BUFFER)+','+str(max_x+BUFFER)+','+str(min_y-BUFFER)+','+str(max_y+BUFFER)+')"'
    bounds = '"(['+str(min_x-BUFFER)+','+str(min_x+BUFFER)+'],['+str(min_y-BUFFER)+','+str(min_y+BUFFER)+'],[0,2000])"'
    print bounds
#POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))
#    polygon = "POLYGON ((594998 595002))"
    cmd = 'pdal tindex --merge ' + TILEINDEX + ' --lyr_name tileindex --bounds ' + bounds + ' --a_srs EPSG:21781 /home/stefan/tmp.las'
    #cmd = 'pdal tindex --merge ' + TILEINDEX + ' --lyr_name tileindex --polygon "' + polygon + '" --a_srs EPSG:21781 /home/stefan/tmp.las'
    print cmd

    break
