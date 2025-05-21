import streamlit as st
import pandas as pd
from pathlib import Path
from vega_datasets import local_data
from collections import namedtuple
from src.ui.gs_body import render_body

st.set_page_config(
    page_title="Grid Surfer",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Report a bug': "https://github.com/rajivnarayan/grid-surfer/",
        'About': "Grid Surfer - Interactively explore tabular datasets"
    })

# Custom CSS styling for widgets
st.markdown("""
<style>
    /*@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@100&display=swap'); */

    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif; 
        font-size: 16px;
        font-weight:400;
        color: #091747;
    }
    [alt=Logo] {
        display: block;
        margin-left:48px;
        margin-right:auto;
        width: 200px;
    }
    /* Multiselect format*/
    .stMultiSelect > label {
        font-size: 1.2rem; 
        font-weight: bold; 
    } 
    .stMultiSelect [data-baseweb=select] span{
        height: px;   
        padding-top: 0px;    
        font-size: 0.8rem;
    }
    /* Adjust tab appearance */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"]
    p {
        font-size: 12pt;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;        
    }
    .stTabs [data-baseweb="tab"] {
        height: 14px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-left: 10px;
        padding-right: 10px;
        padding-top: 10px;
        padding-bottom: 10px;
        border: 1px solid #808080;
    }
</style>
""", unsafe_allow_html=True)

def gs_sidebar():
    with st.sidebar:
        st.logo('assets/logo-main_400x100.png', size='small', icon_image = 'assets/logo-icon_64x64.png')
        #st.image('assets/logo-main_400x100.png', use_container_width=True)
        input_select = st.pills("Load Data",
                            ["File", "Demo"],
                            default = 'File',
                            label_visibility = 'collapsed')        
        h_data_loader = st.container()
        st.divider()
        h_data_options = st.container()
        data_file = None
        with h_data_loader:
            if input_select == 'File':
                data_file = gs_data_loader(h_data_loader)
            else:
                Dataset = namedtuple('Dataset', 'name source type file')
                examples = {'iris': {'source': 'vega-dataset', 
                                     'type': None,
                                     'file' : None},
                            'barley': {'source': 'vega-dataset',
                                       'type': None,
                                      'file': None},
                            'cars' : {'source': 'vega-dataset',
                                      'type': None,
                                      'file': None},
                            'penguins' : {'source': 'local-dataset',
                                      'type': 'application/json',
                                      'file': 'data/penguins.json'
                                      },
                            }
                ds_list = examples.keys()
                selected_ds = st.radio('Select Dataset', ds_list, label_visibility='hidden', index=None)
                if selected_ds:                    
                    data_file = Dataset(selected_ds, **examples[selected_ds])
            
    return data_file, h_data_loader, h_data_options

def gs_data_loader(h):
    with h:
        data_file = st.file_uploader("**Explore your data**", 
                                    type=["csv", "txt", "tsv", "json"],
                                    label_visibility='visible')
    return data_file

def main():

    data_file, h_data_loader, h_data_options = gs_sidebar()    
    render_body(data_file, h_data_options)

if __name__ == "__main__":
    main()