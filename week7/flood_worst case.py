from numpy import zeros, logical_or
from rasterio import open as rio_open
from rasterio.transform import rowcol
from rasterio.plot import show as rio_show
from matplotlib.pyplot import subplots, savefig
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from geopandas import GeoSeries
from shapely.geometry import Point
from matplotlib_scalebar.scalebar import ScaleBar
from math import floor, ceil

def coord_2_img(transform, x, y):
	""" 
	* Convert from coordinate space to image space using the 
	*   Affine transform object from a rasterio dataset
	"""
	r, c = rowcol(transform, x, y)
	return int(r), int(c)


def flood_fill_single_point(depth, x0, y0, dem_data, transform, dem):
    """
    * Implement flood fill for a single point and depth
    * Returns flood layer for this point (1=flooded, 0=not flooded)
    """
    flood_layer = zeros(dem_data.shape)
    r0, c0 = coord_2_img(transform, x0, y0)
    
    # Skip if origin is out of bounds (optional safety check)
    if not (0 <= r0 < dem.height and 0 <= c0 < dem.width):
        print(f"Warning: Flood origin ({x0}, {y0}) is out of raster bounds")
        return flood_layer
    
    flood_extent = dem_data[r0][c0] + depth
    assessed = set()
    to_assess = set()
    to_assess.add((r0, c0))
    
    while to_assess:
        r, c = to_assess.pop()
        assessed.add((r, c))
        
        if dem_data[r][c] <= flood_extent:
            flood_layer[r][c] = 1
            
            # Check all 8 neighbors (course's elegant version)
            for r_adj, c_adj in [(-1, -1), (-1, 0), (-1, 1),
                                 (0, -1),          (0, 1),
                                 (1, -1),  (1, 0), (1, 1)]:
                neighbour = (r + r_adj, c + c_adj)
                if (0 <= neighbour[0] < dem.height and 
                    0 <= neighbour[1] < dem.width and 
                    neighbour not in assessed):
                    to_assess.add(neighbour)
    
    return flood_layer


def calculate_worst_case_flood(flood_points, dem_data, transform, dem):
    """
    * Calculate worst-case flood zone (union of all single-point floods)
    * Input: flood_points = list of tuples [(x1, y1, depth1), (x2, y2, depth2), ...]
    * Output: Combined flood layer (1=flooded by any point, 0=not flooded)
    """
    # Initialize worst-case layer with all 0s
    worst_case_flood = zeros(dem_data.shape)
    
    # Process each flood point and merge results (union)
    for idx, (x, y, depth) in enumerate(flood_points, 1):
        print(f"Processing flood point {idx}: (x={x}, y={y}, depth={depth}m)")
        single_flood = flood_fill_single_point(depth, x, y, dem_data, transform, dem)
        # Merge using logical OR (retain 1s from any flood layer)
        worst_case_flood = logical_or(worst_case_flood, single_flood).astype(int)
    
    return worst_case_flood


# ----------------------
# Course-compatible settings (multiple points + depths)
# ----------------------
# Define MULTIPLE flood points: list of (x, y, flood_depth) tuples
FLOOD_POINTS = [
    (332000, 514000, 2),    # Original point + 2m depth
    (331500, 513800, 3),    # Additional point + 3m depth
    (332500, 514200, 1.5)   # Third point + 1.5m depth
]


# ----------------------
# Main execution
# ----------------------
with rio_open("E:/Manchester/UGIS/data/helvellyn/Helvellyn-50.tif") as dem:
    dem_data = dem.read(1)
    
    # Calculate worst-case flood (union of all points)
    worst_case_output = calculate_worst_case_flood(FLOOD_POINTS, dem_data, dem.transform, dem)
    
    # Print verification stats
    total_flooded_cells = worst_case_output.sum()
    print(f"\nWorst-case flooded cells: {int(total_flooded_cells)}")
    
    # ----------------------
    # Visualization (retained course original code)
    # ----------------------
    fig, my_ax = subplots(1, 1, figsize=(16, 10))
    my_ax.set_title("Worst-Case Flood Fill Model (Union of Multiple Points)")
    
    # Plot DEM
    rio_show(
        dem_data,
        ax=my_ax,
        transform=dem.transform,
        cmap='cividis'
    )
    
    # Add elevation contours
    rio_show(
        dem_data,
        ax=my_ax,
        transform=dem.transform,
        contour=True,
        colors=['white'],
        linewidths=[0.5]
    )
    
    # Plot worst-case flood zone (transparent blue)
    flood_cmap = LinearSegmentedColormap.from_list(
        'binary', 
        [(0, 0, 0, 0), (0, 0.5, 1, 0.5)], 
        N=2
    )
    rio_show(
        worst_case_output,
        ax=my_ax,
        transform=dem.transform,
        cmap=flood_cmap
    )
    
    # Plot ALL flood origins (red markers)
    origin_points = [Point(x, y) for x, y, _ in FLOOD_POINTS]
    GeoSeries(origin_points).plot(
        ax=my_ax,
        markersize=50,
        color='red',
        edgecolor='white'
    )
    
    # Add colorbar for elevation
    fig.colorbar(
        ScalarMappable(
            norm=Normalize(vmin=floor(dem_data.min()), vmax=ceil(dem_data.max())),
            cmap='cividis'
        ), 
        ax=my_ax, 
        pad=0.01
    )
    
    # Add north arrow
    x, y, arrow_length = 0.97, 0.99, 0.1
    my_ax.annotate(
        'N', 
        xy=(x, y), 
        xytext=(x, y-arrow_length),
        arrowprops=dict(facecolor='black', width=5, headwidth=15),
        ha='center', 
        va='center', 
        fontsize=20, 
        xycoords=my_ax.transAxes
    )
    
    # Add scale bar
    my_ax.add_artist(ScaleBar(dx=1, units="m", location="lower right"))
    
    # Add legend (updated for multiple points)
    my_ax.legend(
        handles=[
            Patch(facecolor=(0, 0.5, 1, 0.5), edgecolor=None, label='Worst-Case Flood Zone'),
            Line2D([0], [0], marker='o', color=(1,1,1,0), label='Flood Origins', markerfacecolor='red', markersize=8)
        ], 
        loc='lower left'
    )
    
    # Save output
    savefig('./out/8.png', bbox_inches='tight')
    print("done!")