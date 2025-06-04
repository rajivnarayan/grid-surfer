# Descriptive statistics on columns
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid
from src.ui import gs_utils as gsu


def get_description(df: pd.DataFrame, 
                    group_var: str=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    ctypes = gsu.get_df_column_types(df)
    if group_var is not None:
        df_desc_num = (df
                        .loc[:, ctypes['num_columns'] + [group_var]]
                        .groupby(group_var)
                        .describe()
                        .rename_axis(columns = ['field', 'metric'])
                        .stack(0, future_stack=True)
                        .sort_values(['field', group_var])
                        .style
                        .format(precision=2)
                        )
    else:
        df_desc_num = (df
                       .loc[:, ctypes['num_columns']]
                       .describe()
                       .T
                       .rename_axis('field')
                       .style.format(precision=2)                           
                       )
    df_desc_cat = (df
                .loc[:, ctypes['cat_columns']]
                .describe()
                .T
                .rename_axis('field')
                .style.format(precision=2)
        )
    return (df_desc_num, df_desc_cat)


def show_description(grid: AgGrid):
    ctypes = gsu.get_df_column_types(grid.data)
    h_main = st.container()

    tab_num, tab_cat = st.tabs(['Numeric', 
                                'Categorical'])
    with h_main:
        get_describe_options(ctypes)
        group_by = st.session_state['describe_group_by']

        df_desc_num, df_desc_cat = get_description(grid.data, 
                                                   group_var=group_by)
        tab_num.dataframe(df_desc_num, use_container_width=True)
        tab_cat.dataframe(df_desc_cat, use_container_width=True)
        

def get_describe_options(ctypes, widget_id='describe_'):
    """Get parameters and options"""
    with st.sidebar:
        with st.container(border=True):
            st.markdown('**Describe**')
            st.selectbox('Group by:',
                        ctypes['cat_columns'],
                        index=None,
                        label_visibility='visible',
                        help = 'Categorical variable for calculating grouped statistics of numeric fields',
                        key=widget_id + 'group_by')
