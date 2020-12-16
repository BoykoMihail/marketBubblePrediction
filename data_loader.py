#!/usr/bin/env python

import pkg_resources
import pandas as pd




def sp500_2017():
    stream = pkg_resources.resource_stream(__name__, 'data/sp500_2017.csv')
    return pd.read_csv(stream, encoding='latin-1')
    

def sp500_2000():
    stream = pkg_resources.resource_stream(__name__, 'data/sp500_2000.csv')
    return pd.read_csv(stream, encoding='latin-1')
    
def sp500_2019():
    stream = pkg_resources.resource_stream(__name__, 'data/sp500_2019.csv')
    return pd.read_csv(stream, encoding='latin-1')
    
def sp500_1990():
    stream = pkg_resources.resource_stream(__name__, 'data/sp500_1990.csv')
    return pd.read_csv(stream, encoding='latin-1')

def sp500_1970():
    stream = pkg_resources.resource_stream(__name__, 'data/sp500_1970.csv')
    return pd.read_csv(stream, encoding='latin-1')

def sp500_2007():
    stream = pkg_resources.resource_stream(__name__, 'data/sp500_2007.csv')
    return pd.read_csv(stream, encoding='latin-1')

def sp500_1926():
    stream = pkg_resources.resource_stream(__name__, 'data/sp500_1926.csv')
    return pd.read_csv(stream, encoding='latin-1')
    
def illumina_2001():
    stream = pkg_resources.resource_stream(__name__, 'data/ILMN_2001.csv')
    return pd.read_csv(stream, encoding='latin-1')
    
def illumina_2017():
    stream = pkg_resources.resource_stream(__name__, 'data/ILMN_2017.csv')
    return pd.read_csv(stream, encoding='latin-1')
