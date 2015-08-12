## LAS-Format ##
Es werden die RGB-losen LAS-Dateien transformiert, dh. LAS-Format 1.

## Tileindex erstellen ##
```
find /home/stefan/mr_candie_nas/Geodaten/ch/so/agi/hoehen/2014/lidar/ -maxdepth 1 -iname "*.laz" | pdal tindex tileindex.gpkg -f "GPKG" --a_srs EPSG:21781 --t_srs EPSG:21781 --fast_boundary --stdin --lyr_name tileindex
```
