"""Manage session state of UI"""
import json
import streamlit as st

@st.cache_data
def get_demos():
    with open('data/demo_datasets.json', 'rt') as infile:
        demos = json.load(infile)
    return demos

def init_state():
    if 'expand_data_loader' not in st.session_state:
        st.session_state['expand_data_loader'] = True
    if 'opts' not in st.session_state:
        st.session_state['opts'] = {}
    if 'opts_type' not in st.session_state:
        st.session_state['opts_type'] = {}

    if 'examples' not in st.session_state:
        st.session_state['examples'] = get_demos()
    if 'data_file' not in st.session_state:
        st.session_state['data_file'] = None
    if 'data_select' not in st.session_state:
        st.session_state['data_select'] = None


def set_state(id, key, value):
    if id not in st.session_state:
        reset_state(id)
    st.session_state[id] = {key: value}

def reset_state(id):
    st.session_state[id] = {}
