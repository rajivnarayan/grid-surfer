import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import subprocess
from decimal import Decimal

def init_custom_style():
    """Custom CSS styling for widgets
    """
    st.markdown(
    """<style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@100&display=swap'); 

        html, body, [class*="css"] {
            font-family: 'Roboto', sans-serif; 
            font-size: 16px;
            font-weight:400;
            color: #091747;
        }
        [alt=Logo] {
            display: block;
            margin-left:64px;
            margin-right:auto;
        }
        /* Multiselect format*/
        .stMultiSelect > label {
            font-size: 1.0rem; 
            font-weight: bold; 
        } 
        .stMultiSelect [data-baseweb=select] span{
            height: px;   
            padding-top: 0px;    
            font-size: 0.8rem;
        }
    </style>
    """, unsafe_allow_html=True)    


def get_df_column_types(df: pd.DataFrame) -> dict:
    is_numeric=df.dtypes!='object'
    column_types={}
    column_types['all_columns']=df.columns
    column_types['num_columns']=df.columns[is_numeric].tolist()
    column_types['cat_columns']=df.columns[~is_numeric].tolist()
    return column_types


def pick_if_present(reference: list,
                    to_check: list,
                    default: int=0) -> tuple[int, list]:
    """
    Check if reference exist in a list

    Parameters:
    reference (list): referemce list of items
    to_check (list): list of items to search in the reference

    Returns:
    pick (int): index of first found item in the reference list
    items_found: (list): list of items found in reference
    
    """    
    items_found = set(reference).intersection(set(to_check))
    default_index = np.clip(default, 0, len(reference))
    pick = reference.index(next(iter(items_found or []),
                                reference[default_index]))
    return pick, items_found


def get_axis_scale(scale_str: str) -> alt.Scale:
    """
    This function takes a scale string as input and returns an Altair Scale 
    object based on the provided scale type.
    
    Parameters:
    scale_str (str): A string representing the scale type. It can be one of the
     following:
    - 'linear': Linear scale
    - 'log10': Logarithmic scale with base 10
    - 'log2': Logarithmic scale with base 2
    
    Returns:
    alt.Scale: An Altair Scale object configured according to the specified 
    scale type.
    """
    scale_lut={'linear': {'type':'linear'},
    'log10' : {'type':'log', 'base':10},
    'log2' : {'type':'log', 'base':2}
    }
    return alt.Scale(**scale_lut[scale_str], zero=False)


def format_float(f):
    d = Decimal(str(f))
    return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()


def transform_nlogp(p: list[float], base:int=10) -> float:
    """
    Calculate negative-log p-values 
    
    Parameters:
    p (list[float]): list of p-values
    base (int): Base of logarithm. Default is 10

    Returns:
    nlogp: list of negative log_base p-values of same length as p     
    """
    
    # to avoid log(0), set zeros to small non-zero values
    min_nz_p = 0.01*np.min(p[p]>0)
    return -np.log(np.clip(p, min_nz_p, 1))/np.log(base)


def set_chart_name(chart: alt.Chart,
                   filename: str) -> alt.Chart:
    # set chart save filename and actions
    chart['usermeta'] = {
        'embedOptions': {
            'downloadFileName': filename,
            'actions': {'export':True,
                        'source':False,
                        'editor':False,
                        'compiled':False}
        }
    }
    return chart


def update_status(s: str):
    """Display string in status bar"""
    st.session_state['status_bar'].code(s, language='python')

@st.cache_data
def get_version()->str:
    """Get version from build-time generated file or fallback to git"""
    try:
        with open('version.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback for development environment
        try:
            return (subprocess
                    .check_output(['git', 'describe', '--always'])
                    .decode('ascii')
                    .strip()
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "latest"