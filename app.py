import streamlit as st
import pandas as pd
from pathlib import Path
from vega_datasets import local_data
from collections import namedtuple
from src.ui.gs_body import render_body
from src.ui import gs_utils as gsu
from src.ui import gs_state

st.set_page_config(
    page_title="Grid Surfer",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://github.com/rajivnarayan/grid-surfer/',
        'Report a bug': "https://github.com/rajivnarayan/grid-surfer/",
        'About': "Grid Surfer v0.1 - Explore tabular datasets"
    })

# setup custom styles
gsu.init_custom_style()

# initialize session state
gs_state.init_state()

def gs_sidebar():
    with st.sidebar:
        st.logo('assets/logo-main.png', size='medium', icon_image = 'assets/logo-main.png', link='https://github.com/rajivnarayan/grid-surfer/')
        st.get_option('theme.base')
        #st.image('assets/logo-main_400x100.png', use_container_width=True)
        input_select = st.pills("Load Data",
                            ["File", "Demos"],
                            default = 'File',
                            label_visibility = 'collapsed')        
        h_data_loader = st.container()
        st.divider()
        h_data_options = st.container()

        with h_data_loader:
            if input_select == 'File':
                selected_ds = st.file_uploader("**Explore your data**", 
                                    type=["csv", "txt", "tsv", "json"],
                                    label_visibility='visible')
                if selected_ds:
                     st.session_state['data_file'] = selected_ds
            else:
                ds_list = list(st.session_state['examples'].keys())
                demo_choice = st.session_state.get('demo_choice')
                if demo_choice is not None:
                    ds_index = ds_list.index(demo_choice)
                else:
                    ds_index = None

                selected_ds = st.radio('Select Dataset', ds_list,
                                       label_visibility='hidden',
                                       index=ds_index,
                                       key = 'demo_choice')
                if selected_ds:
                    Dataset = namedtuple('Dataset', 
                                         'name source type file')       
                    st.session_state['data_file'] = Dataset(selected_ds, 
                                        **st.session_state.examples[selected_ds])
            
    return h_data_loader, h_data_options


def main():

    h_data_loader, h_data_options = gs_sidebar()    
    render_body(h_data_options)

if __name__ == "__main__":
    main()