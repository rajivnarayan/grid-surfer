import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from st_aggrid import AgGrid
from src.ui import gs_utils as gsu
from src.ui import gs_state as gss

"""
Functions to create dot plots
"""

def make_dot_plot(grid_return: AgGrid):
    """Generate dotplot"""
    ctypes = gsu.get_df_column_types(grid_return.data)
    # settings and options
    opts, opts_type = get_dot_options(ctypes)
    
    # main viz        
    chart = plot_dot(grid_return.data, opts, opts_type)
    st.altair_chart(chart, use_container_width=False)


def plot_dot(df: pd.DataFrame,
             opts: dict,
             opts_type: dict) -> alt.Chart:
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
    if not opts['show_points']:
        mark_kwds['strokeWidth'] = 0.
        mark_kwds['filled'] = False
    
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
    
    chart = (alt.Chart(data=df,
                        mark = {**mark_kwds})
                .encode(**kwds)
                .properties(width = opts['width'],
                            height = opts['height'])
                )

    if opts['show_boxplot'] is True:
        h_boxplot = (alt.Chart()
                        .mark_boxplot(extent = 1.5,
                                      opacity = opts['opacity'],
                                      outliers={'size':0},
                                      ticks = False)
                        .encode(**kwds))
        chart = alt.layer(chart, h_boxplot, data=df)

    if opts['show_dispersion'] is True:
        agg_kwds = kwds
        agg_kwds['tooltip'] = alt.Undefined        
        h_dispersion = (alt.Chart()
                        .mark_errorbar(extent = opts['agg_dispersion'],
                                        thickness = 4,
                                        opacity = opts['opacity'],
                                        color = opts['default_agg_color'])
                        .encode(**agg_kwds))
        chart = alt.layer(chart, h_dispersion, data=df)

    if opts['show_average'] is True:
        agg_kwds = kwds
        agg_kwds['x'] = alt.X(opts['x_axis'],
                                aggregate = opts['agg_average'],
                                title = '')
        agg_kwds['tooltip'] = alt.Undefined
        h_avg = (alt.Chart()
                    .mark_point(filled = True,
                            strokeWidth = 2,
                            size = 150,
                            opacity = opts['opacity'],
                            color = opts['default_agg_color'])
                    .encode(**agg_kwds))
        chart = alt.layer(chart, h_avg, data = df)

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
    return chart

def get_dot_options(ctypes, widget_id = 'dot_'):
    """Get parameters and options"""
    
    names_tocheck = ['gene_name', 'gene_symbol', 'name', 'treatment', 'target_name']
    x_to_check = ['x', 'cc_q75']
    y_to_check = ['y', 'ss_ngene']
    _, names_list = gsu.pick_if_present(ctypes['cat_columns'], names_tocheck)
    default_tooltip = next(iter(names_list or []), None)                
    default_x, _ = gsu.pick_if_present(ctypes['num_columns'], x_to_check)
    default_y, _ = gsu.pick_if_present(ctypes['cat_columns'], y_to_check)
    opts = {}
    opts_type = {'mark': ['type', 'size', 'opacity', 'strokeWidth', 'color', 'filled']}
    #with st.expander('Parameters:', expanded=True):
    with st.sidebar:
        with st.container(border=True):
            st.write('**Dot Settings**')
            with st.popover('Fine tune', 
                            icon=':material/tune:', 
                            use_container_width=True).container(
                                height=300):
                opts['x_scale'] = st.selectbox('X-Axis Scale:', 
                                                        options=['linear', 'log2', 'log10'], 
                                                        index=0)
                opts['agg_average'] = st.selectbox('Average metric:',
                                            ['mean', 'median'],
                                            index=0)
                opts['agg_dispersion'] = st.selectbox('Variance metric:',
                                                ['stdev', 'iqr', 'stderr', 'ci'], index=0)                     
                opts['width'] = st.slider('Plot Width:', min_value = 50, max_value=1000, step = 25, value = 400)
                opts['height'] = st.slider('Plot Height:', min_value = 50, max_value=1000, step = 25, value = 400)

                opts['x_title'] = st.text_input('X-Axis Title:', None)
                opts['y_title'] = st.text_input('Y-Axis Title:', None)
                opts['type'] = st.selectbox('Marker:', ['point', 'tick'], index = 0)
                opts['size'] = st.slider('Marker Size:', 
                                            min_value = 5, max_value = 500, 
                                            step = 5, value = 15,
                                            key=widget_id + 'size')
                opts['strokeWidth'] = st.slider('Stroke Width:', 
                                                    min_value = 0.0, max_value = 10.0, step = 0.5, value = 1.0,
                                                    key = widget_id+'strokeWidth')
                opts['opacity'] = st.slider('Opacity:', 
                                                min_value = 0.0, max_value  = 1.0, step = 0.1, value = 0.8, key=widget_id+'opacity')        
                opts['filled'] = st.checkbox('Fill Markers:', value = False,
                                            key=widget_id + 'filled')
                opts['color'] = st.color_picker('Marker Color:', value='#7570b2',  key=widget_id + 'color')   
                opts['default_agg_color'] = st.color_picker('Aggregate Color:', value='#d95f02', key=widget_id + 'default_agg_color')

            agg_opts = {'show_points': 'Dot',
                        'show_boxplot': 'Boxplot',
                        'show_average': 'Avg',
                        'show_dispersion': 'Var'}
            show_agg = st.segmented_control('Show', 
                                            label_visibility='collapsed',
                                options=agg_opts.keys(),
                                format_func=lambda option: agg_opts[option],
                                selection_mode='multi',
                                default = ['show_points', 'show_boxplot'])
            st.session_state[widget_id+'show_points'] = 'show_points' in show_agg
            st.session_state[widget_id+'show_average'] = 'show_average' in show_agg
            st.session_state[widget_id+'show_dispersion'] = 'show_dispersion' in show_agg

            opts['show_points'] = 'show_points' in show_agg
            opts['show_boxplot'] = 'show_boxplot' in show_agg
            opts['show_average'] = 'show_average' in show_agg
            opts['show_dispersion'] = 'show_dispersion' in show_agg
            opts['x_axis'] = st.selectbox('X-Axis:',
                                        ctypes['num_columns'],
                                        index=default_x, 
                                        key=widget_id + 'x_axis')
            opts['y_axis'] = st.selectbox('Y-Axis:',
                                        ctypes['cat_columns'],
                                        index=default_y,
                                        key=widget_id + 'y_axis')
            opts['color_by'] = st.selectbox('Color:', 
                                            ctypes['cat_columns'],
                                            label_visibility='collapsed',
                                            placeholder='Color by',
                                            index=None,
                                            key=widget_id + 'color_by')
            opts['column_facet'] = st.selectbox('Column Facet:',
                                                ctypes['cat_columns'],
                                                label_visibility='collapsed',
                                                placeholder='Column facet',
                                                index=None,
                                                key=widget_id + 'column_facet')
            opts['row_facet'] = st.selectbox('Row Facet:',
                                            ctypes['cat_columns'],
                                            label_visibility='collapsed',
                                            placeholder='Row facet',
                                            index=None,
                                            key=widget_id + 'row_facet')
 
    return (opts, opts_type)
