import altair as alt
import numpy as np
import pandas as pd
from decimal import Decimal

def get_df_column_types(df: pd.DataFrame) -> dict:
    is_numeric=df.dtypes!='object'
    column_types={}
    column_types['all_columns']=df.columns
    column_types['num_columns']=df.columns[is_numeric].tolist()
    column_types['cat_columns']=df.columns[~is_numeric].tolist()
    return column_types

def pick_if_present(reference: list, to_check: list, default: int=0) -> tuple[int, list]:
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
    This function takes a scale string as input and returns an Altair Scale object based on the provided scale type.
    
    Parameters:
    scale_str (str): A string representing the scale type. It can be one of the following:
    - 'linear': Linear scale
    - 'log10': Logarithmic scale with base 10
    - 'log2': Logarithmic scale with base 2
    
    Returns:
    alt.Scale: An Altair Scale object configured according to the specified scale type.
    """
    scale_lut={'linear': {'type':'linear'},
    'log10' : {'type':'log', 'base':10},
    'log2' : {'type':'log', 'base':2}
    }
    return alt.Scale(**scale_lut[scale_str])


def format_float(f):
    d = Decimal(str(f));
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
