# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 13:37:57 2025

@author: Chris
"""

rom geopandas import read_file, GeoSeries

# load the shapefile of countries - this gives a table of 12 columns and 246 rows (one per country)
world = read_file("E:/Manchester/UGIS/data/natural-earth/ne_10m_admin_0_countries.shp")