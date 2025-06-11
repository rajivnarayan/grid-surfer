import streamlit as st
import pandas as pd
import altair as alt
from src.ui import gs_utils as gsu

"""
Functions to create histograms
"""

def make_dist_plot(grid_return):
    """Distribution Plot"""
    ctypes = gsu.get_df_column_types(grid_return.data)    
    # settings and options
    opts, opts_types = get_dist_options(ctypes)

    # main viz    
    chart = plot_histogram(grid_return.data, opts, opts_types)
    st.altair_chart(chart, use_container_width=False)

def plot_histogram(df: pd.DataFrame, 
                   opts: dict, 
                   opts_types: dict) -> alt.Chart:
    """Generate histogram"""
    mark_kwds = {k: opts.get(k) for k in opts_types['mark']}    
    kwds = {'x' : alt.X(opts['x_axis'], 
                        bin = alt.Bin(maxbins=opts['bins'])),
            'y': alt.Y('count()')
            }
    tooltips = opts.get('add_tooltips', [])
    select_fields = []
    facet_header = alt.Header(titleFontSize=20, labelFontSize=20, 
                                labelAnchor='middle', 
                                labelColor='#808080', 
                                labelFontWeight='normal',
                                titleFontWeight='bold',
                                titleAnchor='middle', 
                                labelAlign='left')
    
    if opts['facet_by_column'] is not None:
        kwds['column']=alt.Facet(opts['facet_by_column'], header=facet_header)
        #tooltips.extend([opts['column']])

    if opts['facet_by_row'] is not None:
        kwds['row'] = alt.Facet(opts['facet_by_row'], header=facet_header)
        #tooltips.extend([opts['row']])

    if opts['color_by'] is not None:
        kwds['color'] = {"field": opts['color_by'],
                         "scale": {"scheme": "tableau10"}}
        tooltips.extend([opts['color_by']])
        select_fields.extend([opts['color_by']])

    tooltips.extend([
            alt.Tooltip(opts['x_axis'])])
    
    if select_fields:
        selection = alt.selection_multi(fields=select_fields)
    else:
        selection = alt.selection_multi()

    chart=(
        alt.Chart(data=df)
        .mark_bar(**mark_kwds)
        .encode(**kwds)
        .configure_axis(labelFontSize=20, 
                        titleFontSize=20, 
                        titleFontWeight='bold')
        .configure_view(stroke = '#808080',
                        strokeWidth = 1.5)
        .add_selection(selection)
        .transform_filter(selection)
        .properties(width=opts['width'],
                    height=opts['height'])
        )                                                        
    return chart


def get_dist_options(ctypes):
    """Get parameters and options for distribution plots"""
    #names_tocheck=['gene_name', 'gene_symbol', 'name',
    #               'treatment', 'target_name']
    x_to_check=['x', 'cc_q75']
    #names_list = set([e for e in ctypes['cat_columns'] 
    #                  for n in names_tocheck if n in e])  
    
    #default_tooltip = next(iter(names_list or []), None)                
    default_x, x_found = gsu.pick_if_present(ctypes['num_columns'], x_to_check)
    opts = {}
    opts_type = {'mark':['color'], 'scale':['y_scale']}
    #with st.expander('Parameters:', expanded=True):
    with st.sidebar:
        with st.container(border=True):
            st.write('**Histogram Settings**')
            with st.popover('Fine tune',
                            icon=':material/tune:',
                            use_container_width=True).container(
                                height=400):
                # scale properties
                opts['plot_name'] = st.text_input('Plot name:',
                                                   'xy_plot',
                                                     max_chars=50)
                opts['y_scale'] = st.selectbox('Y-Axis Scale:', 
                                            options=['linear', 
                                                     'log2',
                                                     'log10'],
                                                     index=0)
                opts['width'] = st.slider('Plot width:',
                                        min_value=50,
                                        max_value=1000,
                                        step=25,
                                        value=350)
                opts['height'] = st.slider('Plot height:',
                                        min_value=50,
                                        max_value=1000,
                                        step=25,
                                        value=350)
                # mark properties
                opts['color'] = st.color_picker('Color:', value='#4e79a7')
                            
            opts['x_axis'] = st.selectbox('X-Axis:', 
                                        ctypes['num_columns'],
                                        index=default_x)
            opts['bins'] = st.slider('Bins:',
                                    min_value=5,
                                    max_value=200,
                                    step=5,
                                    value=30 )
            opts['color_by'] = st.selectbox('Color:',
                                            ctypes['cat_columns'],
                                            label_visibility='collapsed',
                                            placeholder='Color by',
                                            index=None)
            opts['facet_by_column'] = st.selectbox('Column Facet:',
                                                ctypes['cat_columns'], 
                                                label_visibility='visible',
                                                placeholder='Column facet',  
                                        help='Select field for column facet',
                                                index=None)
            opts['facet_by_row'] = st.selectbox('Row Facet:',
                                                ctypes['cat_columns'],
                                                label_visibility='collapsed',
                                                placeholder='Row facet',
                                                index=None)
    return (opts, opts_type)
