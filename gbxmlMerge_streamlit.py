## -*- coding: utf-8 -*-
"""
Spyder Editor

Merges two gbXML files exported from Revit. First gbXML based on Revit masses does not include openings.
Second gbXML based on Revit spaces includes openings. Openings within variable 'dist' parameter are
take from gbXML based on Revit spaces and merged with gbXML based on Revit masses.
"""

# xgbxml on PyPi: https://pypi.org/project/xgbxml/
# Topologic on PyPi: https://pypi.org/project/topologicpy/

from lxml import etree
from xgbxml import get_parser
from copy import copy
import streamlit as st
import streamlit.components.v1 as components
from topologicpy import topologic

#print(dir(topologic)) # troubleshooting of topologic module path(s)


# tab1 front matter
title_body = '[gbxmlMerge](https://github.com/jpstaub/Revit-Dynamo-MEP/blob/master/AutomatedBuildingEnergyModel/Ripcord_Revit-gbXML_Workflow_22-09-15.pdf)'
sub_body = 'by [Ripcord Engineering](https://www.ripcordengineering.com)'


def uploader_fpa():
    print("Uploaded gbxml without openings.")
    
def uploader_fpb():
    print("Uploaded gbxml with openings.")
    

# define: file variables with streamlit
# fpa = st.file_uploader("gbxml without openings", type = 'xml', on_change = uploader_cb())
fpa_label = 'gbxml without openings'
fpa = st.sidebar.file_uploader(fpa_label, type = 'xml', on_change = uploader_fpa())
if fpa is None:
    st.stop()
    
# fpb = st.file_uploader("gbxml with openings", type = 'xml', on_change = uploader_cb())
fpb_label = 'gbxml with openings'
fpb = st.sidebar.file_uploader(fpb_label, type = 'xml', on_change = uploader_fpb())
if fpb is None:
    st.stop()
    
fpo = 'merged.xml'

# set: distance tolerance of opening from surface in gbXML length units (typically the thickness of the roof or wall)
# dist = 1.1
dist_statement = 'tolerance of opening from surface in gbXML length units'
dist_help = 'typically greater than the thickness of the roof'
dist_warning = 'Please input an opening tolerance value greater than 0.'
dist = st.sidebar.number_input(dist_statement, min_value=0.0, max_value=2.0, value=0.0, help=dist_help)
if dist==0:
    st.warning(dist_warning)
    st.stop()
    

# use: xgbxml to generate a lxml parser / read: gbXML version from input file
tree_parser=etree.parse(fpa)
gbxml=tree_parser.getroot()
parser=get_parser(version=gbxml.attrib['version'])
# parser=get_parser(version='0.37')


# open: the file using the lxml parser
tree_A = etree.parse(fpa,parser)
gbxml_A = tree_A.getroot()


# open: the file using the lxml parser
tree_B = etree.parse(fpb,parser)
gbxml_B = tree_B.getroot()


# make: a copy of gbxml_A which is named gbxml_C
gbxml_C = copy(gbxml_A)
etree_C = etree.ElementTree(gbxml_C)


# define: topologicpy faceByVertices (Wassim Jabi) - 27MAY
def faceByVertices(vertices):
    vertices
    edges = []
    for i in range(len(vertices)-1):
        v1 = vertices[i]
        v2 = vertices[i+1]
        try:
            e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
            if e:
                edges.append(e)
        except:
            continue

    v1 = vertices[-1]
    v2 = vertices[0]
    # print("V1:", v1.X(), v1.Y(), v1.Z())
    # print("V2:", v2.X(), v2.Y(), v2.Z())
    try:
        e = topologic.Edge.ByStartVertexEndVertex(v1, v2)
        if e:
            edges.append(e)
    except:
        print("Edge creation failed!")
        pass
    # print("I managed to create",len(edges),"edges")
    if len(edges) >= 3:
        c = topologic.Cluster.ByTopologies(edges, False)
        w = c.SelfMerge()
        if w.Type() == topologic.Wire.Type() and w.IsClosed():
            f = topologic.Face.ByExternalBoundary(w)
        else:
            raise Exception("Error: Could not get a valid wire")
    else:
        raise Exception("Error: could not get a valid number of edges")
    return f


# get: gbxml_B openings (ops)    
# make: gbxml_B opening centroids (ocs)
ops = []
ocs = []
for op in gbxml_B.Campus.Surfaces.Openings:
    ops.append(op)
    o = []
    for c in op.PlanarGeometry.get_coordinates():
        o.append(topologic.Vertex.ByCoordinates(c[0],c[1],c[2]))
    ocs.append(topologic.Topology.Centroid(faceByVertices(o)))


# get: gbxml_C exterior surfaces (exsu)
# make: gbxml_C surface faces (sfs)
exsu = []
sfs = []
for su in gbxml_C.Campus.Surfaces:
    if su.get_attribute('surfaceType') in ['ExteriorWall', 'Roof']:
        exsu.append(su)
        s = []
        for c in su.PlanarGeometry.get_coordinates():
            s.append(topologic.Vertex.ByCoordinates(c[0],c[1],c[2]))
        sfs.append(faceByVertices(s))


# test: gbxml_B opening centroid IsInside(face,point,tolerance) of gbxml_C surface face (vin)
vin = []
for oc in ocs:
    r = []
    for sf in sfs:
        r.append(topologic.FaceUtility.IsInside(sf,oc,dist))
    vin.append(r)
    
   
# # qa: count number of true responses per opening vertex
# count = []
# for v in vin:
#     count.append(v.count(True))
    
    
# get: indices of gbxml_C surfaces with gbxml_B opening centroid isinside (sfoc)
sfoc = []
for v in vin:
    if True in v:
        sfoc.append(v.index(True))
    else:
        sfoc.append(False)       
           

# insert: gbxml_B opening into gbxml_C surface object if opening within variable 'dist' parameter
i = 0
for sf in sfoc:
    if sf==False:
        i+=1
    else:
        try:
            exsu[sf].insert(3, exsu[sf].copy_opening(ops[i],tolerance=dist)) # copy_opening is xgbxml method
            i+=1
        except ValueError:
            opening_error = ('Caught ValueError. Check opening: ' + ops[i].Name.text + '.')
            with st.sidebar.expander:
                st.error(opening_error)
            i+=1
        except Exception:
            opening_error = ('Caught Exception. Check opening: ' + ops[i].Name.text + '.')
            with st.sidebar.expander:
                st.error(opening_error)
            i+=1


# render: the gbXML etree
render_body = 'Please select the gbXML to view.'
render_options = ('gbXML without openings', 'gbXML with openings', 'merged gbXML')       
render = st.radio(render_body, render_options, index=2)

if render == 'gbXML without openings':
    ax = gbxml_A.Campus.render()
    ax.figure.set_size_inches(8, 8)
    ax.set_title('gbXML without openings')
elif render == 'gbXML with openings':
    ax = gbxml_B.Campus.render()
    ax.figure.set_size_inches(8, 8)
    ax.set_title('gbXML with openings')
else:
    ax = gbxml_C.Campus.render()
    ax.figure.set_size_inches(8, 8)
    ax.set_title('merged gbXML')
st.set_option('deprecation.showPyplotGlobalUse', False) #hides deprecation warning on webpage
st.pyplot()


# download: the gbXML_C etree to a local file
with st.sidebar:
    download_label = 'Download Merged gbXML'
    st.download_button(download_label, etree.tostring(etree_C, pretty_print=True), file_name = fpo)


# embed: ladybug tools gbxml viewer
iframe_address = 'https://www.ladybug.tools/spider/gbxml-viewer/r14/gv-cor-core/gv-cor.html'
components.iframe(iframe_address, width=900, height=600)
