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
TEMPDIR = "/tmp/"

#TILEINDEX = "/home/stefan/tmp/lidar/srs/tileindex.gpkg"
#OUTDIR = "/home/stefan/tmp/"

TILEINDEX = "/home/stefan/tmp/lidar/tileindex.gpkg"
OUTDIR = "/home/stefan/tmp/"

#TILEINDEX = "/home/stefan/Projekte/brw_lidar/tileindex/tileindex.gpkg"
#OUTDIR = "/home/stefan/mr_candie_nas/Geodaten/ch/so/agi/hoehen/2014/lidar_lv95/"

BUFFER = 2
SCALE = 0.01

gpkg = ogr.Open(TILEINDEX)
lyr = gpkg.GetLayerByName(LAYERNAME)

start = timeit.default_timer()

for feat in lyr:
    cmd = "rm " + os.path.join(TEMPDIR, "*.las")
    os.system(cmd)

    cmd = "rm " + os.path.join(TEMPDIR, "*.laz")
    os.system(cmd)

    filename = feat.GetField("location")
    print "*** " + os.path.basename(filename) + " ***"

    env = feat.GetGeometryRef().GetEnvelope()
    min_x = int(env[0] + 0.001) # ? not needed anymore?
    min_y = int(env[2] + 0.001)
    max_x = int(env[1] + 0.001)
    max_y = int(env[3] + 0.001)

    # Create new file name.
    filename_lv95 = "LAS_" + str(min_x/1000 + 2000) + "_" + str(min_y/1000 + 1000) + ".laz"
    filename_lv95 = os.path.join(OUTDIR, filename_lv95)
    print filename_lv95

    if (False):
    #if (os.path.isfile(filename_lv95)):
        continue
    else:

        #polygon = feat.GetGeometryRef().Buffer(2,1).ExportToWkt()
        #print polygon

        # Get a slightly larger tile. Two meters buffer is enough. We crop afterwards.
        # Reason: 620'000 -> 2'620'000.65

        if str(os.path.basename(filename)) != str("LAS_594228.laz"):
            continue

        #polygon = "POLYGON (("+str(min_x-BUFFER)+" "+str(min_y-BUFFER)+","+str(min_x-BUFFER)+" "+str(max_y+BUFFER)+","+str(max_x+BUFFER)+" "+str(max_y+BUFFER)+","+str(max_x+BUFFER)+" "+str(min_y-BUFFER)+","+str(min_x-BUFFER)+" "+str(min_y-BUFFER)+"))"
        #cmd = 'pdal tindex --merge ' + TILEINDEX + ' --lyr_name tileindex --polygon "' + str(polygon) + '" --t_srs EPSG:21781 ' + os.path.join(TEMPDIR, 'tmp.las')
        bounds = "(["+str(min_x-BUFFER)+", "+str(max_x+BUFFER)+"], ["+str(min_y-BUFFER)+", "+str(max_y+BUFFER)+"])"
        cmd = 'pdal tindex --merge ' + TILEINDEX + ' --lyr_name tileindex --bounds "' + str(bounds) + '" --t_srs EPSG:21781 ' + os.path.join(TEMPDIR, 'tmp.las')
        #cmd = 'pdal tindex --merge ' + TILEINDEX + ' --lyr_name tileindex --polygon "' + str(polygon) + '" --a_srs EPSG:21781 --t_srs EPSG:21781 ' + os.path.join(TEMPDIR, 'tmp.las')
        #cmd = 'pdal tindex --merge ' + TILEINDEX + ' --lyr_name tileindex --polygon "' + str(polygon) + '" --a_srs "'+S_SRS+'" --t_srs "'+T_SRS+'" ' + os.path.join(TEMPDIR, 'tmp.las')
        print cmd
        os.system(cmd)

        stop = timeit.default_timer()
        print stop - start

        # Now change reference frame with ntv2.
        cmd = 'pdal translate --a_srs "'+S_SRS+'" --t_srs "'+T_SRS+'" -i ' + os.path.join(TEMPDIR, 'tmp.las') + ' -o ' + os.path.join(TEMPDIR, 'tmp_lv95.las')
        print cmd
        os.system(cmd)

        stop = timeit.default_timer()
        print stop - start

        # Set better/nicer EPSG:2056. The ntv2 transformation lacks of datum name.
        # Crop to nice bbbox.
        #polygon = "POLYGON (("+str(min_x+2000000-SCALE)+" "+str(min_y+1000000-SCALE)+","+str(min_x+2000000-SCALE)+" "+str(max_y+1000000)+","+str(max_x+2000000)+" "+str(max_y+1000000)+","+str(max_x+2000000)+" "+str(min_y+1000000-SCALE)+","+str(min_x+2000000-SCALE)+" "+str(min_y+1000000-SCALE)+"))"
        #cmd = 'pdal translate --a_srs EPSG:2056 --t_srs EPSG:2056 --writers.las.format="1" --polygon "' + polygon + '" -z -i ' + os.path.join(TEMPDIR, 'tmp_lv95.las') + ' -o ' + os.path.join(OUTDIR, filename_lv95)

        bounds = "(["+str(min_x+2000000)+", "+str(max_x+2000000)+"], ["+str(min_y+1000000)+", "+str(max_y+1000000)+"])"
        cmd = 'pdal translate --a_srs EPSG:2056 --t_srs EPSG:2056 --writers.las.format="1" --bounds "' + bounds + '" -z -i ' + os.path.join(TEMPDIR, 'tmp_lv95.las') + ' -o ' + os.path.join(OUTDIR, filename_lv95)
        print cmd
        os.system(cmd)

        stop = timeit.default_timer()
        print stop - start
        break
