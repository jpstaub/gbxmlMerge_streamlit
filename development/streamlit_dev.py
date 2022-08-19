# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 13:09:34 2022

@author: admin
"""

from copy import copy
from lxml import etree
from xgbxml import get_parser
import streamlit as st
import pandas as pd
import numpy as np

fpa = st.file_uploader("gbxml without openings", type = 'xml')
fpb = st.file_uploader("gbxml with openings", type = 'xml')
fpo = 'merged.xml'

# use: xgbxml to generate a lxml parser / read: gxXML version 0.37
parser=get_parser(version='0.37')

# open: the file using the lxml parser
tree_A = etree.parse(fpa,parser)
gbxml_A = tree_A.getroot()

gbxml_C = copy(gbxml_A)
etree_C = etree.ElementTree(gbxml_C)

st.download_button("Download Merged gbXML", etree.tostring(etree_C, pretty_print=True), file_name = fpo) 
