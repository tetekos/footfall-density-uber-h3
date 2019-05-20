#!/usr/bin/python3


from h3 import h3
import pandas as pd
import folium
import geohash2
from src.generalFunctions import *


def get_hexagons_fromJson(boundary_geoJson, aperture):
    '''

    :param boundary_geoJson: only polygon
    :param aperture: the hex size
    :return: list of hexagons
    '''

    # https://github.com/uber/h3-py/blob/master/h3/h3.py
    hexagons = list(h3.polyfill(boundary_geoJson, aperture, geo_json_conformant=True))
    return hexagons


def get_hexagons_from_gdf(gdf, geometry_column, boundary_id, aperture):
    # convert the multipolygons to polygons by our custom explode function
    polygonOnly_gdf1 = good_explode(gdf)
    polygonOnly_gdf1['hex_list_before'] = polygonOnly_gdf1[geometry_column].apply(
        lambda x: get_hexagons_fromJson(x.__geo_interface__, aperture))
    polygonOnly_gdf1_group = polygonOnly_gdf1.groupby(boundary_id)
    # count the sum of hexagons in each unique id
    final_df = pd.DataFrame(polygonOnly_gdf1_group.apply(lambda grp: grp['hex_list_before'].sum()))
    # reset the index and rename the 0 column
    final_df.reset_index(inplace=True)
    final_df.rename(columns={0: 'hex_list'}, inplace=True)
    # count again the final number of hexagons for each unique id
    final_df['hex_list_length'] = final_df['hex_list'].apply(lambda x: len(x))
    return final_df


def from_df_points_to_df_hexagon_cnt(df, aperture, lat='lat', lon='lon', ):
    '''
    this function is used to convert a dataframe with points but no hex and hex lat/lon
     to a dataframe of hexagons with counts of the points
    :param df: the dataframe with points
    :param lat: point latitude
    :param lon: point longitude
    :param aperture: the size of the hexagon
    :return: a dataframe with hex column, the count in each hexagon and lat, lon of the center of each hex
    '''
    hex_col = 'hex' + str(aperture)

    # find hexs containing the points
    df[hex_col] = df.apply(lambda x: h3.geo_to_h3(x[lat], x[lon], aperture), axis=1)

    # aggregate the points
    df_g = df.groupby(hex_col).size().to_frame('cnt').reset_index()

    # find center of hex for visualization
    df_g['lat'] = df_g[hex_col].apply(lambda x: h3.h3_to_geo(x)[0])
    df_g['lon'] = df_g[hex_col].apply(lambda x: h3.h3_to_geo(x)[1])

    return df_g


def from_df_points_to_df_geohash_cnt(df, hash_size, lat='lat', lon='lon', ):
    '''
    this function is used to convert a dataframe with points to a dataframe of geohashes with counts of the points
    :param df: the dataframe with points
    :param lat: point latitude
    :param lon: point longitude
    :param aperture: the size of the geohash
    :return: a dataframe with hash column, the count in each geohash and lat, lon of the center of each geohash
    '''
    hash_col = 'hash' + str(hash_size)

    # find geohashes containing the points
    df[hash_col] = df.apply(lambda x: geohash2.encode(x[lat], x[lon], hash_size), axis=1)

    # aggregate the points
    df_g = df.groupby(hash_col).size().to_frame('cnt').reset_index()

    # find center of hex for visualization
    df_g['lat'] = df_g[hash_col].apply(lambda x: geohash2.decode(x)[0])
    df_g['lon'] = df_g[hash_col].apply(lambda x: geohash2.decode(x)[1])

    return df_g


def visualise_hex_of_boundaryId_from_flatten_df(*boundary_id, flatten_gdf, compaction=False):
    boundary_df = flatten_gdf[flatten_gdf.GID_2.isin(boundary_id)]
    if not compaction:
        return visualize_hexagon_and_boundary_from_hexagons_and_boundaryJson(boundary_df.hex.unique().tolist(),
                                                                             boundary_df.geometry[0].__geo_interface__)
    else:
        return visualize_hexagon_and_boundary_from_hexagons_and_boundaryJson(
            h3.compact(boundary_df.hex.unique().tolist()),
            boundary_df.geometry[0].__geo_interface__)


def visualize_hexagon_and_boundary_from_hexagons_and_boundaryJson(hexagons, boundary_geoJson, folium_map=None):
    # hexagons
    polylines = []
    lat = []
    lng = []
    for hex in hexagons:
        polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
        # flatten polygons into loops.
        outlines = [loop for polygon in polygons for loop in polygon]
        polyline = [outline + [outline[0]] for outline in outlines][0]
        lat.extend(map(lambda v: v[0], polyline))
        lng.extend(map(lambda v: v[1], polyline))
        polylines.append(polyline)

    # boundary
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

    for polyline in polylines:
        my_PolyLine = folium.PolyLine(locations=polyline, weight=4, opacity=0.6, color='red')
        m.add_child(my_PolyLine)

    my_Boundary = folium.PolyLine(locations=final_boundary, weight=4, opacity=0.6, color='green')
    m.add_child(my_Boundary)

    return m


def visualize_hexagons_and_boundary_from_boundaryJson(boundary_geoJson, aperture, folium_map=None):
    '''

    :param boundary_geoJson: only POLYGON
    :param aperture: size of hex
    :param folium_map:
    :return: folium map
    '''
    first_boundary = boundary_geoJson['coordinates'][0]
    if type(first_boundary) == tuple:
        # convert tuple to list
        boundary = convert_tuple_to_list(first_boundary)
    boundary.append(boundary[0])
    final_boundary = [list(reversed(i)) for i in boundary]
    lat = [p[0] for p in final_boundary]
    lng = [p[1] for p in final_boundary]

    if folium_map is None:
        m = folium.Map(location=[sum(lat) / len(lat), sum(lng) / len(lng)], zoom_start=13, tiles='cartodbpositron')
    else:
        m = folium_map

    my_PolyLine = folium.PolyLine(locations=final_boundary, weight=8, color="green")
    m.add_child(my_PolyLine)

    # https://github.com/uber/h3-py/blob/master/h3/h3.py
    hexagons = list(h3.polyfill(boundary_geoJson, aperture, geo_json_conformant=True))
    polylines = []
    lat = []
    lng = []
    for hex in hexagons:
        polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
        # flatten polygons into loops.
        outlines = [loop for polygon in polygons for loop in polygon]
        polyline = [outline + [outline[0]] for outline in outlines][0]
        lat.extend(map(lambda v: v[0], polyline))
        lng.extend(map(lambda v: v[1], polyline))
        polylines.append(polyline)
    for polyline in polylines:
        my_PolyLine = folium.PolyLine(locations=polyline, weight=8, color='red')
        m.add_child(my_PolyLine)

    return m


def visualize_polygon(color, hexagons=None, points_polyline=None, folium_map=None):
    if hexagons and points_polyline:
        raise ValueError("Either hexagons or points_polyline as args")
    elif hexagons:
        polyline = h3.h3_set_to_multi_polygon(hexagons)[0][0]
    elif points_polyline:
        polyline = points_polyline
    else:
        raise ValueError("Either hexagons or points_polyline as args")

    polyline.append(polyline[0])
    lat = [p[0] for p in polyline]
    lng = [p[1] for p in polyline]

    if folium_map is None:
        m = folium.Map(location=[sum(lat) / len(lat), sum(lng) / len(lng)], zoom_start=10, tiles='cartodbpositron')
    else:
        m = folium_map

    my_PolyLine = folium.PolyLine(locations=polyline, weight=4, opacity=0.6, color=color)
    m.add_child(my_PolyLine)

    return m


def visualize_hexagons(hexagons, color="red", folium_map=None):
    """
    hexagons is a list of hexcluster. Each hexcluster is a list of hexagons.
    eg. [[hex1, hex2], [hex3, hex4]]
    """
    polylines = []
    lat = []
    lng = []
    for hex in hexagons:
        polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
        # flatten polygons into loops.
        outlines = [loop for polygon in polygons for loop in polygon]
        polyline = [outline + [outline[0]] for outline in outlines][0]
        lat.extend(map(lambda v: v[0], polyline))
        lng.extend(map(lambda v: v[1], polyline))
        polylines.append(polyline)

    if folium_map is None:
        m = folium.Map(location=[sum(lat) / len(lat), sum(lng) / len(lng)], zoom_start=10, tiles='cartodbpositron')
    else:
        m = folium_map
    for polyline in polylines:
        my_PolyLine = folium.PolyLine(locations=polyline, weight=4, opacity=0.6, color=color)
        m.add_child(my_PolyLine)
    return m


