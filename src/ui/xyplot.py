import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from st_aggrid import AgGrid
from src.ui import gs_utils as gsu

"""
Functions to create XY / scatter plots
"""

def make_xy_plot(grid_return: AgGrid):
    """ Render scatter plot in ui
    """
    ctypes = gsu.get_df_column_types(grid_return.data)
    # settings and options
    opts, opts_type = get_xy_options(ctypes)
    
    # main viz        
    chart = plot_xy(grid_return.data, opts, opts_type)
    st.altair_chart(chart, use_container_width=False)

def plot_xy(df: pd.DataFrame, opts:dict, opts_type:dict) -> alt.Chart:
    """Generate XY plot"""
    mark_kwds={k: opts.get(k) for k in opts_type['mark']}
    kwds={'x' : alt.X(opts['x_axis'], 
                scale = gsu.get_axis_scale(opts['x_scale']),
                axis=alt.Axis(tickCount=9, format = '2.4g')), 
            'y': alt.Y(opts['y_axis'], 
                scale = gsu.get_axis_scale(opts['y_scale']),
                axis = alt.Axis(tickCount=9, format = '2.4g')),
            }
    tooltips=opts['add_tooltips'] or []
    select_fields=[]
    facet_header=alt.Header(titleFontSize=20,
                            labelFontSize=20, 
                            labelAnchor='middle', 
                            labelColor='#808080', 
                            labelFontWeight='normal',
                            titleFontWeight='bold',
                            titleAnchor='middle', 
                            labelAlign='center')
    
    if opts['column_facet'] is not None:
        kwds['column'] = alt.Facet(opts['column_facet'], header=facet_header)
        #tooltips.extend([opts['column']])

    if opts['row_facet'] is not None:
        kwds['row'] = alt.Facet(opts['row_facet'], header=facet_header)
        #tooltips.extend([opts['row']])

    if opts['color_by'] is not None:
        kwds['color'] = {"field": opts['color_by'], "scale": {"scheme": "tableau10"}}
        tooltips.extend([opts['color_by']])
        select_fields.extend([opts['color_by']])

    if opts['size_by'] is not None:
        kwds['size'] = opts['size_by']
        tooltips.extend([opts['size_by']])
        select_fields.extend([opts['size_by']])

    if opts['shape_by'] is not None:                
        kwds['shape'] = opts['shape_by']
        tooltips.extend([opts['shape_by']])
        select_fields.extend([opts['shape_by']])

    tooltips.extend([
            alt.Tooltip(opts['x_axis'], format="0.2f"),
            alt.Tooltip(opts['y_axis'], format="0.2f")])

    kwds['tooltip']=tooltips
    
    if select_fields:
        selection=alt.selection_multi(fields=select_fields)
    else:
        selection=alt.selection_multi()
    
    chart=(
        alt.Chart(data=df)
        .mark_point(**mark_kwds)
        .encode(**kwds)
        .configure_axis(labelFontSize=16,
                        titleFontSize=16,
                        titleFontWeight='bold')
        .configure_view(stroke = '#808080',
                        strokeWidth = 1.5)                            
        .add_selection(selection)
        .transform_filter(selection)
        .properties(width=opts['width'],
                    height=opts['height'])
        )                                                        
    return chart


def get_xy_options(ctypes):

    mark_props={
        'opacity' : {'min_value' : 0.0, 'max_value': 1.0, 'step' : 0.1, 'value' : 0.7},
        'size' : {'min_value' : 0, 'max_value' : 500, 'step' : 10, 'value' : 30},
        'strokeWidth' : {'min_value' : 0.0, 'max_value' : 10.0, 'step' : 0.5, 'value' : 2.0},
        'color' : {'value': '#7570b3'},  
        'filled': {'value': True}
    }
    scale_props={
        'x_scale' : {'options' : ['linear', 'log2', 'log10'], 'index': 0},
        'y_scale' : {'options' : ['linear', 'log2', 'log10'], 'index': 0}
    }
   
    names_tocheck=['gene_name', 'gene_symbol', 'name', 'treatment', 'target_name']
    x_to_check = ['x', 'treatment', 'group']
    y_to_check = ['y', 'ss_ngene']
    default_tooltip, names_list = gsu.pick_if_present(ctypes['cat_columns'], 
                                                      names_tocheck)    
    default_x, x_list = gsu.pick_if_present(ctypes['num_columns'],
                                            x_to_check, default=0)
    default_y, y_list = gsu.pick_if_present(ctypes['num_columns'], 
                                            y_to_check, default=1)

    opts={}
    #with st.expander('Parameters:', expanded=True):
    with st.sidebar:
        with st.container(border=True):
            st.write('**Scatter plot**')
            with st.popover('Fine tune', 
                            icon=':material/tune:',
                            use_container_width=True):
                # scale properties
                opts['x_scale'] = st.selectbox('X-Axis Scale:',
                                                **scale_props['x_scale'])
                opts['y_scale'] = st.selectbox('Y-Axis Scale:',
                                                **scale_props['y_scale'])
                opts['agg_average'] = st.selectbox('Show Averages:',
                                            ['median', 'mean'],
                                            index=0)
                opts['width'] = st.slider('Plot width:',
                                        min_value=50,
                                        max_value=1000,
                                        step=25,
                                        value=400)
                opts['height'] = st.slider('Plot height:',
                                        min_value=50,
                                        max_value=1000,
                                        step=25,
                                        value=400)            
                # mark properties
                opts['opacity'] = st.slider('Opacity:',
                                            **mark_props['opacity'])
                opts['size'] = st.slider('Size:',
                                        **mark_props['size'])
                opts['strokeWidth'] = st.slider('Stroke Width:',
                                                **mark_props['strokeWidth'])
                opts['color'] = st.color_picker('Color:',
                                                **mark_props['color'])
                opts['filled'] = st.checkbox('Fill Markers:',
                                            **mark_props['filled'])        
            opts['x_axis'] = st.selectbox('X-Axis:',
                                        ctypes['num_columns'],
                                        index=default_x)
            opts['y_axis'] = st.selectbox('Y-Axis:',
                                        ctypes['num_columns'],
                                        index=default_y)
            opts['color_by'] = st.selectbox('Color:',
                                            ctypes['cat_columns'],
                                            label_visibility='collapsed',
                                            placeholder='Color by',
                                            index=None)
            opts['size_by'] = st.selectbox('Size:',
                                        ctypes['all_columns'],
                                            label_visibility='collapsed',
                                            placeholder='Size by',
                                        index=None)
            opts['shape_by'] = st.selectbox('Shape:',
                                            ctypes['all_columns'],
                                            label_visibility='collapsed',
                                            placeholder='Shape by',
                                            index=None)
            opts['column_facet'] = st.selectbox('Column Facet:',
                                                ctypes['cat_columns'],
                                                label_visibility='collapsed',
                                                placeholder='Column facet',
                                                index=None)
            opts['row_facet'] = st.selectbox('Row Facet:',
                                            ctypes['cat_columns'],
                                            label_visibility='collapsed',
                                            placeholder='Row facet',
                                            index=None)
            opts['add_tooltips'] = st.multiselect('Tooltips:',
                                                ctypes['all_columns'],
                                                label_visibility='collapsed',
                                                placeholder='Add tooltips',
                                                default=names_list)

    opts_type={'mark':list(mark_props), 
               'scale':list(scale_props)}
    return (opts, opts_type)
