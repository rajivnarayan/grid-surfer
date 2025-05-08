import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder
import pandas as pd
import numpy as np
import requests
import re
from decimal import Decimal
import altair as alt

@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path, sep = None)
    # Add -log10(padj)
    if 'padj' in df and not 'nlogp' in df:            
        df["nlogp"] = -np.log10(df['padj']) + 0.01*np.min(df['padj']>0)
    return df

uploaded_file = st.file_uploader("Choose a delimited text file", type=["csv", "txt"],)

def format_float(f):
    d = Decimal(str(f));
    return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()

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
    scale_lut = {'linear': {'type':'linear'},
    'log10' : {'type':'log', 'base':10},
    'log2' : {'type':'log', 'base':2}
    }
    return alt.Scale(**scale_lut[scale_str])

# Load data
if uploaded_file is not None:
    df = load_data(uploaded_file)
    tab_table, tab_dist, tab_xy, tab_bar = st.tabs(["Table", "Distributions", "XY", "Bar"])
    # adjust tab appearance
    css_tab = '''<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"]
    p {
        font-size: 16pt;
    }
    .stTabs [data-baseweb="tab-list"] {
		gap: 4px;        
    }
    .stTabs [data-baseweb="tab"] {
		height: 32px;
        white-space: pre-wrap;
		background-color: #ffffff;
		border-radius: 4px 4px 0px 0px;
		gap: 2px;
        padding-left: 10px;
        padding-right: 10px;
		padding-top: 10px;
		padding-bottom: 10px;
        border: 1px solid #808080;
    }
    </style>
    '''
    st.markdown(css_tab, unsafe_allow_html=True)

    # Infer basic colDefs from dataframe types
    gb = GridOptionsBuilder.from_dataframe(df)
    # customize gridOptions
    gb.configure_default_column(
        min_column_width = 25,
        alwaysShowHorizontalScroll = True,
        alwaysShowVerticalScroll= False,
        filterable = True,        
        groupable=True,
        editable = False)        
    # Note the sidebar only available with the enterprise version
    # i.e. set enable_enterprise_modules = True in AgGrid() call
    gb.configure_side_bar(filters_panel=True, columns_panel=True)
    # set precision of numeric columns
    for f in df.dtypes[df.dtypes=='float64'].index:
        gb.configure_column(f, type = ["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
    gridOptions = gb.build()
    column_defs = gridOptions['columnDefs']
    # Set all columns to be filterable
    for col in column_defs:
        col['filter'] = True
    
    # Data table
    with tab_table:
        columns_to_show = st.multiselect('Columns to show:', options = df.columns, default = df.columns)
        columns_to_hide = set(df.columns).difference(columns_to_show)

        for col in column_defs:
            if col['headerName'] in columns_to_hide:
                col['hide'] = True

        grid_return = AgGrid(df, 
                    gridOptions=gridOptions,
                    fit_columns_on_grid_load=True,
                    enable_enterprise_modules=False,
                    data_return_mode=DataReturnMode.FILTERED_AND_SORTED)
    # XY plot
    with tab_xy:
        mark_props = {
            'opacity' : {'min_value' : 0.0, 'max_value': 1.0, 'step' : 0.1, 'value' : 0.7},
            'size' : {'min_value' : 0, 'max_value' : 500, 'step' : 10, 'value' : 250},
            'strokeWidth' : {'min_value' : 0.0, 'max_value' : 10.0, 'step' : 0.5, 'value' : 2.0},
            'shape' : {'value': 'circle'},
            'color' : {'value': '#7570b3'},  
            'filled': {'value': True}
        }
        scale_props = {
            'x_scale' : {'options' : ['linear', 'log2', 'log10'], 'index': 0},
            'y_scale' : {'options' : ['linear', 'log2', 'log10'], 'index': 0}
        }


        default_mark_props = dict([(k, v['value']) for k,v in mark_props.items()])     
        default_scale_props = dict([(k, v['options'][v['index']]) for k,v in scale_props.items()])     
        
        is_numeric = df.dtypes!='object'
        all_columns = df.columns
        num_columns = all_columns[is_numeric].tolist()
        cat_columns = all_columns[~is_numeric].tolist()

        col1, col2 = st.columns([0.20, 0.80], gap = 'medium')
        names_tocheck = ['gene_name', 'gene_symbol', 'name', 'treatment', 'target_name']
        x_to_check = ['fc_spikein']
        y_to_check = ['frac_spikein']
        names_list = set([e for e in cat_columns for n in names_tocheck if n in e])        
        x_list = set([e for e in num_columns for n in x_to_check if n in e])
        y_list = set([e for e in num_columns for n in y_to_check if n in e])

        default_tooltip = next(iter(names_list or []), None)                
        default_x = num_columns.index(next(iter(x_list or []), num_columns[0]))
        default_y = num_columns.index(next(iter(y_list or []), num_columns[0]))

        cat_columns.insert(0, None)
        all_columns.insert(0, None)

        with col1:
            with st.popover('Settings :material/tune:'):
                # scale properties
                default_scale_props['x_scale'] = st.selectbox('X-Axis Scale:', **scale_props['x_scale'])
                default_scale_props['y_scale'] = st.selectbox('Y-Axis Scale:', **scale_props['y_scale'])
                # mark properties
                default_mark_props['opacity'] = st.slider('Opacity:', **mark_props['opacity'])
                default_mark_props['size'] = st.slider('Size:', **mark_props['size'])
                default_mark_props['strokeWidth'] = st.slider('Stroke Width:', **mark_props['strokeWidth'])
                default_mark_props['color'] = st.color_picker('Color:', **mark_props['color'])
                default_mark_props['filled'] = st.checkbox('Fill Markers:', **mark_props['filled'])

            x_axis = st.selectbox('X-Axis:', num_columns, index = default_x)
            y_axis = st.selectbox('Y-Axis:', num_columns, index = default_y)
            facet_by_column = st.selectbox('Column Facet:', cat_columns, index = None)
            facet_by_row = st.selectbox('Row Facet:', cat_columns, index = None)
            color_by = st.selectbox('Color:', cat_columns, index = None,
                            label_visibility = 'collapsed', 
                            placeholder = 'Choose color field')
            size_by = st.selectbox('Size:', all_columns, index = None,
                        label_visibility = 'collapsed', 
                        placeholder = 'Choose size field')
            shape_by = st.selectbox('Shape:', all_columns, index = None,       
                        label_visibility = 'collapsed', 
                        placeholder = 'Choose shape field')
                        
            add_tooltips = st.multiselect('Tooltips:', df.columns, default = names_list)
            


        with col2:
            mark_kwds = default_mark_props        
            kwds = {'x' : alt.X(x_axis, 
                        scale = get_axis_scale(default_scale_props['x_scale']),
                        axis = alt.Axis(tickCount = 9, format = '2.4f')), 
                    'y': alt.Y(y_axis, 
                        scale = get_axis_scale(default_scale_props['y_scale']))
                    }

            tooltips = add_tooltips or []
            select_fields = []
            if facet_by_column is not None or facet_by_row is not None:
               kwds['facet'] = alt.Facet(facet_by_column, columns=3,
                                    header = alt.Header(titleFontSize = 20, labelFontSize=20, 
                                    labelAnchor = 'middle', 
                                    labelColor = 'blue', 
                                    labelFontWeight = 'normal',
                                    titleFontWeight = 'bold',
                                    titleAnchor = 'middle', 
                                    labelAlign = 'left'))
            if color_by is not None:
                kwds['color'] = {"field": color_by, "scale": {"scheme": "tableau10"}}
                tooltips.extend([color_by])
                select_fields.extend([color_by])

            if size_by is not None:
                kwds['size'] = size_by
                tooltips.extend([size_by])
                select_fields.extend([size_by])

            if shape_by is not None:                
                kwds['shape'] = shape_by
                tooltips.extend([shape_by])
                select_fields.extend([shape_by])

            tooltips.extend([
                    alt.Tooltip(x_axis, format="0.2f"),
                    alt.Tooltip(y_axis, format="0.2f")])

            kwds['tooltip'] = tooltips
            
            if select_fields:
                selection = alt.selection_multi(fields=select_fields)
            else:
                selection = alt.selection_multi()
            
            chart = (
                alt.Chart(data=grid_return.data)
                .mark_point(**mark_kwds)
                .encode(**kwds)
                .configure_axis(labelFontSize=20, titleFontSize=20, titleFontWeight = 'bold')
                .add_selection(selection)
                .transform_filter(selection)
                )                                                        
            st.altair_chart(chart, use_container_width=False)

    # Distribution plots
    with tab_dist:
        st.empty()

    # Bar plots
    with tab_bar:
        import altair as alt
        import json

        #from vega_datasets import data
        source_url = 'https://raw.githubusercontent.com/altair-viz/vega_datasets/refs/heads/master/vega_datasets/_data/barley.json'
        res = requests.get(source_url)
        if not res.ok:
            raise Exception("Failed to fetch the data")

        source = pd.json_normalize(res.json())
        bars = alt.Chart().mark_bar().encode(
            x='year:O',
            y=alt.Y('mean(yield):Q').title('Mean Yield'),
            color='year:N',
        )

        error_bars = alt.Chart().mark_errorbar(extent='ci').encode(
            x='year:O',
            y='yield:Q'
        )

        chart = alt.layer(bars, error_bars, data=source).facet(
            column='site:N'
        )

        st.altair_chart(chart, use_container_width=True)
