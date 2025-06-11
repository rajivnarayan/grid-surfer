import streamlit as st
from collections import namedtuple
from src.ui.gs_body import render_body
from src.ui import gs_utils as gsu
from src.ui import gs_state

# app version
app_version = gsu.get_version()

st.set_page_config(
    page_title="Grid Surfer",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://github.com/rajivnarayan/grid-surfer/',
        'Report a bug': "https://github.com/rajivnarayan/grid-surfer/",
        'About': f"""Grid Surfer - Explore tabular datasets    
                     Version: `{app_version}`"""
    })

# setup custom styles
gsu.init_custom_style()

# initialize session state
gs_state.init_state()



@st.dialog('Grid Surfer')
def show_help():
    st.markdown(f'''                
                &copy; Rajiv Narayan, 2025    
                Version: `{app_version}`    

                GridSurfer is a web application for exploring tabular datasets.

                **Features:**
                - Load tabular data in CSV, TSV or JSON format
                - Get descriptive statistics on numeric and categorical fields
                - Visualize univariate and bi-variate distributions via       
                histograms, dot and scatter plots
                - View the data in a filterable and sortable grid
                - Apply grouping and faceting to charts                
                ''')
    st.link_button('View code and report bugs',
                   type='primary',
                   url = 'https://github.com/rajivnarayan/grid-surfer/',
                   use_container_width=True)
    
def gs_sidebar():
    with st.sidebar:
        st.logo('assets/logo-main.png', 
                size='medium', 
                icon_image = 'assets/logo-main.png')
        st.button('About', 
                  icon = ':material/info:',
                  use_container_width=True,
                  type = 'secondary',
                  on_click=show_help)


@st.dialog("Load data")
def data_loader():
    input_select = st.session_state['data_select']
    if input_select == 'File':
        selected_ds = st.file_uploader("**Explore your data**", 
                        type=["csv", "txt", "tsv", "json"],
                        label_visibility='visible')
        if selected_ds:
            st.session_state['data_file'] = selected_ds
            st.rerun()

    else:   
        ds_list = list(st.session_state['examples'].keys())
        demo_choice = st.session_state.get('demo_choice')
        if demo_choice is not None:
            ds_index = ds_list.index(demo_choice)
        else:
            ds_index = None

        selected_ds = st.radio('**Example Datasets**', ds_list,
                                label_visibility='visible',
                                index=ds_index,
                                key = 'demo_choice')
        if selected_ds:
            Dataset = namedtuple('Dataset', 
                                    'name source type file')
            st.session_state['data_file'] = Dataset(selected_ds, 
                                **st.session_state.examples[selected_ds])            
            st.rerun()


def load_data():
    option_map = {'File': ":material/folder_open: File", 
                  'Demo': ":material/auto_stories: Examples"}
    col_load, col_status = st.columns([0.8, 0.2])
    with col_load:
        st.segmented_control(
                        "Load Data",                                         
                        options = option_map.keys(),
                        format_func=lambda option: option_map[option],
                        default = None,
                        key = 'data_select',
                        on_change=data_loader,
                        label_visibility = 'collapsed') 
    st.session_state['status_bar'] = col_status

def main():
    gs_sidebar()        
    load_data()
    h_filter = st.expander('Filter Data',
                           expanded=False,
                           icon=':material/filter_alt:')
    render_body(h_filter)

if __name__ == "__main__":
    main()