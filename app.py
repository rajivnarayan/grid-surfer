import streamlit as st
from pathlib import Path
from src.ui.gs_body import render_body

st.set_page_config(
    page_title="Grid Surfer",
    page_icon=":widgets:",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Report a bug': "https://github.com/rajivnarayan/grid-surfer/",
        'About': "Grid Surfer - Interactively explore tabular datasets"
    })

# Custom CSS styling for widgets
st.markdown("""
<style>
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
        font-size: 14pt;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;        
    }
    .stTabs [data-baseweb="tab"] {
        height: 24px;
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
""", unsafe_allow_html=True)

def gs_sidebar():
    with st.sidebar:
        st.header('Grid Surfer', divider = 'grey')
        h_data_loader = st.empty()
        st.divider()
        h_options = st.empty()
    return h_data_loader, h_options

def gs_data_loader(h):
    with h:
        data_file = st.file_uploader(":blue[Choose a delimited text file]", 
                                    type=["csv", "txt"],
                                    label_visibility='visible')
    return data_file

# def gs_body():
#     pages = {
#         "Grid Surfer": [
#                 st.Page("pages/page_01.py", 
#                 title = 'Analyze Tabular Data',
#                 icon = ':material/analytics:')
#         ]        
#     }
#     pg = st.navigation(pages)
#     pg.run()
#     return None

def main():

    h_data_loader, h_options = gs_sidebar()
    data_file = gs_data_loader(h_data_loader)
    render_body(data_file, h_options)

if __name__ == "__main__":
    main()