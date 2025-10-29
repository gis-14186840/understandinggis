from geopandas import read_file
from week5 import evaluate_distortion
from pyproj import Geod, CRS, Transformer

# set the projected CRS to evaluate for distortion
proj_string = "+proj=eck4 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"  # Eckert IV (Equal Area)

# set the geographical proj string and ellipsoid (should be the same)
geo_string = "+proj=longlat +datum=WGS84 +no_defs"
g = Geod(ellps='WGS84')

# load the shapefile of countries and extract country of interest
world = read_file("E:/Manchester/UGIS/data/natural-earth/ne_10m_admin_0_countries.shp")

# set country using country code
country = world.loc[world.ISO_A3 == "ISL"]

# get the bounds of the country
minx, miny, maxx, maxy = country.total_bounds

# initialise a PyProj Transformer to transform coordinates
transformer = Transformer.from_crs(CRS.from_proj4(geo_string), CRS.from_proj4(proj_string), always_xy=True)

# calculate the distortion
Ep, Es, Ea = evaluate_distortion(g, transformer, minx, miny, maxx, maxy, 10000, 1000000, 1000)

# report to user
print(f"{"Distance distortion (Ep):":<26}{Ep:.6f}")
print(f"{"Shape distortion (Es):":<26}{Es:.6f}")
print(f"{"Area distortion (Ea):":<26}{Ea:.6f}")
