import os
import networkx as nx
import osmnx as ox
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import itertools
import random
random.seed(1)

miles = 5

# The former location of the iconic Regal Theater, site of B.B. King's famous
# "Live at the Regal", among many other many, many others.
# https://en.wikipedia.org/wiki/Regal_Theater,_Chicago
center_coords = [41.80920440478678, -87.6160738081508]

def get_network(center_coords, miles_diameter, filepath = 'network.graphml'):
  if os.path.exists(filepath):
    G = ox.io.load_graphml(filepath)
  else:
    radius = 1609 * miles/2 # meters to miles
    G = ox.graph_from_point(center_coords, dist=radius, network_type="walk")
    ox.io.save_graphml(G, filepath)

  return(G)


G = get_network(center_coords, miles, 'thumbnail.graphml')

my_house_gdf = gpd.GeoDataFrame(
    geometry=gpd.points_from_xy([center_coords[1]], [center_coords[0]]), crs=ox.settings.default_crs
)
x = my_house_gdf.geometry.values.x[0]
y = my_house_gdf.geometry.values.y[0]

my_node = ox.nearest_nodes(G, x, y)

def get_ego_doughnut(G, origin_node, target, tol_lower, tol_upper = None, weight="length"):
  if tol_upper is None:
        tol_upper = tol_lower

  nodes = nx.single_source_dijkstra_path_length(G, origin_node, cutoff = target+tol_upper, weight = weight)
  nodes = [k for k,v in nodes.items() if v >= target-tol_lower]

  return nodes

doughnut_nodes = get_ego_doughnut(G, my_node, 1609 * 1, 1609 * 1 * .1 / 3)

# The if statement here just prevents us from drawing donuts that intersect
# with Lake Michigan
Cs = {node:get_ego_doughnut(G, node, 1609 * 1, 1609 * 1 * .1 / 3) for node in doughnut_nodes if G.nodes[node]['x'] < G.nodes[my_node]['x']}

intersections = {k:[n for n in v if n in doughnut_nodes] for k, v in Cs.items()}
intersections = {k:v for k,v in intersections.items() if len(v) > 0}

def get_bbox(G, A_doughnut, B_doughnut):
  nodes = A_doughnut + B_doughnut
  
  bbox = {
    "x_min":min(G.nodes[n]['x'] for n in nodes),
    "x_max":max(G.nodes[n]['x'] for n in nodes),
    "y_min":min(G.nodes[n]['y'] for n in nodes),
    "y_max":max(G.nodes[n]['y'] for n in nodes)
  }
  
  return(bbox)

def score_bbox_real(G, A_doughnut, B_doughnut):
  
  bbox = get_bbox(G, A_doughnut, B_doughnut)
  
  from shapely.geometry import Point
  import geopandas as gpd
  pnt1 = Point(bbox['x_min'], bbox['y_min'])
  pnt2 = Point(bbox['x_max'], bbox['y_min'])
  points_df = gpd.GeoDataFrame({'geometry': [pnt1, pnt2]}, crs='EPSG:4326')
  points_df = points_df.to_crs('EPSG:5234')
  points_df2 = points_df.shift() #We shift the dataframe by 1 to align pnt1 with pnt2
  d1 = points_df.distance(points_df2)[1]
  
  pnt1 = Point(bbox['x_min'], bbox['y_min'])
  pnt2 = Point(bbox['x_min'], bbox['y_max'])
  points_df = gpd.GeoDataFrame({'geometry': [pnt1, pnt2]}, crs='EPSG:4326')
  points_df = points_df.to_crs('EPSG:5234')
  points_df2 = points_df.shift() #We shift the dataframe by 1 to align pnt1 with pnt2
  d2 = points_df.distance(points_df2)[1]
  
  return(d1 / d2)

score_list_real = {n:score_bbox_real(G, doughnut_nodes, v) for n, v in Cs.items()}

best_score = 100
for k,v in score_list_real.items():
  ratio = 1
  if abs(v - ratio) < best_score:
    best_score = abs(v - ratio)
    best_node = k

targets = intersections[best_node]

lowest = 1000
for t in targets:
  if G.nodes[t]['y'] < lowest :
    target = t
    lowest = G.nodes[t]['y']

def create_route(A,B,C):
  A_to_B = ox.shortest_path(G, A, B)
  B_to_C = ox.shortest_path(G, B, C)
  C_to_A = ox.shortest_path(G, C, A)
  
  full_route = A_to_B + B_to_C[1:] + C_to_A[1:]
  
  return(full_route)

route = create_route(my_node, best_node, target)

route_gdf = ox.routing.route_to_gdf(G, route).to_crs(epsg=3857)
route_gdf = route_gdf.buffer(30)

node_gdf = ox.convert.graph_to_gdfs(G, edges = False).to_crs(epsg=3857)
node_gdf['id']=node_gdf.index.values
node_gdf = node_gdf[node_gdf['id'].isin([my_node] + [best_node] + [target] + doughnut_nodes + Cs[best_node])]

circles = node_gdf[~node_gdf['id'].isin([my_node, best_node, target])]
vertices = node_gdf[node_gdf['id'].isin([my_node, best_node, target])]

# plot the donuts
ax = circles.plot(
  color = "#000D4D",
  markersize = 10,
  zorder = 0.1
)

# plot the vertices of the triangles
vertices.plot(
  ax = ax,
  color = "#55CE58",
  markersize = 200,
  zorder = 1
)

# plot the "optimal" route
route_gdf.plot(
  ax = ax,
  color = "#FA7E19",
  zorder = .5
)

# add basemap
import contextily as cx
cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)

# save
ax.set_axis_off()
plt.gca().set_position([0, 0, 1, 1])
plt.savefig("route_example.png", pad_inches = 0, bbox_inches = 'tight')

# show
plt.show()
