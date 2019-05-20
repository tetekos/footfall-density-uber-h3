#!/usr/bin/python3

import folium
import matplotlib.pyplot as plt
from src.generalFunctions import *

def plot_scatter(df, metric_col='cnt', x='lon', y='lat', marker='o', alpha=1, figsize=(20, 12), colormap='plasma'):
    '''
    this function is used when there is a dataframe with counts of some sort and we need to visualise it
    '''
    df.plot.scatter(x=x, y=y, c=metric_col, title=metric_col
                    , edgecolors='none', colormap=colormap, marker=marker, alpha=alpha, figsize=figsize);
    plt.xticks([], []);
    plt.yticks([], [])
    plt.title('hex-grid: Point Density')

def visualize_polyline_fromJson(boundary_geoJson, color, folium_map=None):
    first_boundary = boundary_geoJson['coordinates'][0]
    if type(first_boundary) == tuple:
        # convert tuple to list
        boundary = convert_tuple_to_list(first_boundary)
    boundary.append(boundary[0])
    final_boundary = [list(reversed(i)) for i in boundary]
    lat = [p[0] for p in final_boundary]
    lng = [p[1] for p in final_boundary]

    if folium_map is None:
        m = folium.Map(location=[sum(lat) / len(lat), sum(lng) / len(lng)], zoom_start=10, tiles='cartodbpositron')
    else:
        m = folium_map

    my_PolyLine = folium.PolyLine(locations=final_boundary, weight=4, opacity=0.6, color=color)
    m.add_child(my_PolyLine)

    return m


def add_polyline_to_folium_m(gdf, index, m, color):
    boundary_geoJson = gdf.iloc[[index]].geometry[0].__geo_interface__
    first_boundary = boundary_geoJson['coordinates'][0]
    if type(first_boundary) == tuple:
        # convert tuple to list
        boundary = convert_tuple_to_list(first_boundary)
    boundary.append(boundary[0])
    final_boundary = [list(reversed(i)) for i in boundary]

    my_PolyLine = folium.PolyLine(locations=final_boundary, weight=8, opacity=0.8, color=color)
    m.add_child(my_PolyLine)


def visualize_polylines_from_gdf_polygons(gdf, color, folium_map=None):
    '''
    the gdf must only have polygons as geometries. If multipolygon geometries, they will not be shown
    '''

    boundary_geoJson = gdf.iloc[[0]].geometry[0].__geo_interface__
    first_boundary = boundary_geoJson['coordinates'][0]
    if type(first_boundary) == tuple:
        # convert tuple to list
        boundary = convert_tuple_to_list(first_boundary)
    boundary.append(boundary[0])
    final_boundary = [list(reversed(i)) for i in boundary]
    #     lat = [p[0] for p in final_boundary]
    #     lng = [p[1] for p in final_boundary]

    if folium_map is None:
        m = folium.Map(location=[gdf.unary_union.centroid.y, gdf.unary_union.centroid.x], zoom_start=10,
                       tiles='cartodbpositron')
    else:
        m = folium_map

    my_PolyLine = folium.PolyLine(locations=final_boundary, weight=4, opacity=0.6, color=color)
    m.add_child(my_PolyLine)

    for i in range(len(gdf)):
        if i != 0:
            add_polyline_to_folium_m(gdf, i, m, color)

    return m