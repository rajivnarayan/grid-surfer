import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, StAggridTheme
import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import json
import numpy as np
import requests
import re
import io
from collections import namedtuple
from vega_datasets import local_data
import altair as alt
from src.ui import gs_utils as gsu
from src.ui import describe, dotplot, distplot, xyplot

@st.cache_data
def read_data(fd, file_type):
    if file_type=='text/csv':
        df = pd.read_csv(fd)
    elif file_type in ['text/plain', 'text/tab-separated-values'] :
        df = pd.read_csv(fd, sep='\t')
    elif file_type=='application/json':
        df = pd.json_normalize(json.load(fd))
    else:
        st.error(f"Unsupported file format: {file_type}")
    return df

@st.cache_data
def data_loader(uploaded_file):
    
    if isinstance(uploaded_file, io.BytesIO):
        try:
            df = read_data(uploaded_file, uploaded_file.type)
        except Exception as e:
            st.error("An error occured loading the file.")
            st.exception(e) 
    elif isinstance(uploaded_file, tuple):
        if uploaded_file.source == 'vega-dataset':
            df = local_data(uploaded_file.file)
        elif uploaded_file.source == 'local-dataset':                
            try:
                df = read_data(open(uploaded_file.file), uploaded_file.type)
            except Exception as e:
                st.error("An error occured loading the file.")
                st.exception(e)
    return df

def render_body(h_data_options):
    # Load data
    data_file = st.session_state['data_file']
    if data_file is not None:
        df_all = data_loader(data_file)
        with h_data_options:            
            df = filter_dataframe(df_all)
        h_plot = st.expander('Analyze',
                             expanded=True,
                             icon=':material/insert_chart:')
        h_grid = st.expander('View Table',
                             expanded=False,
                             icon=':material/table_view:')
        
        # Data table
        with h_grid:
            # h_grid_options = st.pills("Grid Options",
            #                     ["Select columns", "Filter data"],
            #                     default=None,
            #                     label_visibility = 'collapsed')
            grid_return = render_grid(df, h_data_options)
    
        # Visualization selector
        # Use pills since st.tabs do not support independent rendering
        with h_plot:
            plot_select = st.pills("Plots",
                                ["Describe", "Histogram", "Dot", "Scatter"],
                                default='Describe',
                                label_visibility = 'collapsed')
            if plot_select=='Describe':
                # Descriptive statistics
                describe.show_description(grid_return)
                # ctypes = gsu.get_df_column_types(grid_return.data)
                # df_desc_num = (df
                #             .loc[:, ctypes['num_columns']]
                #             .describe()
                #             .T
                #             .rename_axis('field')
                #             .style.format(precision=2)                           
                #             )
                # df_desc_cat = (df
                #             .loc[:, ctypes['cat_columns']]
                #             .describe()
                #             .T
                #             .rename_axis('field')
                #             .style.format(precision=2)
                #     )
                # tab_num, tab_cat = st.tabs(['Numeric', 'Categorical'])
                # tab_num.dataframe(df_desc_num, use_container_width=False)
                # tab_cat.dataframe(df_desc_cat, use_container_width = False)
            if plot_select=='Histogram':
                # Histogram
                chart_dist = distplot.make_dist_plot(grid_return)
            elif plot_select=='Dot':
                # Dot plot
                chart_dot = dotplot.make_dot_plot(grid_return)            
            elif plot_select=='Scatter':
                # Scatter plot
                chart_xy = xyplot.make_xy_plot(grid_return)            

    return None

def render_grid(df: pd.DataFrame,
                h_data_options) -> AgGrid:
    """Render Grid"""
    # Infer basic colDefs from dataframe types
    gb = GridOptionsBuilder.from_dataframe(df)
    opt = {"rowSelection": {"mode": "multiRow"}, 
           "autoSizeStrategy" : {"type": 'fitGridWidth'},}
    gb.configure_grid_options(**opt)
    # customize gridOptions
    gb.configure_default_column(
        min_column_width=25,
        alwaysShowHorizontalScroll=True,
        alwaysShowVerticalScroll=False,
        filterable=False,        
        groupable=True,
        editable=False)        
    # Note the sidebar is only available with the enterprise version
    # i.e. set enable_enterprise_modules=True in AgGrid() call
    gb.configure_side_bar(filters_panel=True, columns_panel=True)
    # set precision of numeric columns
    for f in df.dtypes[df.dtypes=='float64'].index:
        gb.configure_column(f, type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
    gridOptions = gb.build()
    column_defs = gridOptions['columnDefs']
    # Set all columns to be filterable
    for col in column_defs:
        col['filter'] = False        
    with h_data_options: 
        columns_to_show = st.multiselect('Display columns:',
                                         help = 'Pick columns to display in the grid',
                                         options=df.columns,
                                         default=df.columns)

    columns_to_hide=set(df.columns).difference(columns_to_show)
    for col in column_defs:
        if col['headerName'] in columns_to_hide:
            col['hide']=True

    grid = AgGrid(df, 
                gridOptions=gridOptions,
                fit_columns_on_grid_load=True,
                enable_enterprise_modules=False,
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED)    
    return grid


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    
    See: https://blog.streamlit.io/auto-generate-a-dataframe-filtering-ui-in-streamlit-with-filter_dataframe/
    """
    modify = st.checkbox("Conditional Filters", help='Filter data columns conditionally')

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df