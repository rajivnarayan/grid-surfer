import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, StAggridTheme
import pandas as pd
import numpy as np
import requests
import re
from decimal import Decimal
import altair as alt
    
@st.cache_data
def load_data(file_path):
    # auto-detects csv or txt
    df=pd.read_csv(file_path, sep=None)
    #st.toast('read file')
    return df

def format_float(f):
    d=Decimal(str(f));
    return d.quantize(Decimal(1)) if d ==d.to_integral() else d.normalize()

def nlogp(p: float, base:int=10) -> float:
    min_nz_p=0.01*np.min(p[p]>0)
    return -np.log(np.clip(p, min_nz_p, 1))/np.log(base)

def get_axis_scale(scale_str):
    """
    This function takes a scale string as input and returns an Altair Scale object based on the provided scale type.
    
    Parameters:
    scale_str (str): A string representing the scale type. It can be one of the following:
    - 'linear': Linear scale
    - 'log10': Logarithmic scale with base 10
    - 'log2': Logarithmic scale with base 2
    
    Returns:
    alt.Scale: An Altair Scale object configured according to the specified scale type.
    """
    scale_lut={'linear': {'type':'linear'},
    'log10' : {'type':'log', 'base':10},
    'log2' : {'type':'log', 'base':2}
    }
    return alt.Scale(**scale_lut[scale_str])

def render_body(data_file, h_sidebar):
    # Load data
    if data_file is not None:
        df=load_data(data_file) 

        # Data table
        grid_return=render_grid(df, h_sidebar)
    

        # Visualization selector
        # Note: st.tabs does not support independent rendering
        plot_select=st.radio("Plots",
                              ["Histogram", "Dot", "Scatter"],
                              index=0,
                              horizontal=True,
                              label_visibility='collapsed')
        
        if plot_select=='Histogram':
            # Distribution plot
            chart_dist=render_dist_plot(grid_return)
        elif plot_select=='Dot':
            # Bar plot
            chart_bar=render_dot_plot(grid_return)            
        elif plot_select=='Scatter':
            # Scatter plot
            chart_xy=render_xy_plot(grid_return)            
        else:
            pass            

    return None

def render_grid(df, h_sidebar):
    """Render Grid"""
    # Infer basic colDefs from dataframe types
    gb=GridOptionsBuilder.from_dataframe(df)
    opt={"rowSelection": {"mode": "multiRow"}}
    gb.configure_grid_options(**opt)
    # customize gridOptions
    gb.configure_default_column(
        min_column_width=25,
        alwaysShowHorizontalScroll=True,
        alwaysShowVerticalScroll=False,
        filterable=True,        
        groupable=True,
        editable=False)        
    # Note the sidebar only available with the enterprise version
    # i.e. set enable_enterprise_modules=True in AgGrid() call
    gb.configure_side_bar(filters_panel=True, columns_panel=True)
    # set precision of numeric columns
    for f in df.dtypes[df.dtypes=='float64'].index:
        gb.configure_column(f, type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
    gridOptions=gb.build()
    column_defs=gridOptions['columnDefs']
    # Set all columns to be filterable
    for col in column_defs:
        col['filter']=True        
    with h_sidebar:  
        columns_to_show=st.multiselect('Grid Columns:', options=df.columns, default=df.columns)

    columns_to_hide=set(df.columns).difference(columns_to_show)
    for col in column_defs:
        if col['headerName'] in columns_to_hide:
            col['hide']=True

    grid=AgGrid(df, 
                gridOptions=gridOptions,
                fit_columns_on_grid_load=True,
                enable_enterprise_modules=False,
                theme='fresh', 
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED)    
    return grid

def get_df_column_types(df):
    is_numeric=df.dtypes!='object'
    column_types={}
    column_types['all_columns']=df.columns
    column_types['num_columns']=df.columns[is_numeric].tolist()
    column_types['cat_columns']=df.columns[~is_numeric].tolist()
    return column_types

def render_xy_plot(grid_return):
    """ Plot scatter
    """
    ctypes=get_df_column_types(grid_return.data)
    h_options, h_main=st.columns([0.20, 0.80], gap='medium')
    # settings and options
    picks, opts_mark, opts_scale=render_xy_options(h_options, ctypes)

    # main viz        
    with h_main:
        mark_kwds=opts_mark            
        kwds={'x' : alt.X(picks['x_axis'], 
                    scale=get_axis_scale(opts_scale['x_scale']),
                    axis=alt.Axis(tickCount=9, format='2.4g')), 
                'y': alt.Y(picks['y_axis'], 
                    scale=get_axis_scale(opts_scale['y_scale']),
                    axis=alt.Axis(tickCount=9, format='2.4g')),
                }
        tooltips=picks['add_tooltips'] or []
        select_fields=[]
        facet_header=alt.Header(titleFontSize=20, labelFontSize=20, 
                                    labelAnchor='middle', 
                                    labelColor='blue', 
                                    labelFontWeight='normal',
                                    titleFontWeight='bold',
                                    titleAnchor='middle', 
                                    labelAlign='left')
        
        if picks['facet_by_column'] is not None:
            kwds['column']=alt.Facet(picks['facet_by_column'], header=facet_header)
            #tooltips.extend([picks['column']])

        if picks['facet_by_row'] is not None:
            kwds['row']=alt.Facet(picks['facet_by_row'], header=facet_header)
            #tooltips.extend([picks['row']])

        if picks['color_by'] is not None:
            kwds['color']={"field": picks['color_by'], "scale": {"scheme": "tableau10"}}
            tooltips.extend([picks['color_by']])
            select_fields.extend([picks['color_by']])

        if picks['size_by'] is not None:
            kwds['size']=picks['size_by']
            tooltips.extend([picks['size_by']])
            select_fields.extend([picks['size_by']])

        if picks['shape_by'] is not None:                
            kwds['shape']=picks['shape_by']
            tooltips.extend([picks['shape_by']])
            select_fields.extend([picks['shape_by']])

        tooltips.extend([
                alt.Tooltip(picks['x_axis'], format="0.2f"),
                alt.Tooltip(picks['y_axis'], format="0.2f")])

        kwds['tooltip']=tooltips
        
        if select_fields:
            selection=alt.selection_multi(fields=select_fields)
        else:
            selection=alt.selection_multi()
        
        chart=(
            alt.Chart(data=grid_return.data)
            .mark_point(**mark_kwds)
            .encode(**kwds)
            .configure_axis(labelFontSize=20, titleFontSize=20, titleFontWeight='bold')
            .add_selection(selection)
            .transform_filter(selection)
            )                                                        
        st.altair_chart(chart, use_container_width=False)
    return chart

def render_dot_plot(grid_return):
    """"""
    ctypes=get_df_column_types(grid_return.data)
    h_options, h_main=st.columns([0.20, 0.80], gap='medium')
    # settings and options
    picks, opts_mark, opts_scale=render_dot_options(h_options, ctypes)

    # main viz        
    with h_main:
        mark_kwds=opts_mark            
        kwds={'x' : alt.X(picks['x_axis']),
                'y': alt.Y(picks['y_axis'])
                }
        tooltips=picks.get('add_tooltips', [])
        select_fields=[]
        facet_header=alt.Header(titleFontSize=20, labelFontSize=20, 
                                    labelAnchor='middle', 
                                    labelColor='blue', 
                                    labelFontWeight='normal',
                                    titleFontWeight='bold',
                                    titleAnchor='middle', 
                                    labelAlign='left')
        
        if picks['facet_by_column'] is not None:
            kwds['column']=alt.Facet(picks['facet_by_column'], header=facet_header)
            #tooltips.extend([picks['column']])

        if picks['facet_by_row'] is not None:
            kwds['row']=alt.Facet(picks['facet_by_row'], header=facet_header)
            #tooltips.extend([picks['row']])

        if picks['color_by'] is not None:
            kwds['color']={"field": picks['color_by'], "scale": {"scheme": "tableau10"}}
            tooltips.extend([picks['color_by']])
            select_fields.extend([picks['color_by']])

        tooltips.extend([
                alt.Tooltip(picks['x_axis']),
                alt.Tooltip(picks['y_axis'], format="0.2f")])

        kwds['tooltip']=tooltips
        
        if select_fields:
            selection=alt.selection_multi(fields=select_fields)
        else:
            selection=alt.selection_multi()
        
        chart=(
            alt.Chart(data=grid_return.data)
            .mark_point(**mark_kwds)
            .encode(**kwds)
            .configure_axis(labelFontSize=20, titleFontSize=20, titleFontWeight='bold')
            .add_selection(selection)
            .transform_filter(selection)
            )                                                        
        st.altair_chart(chart, use_container_width=False)
    return chart


def render_dist_plot(grid_return):
    """Distribution Plot"""
    ctypes=get_df_column_types(grid_return.data)
    h_options, h_main=st.columns([0.20, 0.80], gap='medium')
    # settings and options
    picks, opts_mark, opts_scale=render_dist_options(h_options, ctypes)

    # main viz        
    with h_main:
        mark_kwds=opts_mark            
        kwds={'x' : alt.X(picks['x_axis']).bin(maxbins=picks['bins']),
                'y': alt.Y('count()').stack(None)
                }
        tooltips=picks.get('add_tooltips', [])
        select_fields=[]
        facet_header=alt.Header(titleFontSize=20, labelFontSize=20, 
                                    labelAnchor='middle', 
                                    labelColor='blue', 
                                    labelFontWeight='normal',
                                    titleFontWeight='bold',
                                    titleAnchor='middle', 
                                    labelAlign='left')
        
        if picks['facet_by_column'] is not None:
            kwds['column']=alt.Facet(picks['facet_by_column'], header=facet_header)
            #tooltips.extend([picks['column']])

        if picks['facet_by_row'] is not None:
            kwds['row']=alt.Facet(picks['facet_by_row'], header=facet_header)
            #tooltips.extend([picks['row']])

        if picks['color_by'] is not None:
            kwds['color']={"field": picks['color_by'], "scale": {"scheme": "tableau10"}}
            tooltips.extend([picks['color_by']])
            select_fields.extend([picks['color_by']])

        tooltips.extend([
                alt.Tooltip(picks['x_axis'])])

        kwds['tooltip']=tooltips
        
        if select_fields:
            selection=alt.selection_multi(fields=select_fields)
        else:
            selection=alt.selection_multi()
        
        chart=(
            alt.Chart(data=grid_return.data)
            .mark_bar(**mark_kwds)
            .encode(**kwds)
            .configure_axis(labelFontSize=20, titleFontSize=20, titleFontWeight='bold')
            .add_selection(selection)
            .transform_filter(selection)
            )                                                        
        st.altair_chart(chart, use_container_width=False)
    return chart

def pick_if_present(items, to_check):
    items_found=set(items).intersection(set(to_check))      
    pick=items.index(next(iter(items_found or []), items[0]))
    return pick, items_found

def render_xy_options(h_options, ctypes):

    mark_props={
        'opacity' : {'min_value' : 0.0, 'max_value': 1.0, 'step' : 0.1, 'value' : 0.7},
        'size' : {'min_value' : 0, 'max_value' : 500, 'step' : 10, 'value' : 30},
        'strokeWidth' : {'min_value' : 0.0, 'max_value' : 10.0, 'step' : 0.5, 'value' : 2.0},
        'shape' : {'value': 'circle'},
        'color' : {'value': '#7570b3'},  
        'filled': {'value': True}
    }
    scale_props={
        'x_scale' : {'options' : ['linear', 'log2', 'log10'], 'index': 0},
        'y_scale' : {'options' : ['linear', 'log2', 'log10'], 'index': 0}
    }

    opts_mark={}
    opts_scale={}
    
    names_tocheck=['gene_name', 'gene_symbol', 'name', 'treatment', 'target_name']
    x_to_check=['x', 'treatment', 'group']
    y_to_check=['y', 'ss_ngene']
    names_list=set([e for e in ctypes['cat_columns'] for n in names_tocheck if n in e])       
    x_list=set(ctypes['num_columns']).intersection(set(x_to_check)) 
    y_list=set(ctypes['num_columns']).intersection(set(y_to_check))
    
    default_tooltip=next(iter(names_list or []), None)      
    #default_x=ctypes['num_columns'].index(next(iter(x_list or []), ctypes['num_columns'][0]))              
    default_x, x_found=pick_if_present(ctypes['num_columns'], x_to_check)
    default_y, y_found=pick_if_present(ctypes['num_columns'], y_to_check)
    #default_y=ctypes['num_columns'].index(next(iter(y_list or []), ctypes['num_columns'][0]))

    params={}

    with h_options.container():
        with st.popover('Settings :material/tune:'):
            # scale properties
            opts_scale['x_scale']=st.selectbox('X-Axis Scale:', **scale_props['x_scale'])
            opts_scale['y_scale']=st.selectbox('Y-Axis Scale:', **scale_props['y_scale'])
            # mark properties
            opts_mark['opacity']=st.slider('Opacity:', **mark_props['opacity'])
            opts_mark['size']=st.slider('Size:', **mark_props['size'])
            opts_mark['strokeWidth']=st.slider('Stroke Width:', **mark_props['strokeWidth'])
            opts_mark['color']=st.color_picker('Color:', **mark_props['color'])
            opts_mark['filled']=st.checkbox('Fill Markers:', **mark_props['filled'])

        params['x_axis']=st.selectbox('X-Axis:', ctypes['num_columns'], index=default_x)
        params['y_axis']=st.selectbox('Y-Axis:', ctypes['num_columns'], index=default_y)
        params['color_by']=st.selectbox('Color:', ctypes['cat_columns'], index=None)
        params['size_by']=st.selectbox('Size:', ctypes['all_columns'], index=None)
        params['shape_by']=st.selectbox('Shape:', ctypes['all_columns'], index=None)
        params['facet_by_column']=st.selectbox('Column Facet:', ctypes['cat_columns'], index=None)
        params['facet_by_row']=st.selectbox('Row Facet:', ctypes['cat_columns'], index=None)
        params['add_tooltips']=st.multiselect('Tooltips:', ctypes['all_columns'], default=names_list)

    return (params, opts_mark, opts_scale)

def render_dot_options(h_options, ctypes):
    """Get parameters and options for distribution plots"""
    names_tocheck=['gene_name', 'gene_symbol', 'name', 'treatment', 'target_name']
    x_to_check=['x', 'cc_q75']
    y_to_check=['y', 'ss_ngene']
    names_list=set([e for e in ctypes['cat_columns'] for n in names_tocheck if n in e])  
    #x_list=set(ctypes['cat_columns']).intersection(set(x_to_check))      
    #y_list=set(ctypes['num_columns']).intersection(set(y_to_check))
    
    default_tooltip=next(iter(names_list or []), None)                
    #default_x=ctypes['cat_columns'].index(next(iter(x_list or []), ctypes['cat_columns'][0]))
    #default_y=ctypes['num_columns'].index(next(iter(y_list or []), ctypes['num_columns'][0]))
    default_x, _=pick_if_present(ctypes['cat_columns'], x_to_check)
    default_y, _=pick_if_present(ctypes['num_columns'], y_to_check)
    params={}
    opts_mark={}
    opts_scale={}
    
    with h_options.container():
        with st.popover('Settings :material/tune:'):
            # scale properties
            opts_scale['x_scale']=st.selectbox('X-Axis Scale:', 
                                                 options=['linear', 'log2', 'log10'], 
                                                 index=0)
            opts_scale['y_scale']=st.selectbox('Y-Axis Scale:', 
                                                 options=['linear', 'log2', 'log10'], 
                                                 index=0)
            # mark properties
            opts_mark['color']=st.color_picker('Color:', value='#4e79a7')

        params['x_axis']=st.selectbox('X-Axis:', ctypes['cat_columns'], index=default_x)
        params['y_axis']=st.selectbox('Y-Axis:', ctypes['num_columns'], index=default_y)
        params['color_by']=st.selectbox('Color:', ctypes['cat_columns'], index=None)
        params['facet_by_column']=st.selectbox('Column Facet:', ctypes['cat_columns'], index=None)
        params['facet_by_row']=st.selectbox('Row Facet:', ctypes['cat_columns'], index=None)

    return (params, opts_mark, opts_scale)

def render_dist_options(h_options, ctypes):
    """Get parameters and options for distribution plots"""
    names_tocheck=['gene_name', 'gene_symbol', 'name', 'treatment', 'target_name']
    x_to_check=['x', 'cc_q75']
    names_list=set([e for e in ctypes['cat_columns'] for n in names_tocheck if n in e])  
    
    default_tooltip=next(iter(names_list or []), None)                
    default_x, x_found=pick_if_present(ctypes['num_columns'], x_to_check)
    params={}
    opts_mark={}
    opts_scale={}
    
    with h_options.container():
        with st.popover('Settings :material/tune:'):
            # scale properties
            opts_scale['y_scale']=st.selectbox('Y-Axis Scale:', 
                                                 options=['linear', 'log2', 'log10'], 
                                                 index=0)
            # mark properties
            opts_mark['color']=st.color_picker('Color:', value='#4e79a7')

        params['x_axis']=st.selectbox('X-Axis:', ctypes['num_columns'], index=default_x)
        params['bins']=st.slider('Bins:', min_value=5, max_value=200, step=5, value=30 )
        params['color_by']=st.selectbox('Color:', ctypes['cat_columns'], index=None)
        params['facet_by_column']=st.selectbox('Column Facet:', ctypes['cat_columns'], index=None)
        params['facet_by_row']=st.selectbox('Row Facet:', ctypes['cat_columns'], index=None)

    return (params, opts_mark, opts_scale)