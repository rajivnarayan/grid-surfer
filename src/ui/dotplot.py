import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from src.ui import gsutils as gsu

"""
Functions to create dot plots
"""

def make_dot_plot(grid_return):
    """Generate dotplot"""
    ctypes = gsu.get_df_column_types(grid_return.data)
    h_options, h_main=st.columns([0.20, 0.80], gap='medium')
    # settings and options
    with h_options:
        opts, opts_type = get_dot_options(ctypes)
    
    # main viz        
    with h_main:
        mark_kwds={k: opts.get(k, alt.Undefined) for k in opts_type['mark']}
        kwds={'x' : alt.X(opts['x_axis'],
                          scale = gsu.get_axis_scale(opts['x_scale']),
                          title = opts['x_title'] if opts['x_title'] else opts['x_axis']),
                'y': alt.Y(opts['y_axis'],
                           title = opts['y_title'] if opts['y_title'] else opts['y_axis'])
                }
        facet_kwds = {}
        tooltips=opts.get('add_tooltips', [])
        select_fields=[]
        facet_header=alt.Header(titleFontSize=16, 
                                labelFontSize=16, 
                                labelAnchor='middle', 
                                labelColor='#808080', 
                                labelFontWeight='normal',
                                titleFontWeight='bold',
                                titleAnchor='middle', 
                                labelAlign='center')
        
        if opts['column_facet'] is not None:
            facet_kwds['column'] = alt.Facet(opts['column_facet'], header=facet_header)
            #tooltips.extend([opts['column']])

        if opts['row_facet'] is not None:
            facet_kwds['row']=alt.Facet(opts['row_facet'], header=facet_header)
            #tooltips.extend([opts['row']])

        if opts['color_by'] is not None:
            kwds['color']={"field": opts['color_by'], "scale": {"scheme": "tableau10"}}
            tooltips.extend([opts['color_by']])
            select_fields.extend([opts['color_by']])

        tooltips.extend([
                alt.Tooltip(opts['x_axis']),
                alt.Tooltip(opts['y_axis'], format="0.2f")])

        kwds['tooltip']=tooltips
        
        if select_fields:
            selection=alt.selection_multi(fields=select_fields)
        else:
            selection=alt.selection_multi()
        
        chart = (alt.Chart(data=grid_return.data,
                           mark = {**mark_kwds})
                 .encode(**kwds)
                 .properties(width = opts['width'],
                             height = opts['height'])
                 )

        if opts['agg_dispersion'] is not None:
            agg_kwds = kwds
            agg_kwds['tooltip'] = alt.Undefined            
            h_dispersion = (alt.Chart()
                            .mark_errorbar(extent = opts['agg_dispersion'],
                                           thickness = 4,
                                           opacity = 0.8,
                                           color = opts['default_agg_color'])
                            .encode(**kwds))
            chart = alt.layer(chart, h_dispersion, data=grid_return.data)

        if opts['agg_average'] is not None:
            agg_kwds = kwds
            agg_kwds['x'] = alt.X(opts['x_axis'],
                                  aggregate = opts['agg_average'],
                                  title = '')
            agg_kwds['tooltip'] = alt.Undefined
            h_avg = (alt.Chart()
                     .mark_point(filled = True,
                                strokeWidth = 2,
                                size = 150,
                                opacity = 0.8,
                                color = opts['default_agg_color'])
                     .encode(**agg_kwds))
            chart = alt.layer(chart, h_avg, data = grid_return.data)

        if facet_kwds:
            chart = chart.facet(**facet_kwds)

        chart = (chart
                 .configure_axis(
                     labelFontSize = 16,
                     titleFontSize = 16,
                     titleFontWeight = 'bold',
                     labelLimit = 200)
                 .configure_view(
                    stroke = '#808080',
                    strokeWidth = 1.5)
                    )
        st.altair_chart(chart, use_container_width=False)
        
    return chart


def get_dot_options(ctypes):
    """Get parameters and options"""
    names_tocheck = ['gene_name', 'gene_symbol', 'name', 'treatment', 'target_name']
    x_to_check = ['x', 'cc_q75']
    y_to_check = ['y', 'ss_ngene']
    _, names_list = gsu.pick_if_present(ctypes['cat_columns'], names_tocheck)
    default_tooltip = next(iter(names_list or []), None)                
    default_x, _ = gsu.pick_if_present(ctypes['num_columns'], x_to_check)
    default_y, _ = gsu.pick_if_present(ctypes['cat_columns'], y_to_check)
    opts={}
    opts_type = {'mark': ['type', 'size', 'opacity', 'strokeWidth', 'color', 'filled']}
    with st.popover('Settings :material/tune:'):
        opts['x_scale'] = st.selectbox('X-Axis Scale:', 
                                                options=['linear', 'log2', 'log10'], 
                                                index=0)
        opts['y_scale'] = st.selectbox('Y-Axis Scale:', 
                                                options=['linear', 'log2', 'log10'], 
                                                index=0)
        opts['width'] = st.slider('Plot Width:', min_value = 50, max_value=1000, step = 25, value = 400)
        opts['height'] = st.slider('Plot Height:', min_value = 50, max_value=1000, step = 25, value = 200)

        opts['x_title'] = st.text_input('X-Axis Title:', None)
        opts['y_title'] = st.text_input('Y-Axis Title:', None)
        opts['type'] = st.selectbox('Marker:', ['point', 'tick'], index = 0)
        opts['size'] = st.slider('Marker Size:', 
                                    min_value = 5, max_value = 500, 
                                    step = 5, value = 15)
        opts['strokeWidth'] = st.slider('Stroke Width:', 
                                            min_value = 0.0, max_value = 10.0, step = 0.5, value = 1.0)
        opts['opacity'] = st.slider('Opacity:', 
                                        min_value = 0.0, max_value  = 1.0, step = 0.1, value = 0.8)        
        opts['filled'] = st.checkbox('Fill Markers:', value = False)
        opts['color'] = st.color_picker('Marker Color:', value='#7570b2')
        opts['default_agg_color'] = st.color_picker('Aggregate Color:', value='#d95f02')

    opts['x_axis'] = st.selectbox('X-Axis:', ctypes['num_columns'], index=default_x)
    opts['y_axis'] = st.selectbox('Y-Axis:', ctypes['cat_columns'], index=default_y)
    opts['color_by'] = st.selectbox('Color:', ctypes['cat_columns'], index=None)
    opts['column_facet'] = st.selectbox('Column Facet:', ctypes['cat_columns'], index=None)
    opts['row_facet'] = st.selectbox('Row Facet:', ctypes['cat_columns'], index=None)
    opts['agg_average'] = st.selectbox('Show Averages:', ['median', 'mean'], index=None)
    opts['agg_dispersion'] = st.selectbox('Show Dispersion:', ['iqr', 'stdev', 'stderr', 'ci'], index=None)

    return (opts, opts_type)
