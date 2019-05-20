#!/usr/bin/python3

import geopandas as gpd
import pandas as pd

def convert_tuple_to_list(t, level=0):
    '''
    param: t, is a tuple
    '''
    lista = []
    for t1 in t:
        if type(t1) is tuple:
            if level == 0:
                lista.append(convert_tuple_to_list(t1, level + 1))
            else:
                lista.extend(convert_tuple_to_list(t1, level + 1))
        else:
            lista.append(t1)
    return lista


def get_city_from_gadm(city_name, path):
    # GADM parameters
    # get only the columns we need
    COL_ID = 'GID_2'
    COL_NAME = 'NAME_2'
    COL_GEOM = 'geometry'

    gdf = gpd.read_file(path, crs = {'init' :'epsg:4326'})
    gdf = gdf[[COL_ID, COL_NAME, COL_GEOM]]

    # get only the boundary of city
    if city_name in gdf[COL_NAME].values:
        gdf = gdf[gdf[COL_NAME] == city_name]
    else:
        gdf = gdf[gdf[COL_NAME].str.contains(city_name)]

    return gdf.reset_index(drop=True)

def good_explode(df):
    """
    Explode muti-part geometries into multiple single geometries.
    Each row containing a multi-part geometry will be split into
    multiple rows with single geometries, thereby increasing the vertical
    size of the GeoDataFrame.
    The index of the input geodataframe is no longer unique and is
    replaced with a multi-index (original index with additional level
    indicating the multiple geometries: a new zero-based index for each
    single part geometry per multi-part geometry).
    Returns
    -------
    GeoDataFrame
        Exploded geodataframe with each single geometry
        as a separate entry in the geodataframe.
    """
    df_copy = df.copy()

    exploded_geom = df_copy.geometry.explode().reset_index(level=-1)
    #         exploded_index = exploded_geom.columns[0]

    df = pd.concat(
        [df_copy.drop(df_copy._geometry_column_name, axis=1),
         exploded_geom], axis=1)
    # reset to MultiIndex, otherwise df index is only first level of
    # exploded GeoSeries index.
    #         df.set_index(exploded_index, append=True, inplace=True)
    #         df.index.names = list(self.index.names) + [None]
    geo_df = df.set_geometry(df._geometry_column_name)

    return geo_df.drop(columns=['level_1']).reset_index(drop=True)


def flatten_col_list_value_from_df(df, col_name):
    empty_list = []
    for i in range(len(df)):
        empty_list.append(df.iloc[[i]][col_name][0])
    flat_list = [item for sublist in empty_list for item in sublist]

    return list(set(flat_list))