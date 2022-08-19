# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# Todo: implement Topologic (https://topologic.app/user_doc :: Topologic:Utilities:FaceUtility:IsInside) to detect containment of opening vertex in surface faces.
# Topologic on PyPi: https://test.pypi.org/project/topologicpy/


from lxml import etree
from xgbxml import get_parser
from copy import copy
from topologicpy import topologic as tp # from 'foo' import 'bar': this syntax required for topologicpy functionality
import streamlit as st
import streamlit.components.v1 as components


def uploader_cb():
    print("Dummy callback for file uploader")

# define: file variables with streamlit
fpa = st.file_uploader("gbxml without openings", type = 'xml', on_change = uploader_cb())
if fpa is None:
    st.stop()
    
fpb = st.file_uploader("gbxml with openings", type = 'xml', on_change = uploader_cb())
if fpb is None:
    st.stop()
    
fpo = 'merged.xml'

# use: xgbxml to generate a lxml parser / read: gxXML version 0.37
parser=get_parser(version='0.37')

# # render: the gbXML etree
# ax = gbxml_A.Campus.render()
# ax.figure.set_size_inches(8, 8)
# ax.set_title('gbXML A_Geometry.xml')
# st.set_option('deprecation.showPyplotGlobalUse', False) #hides deprecation warning on webpage

# st.pyplot()

# open: the file using the lxml parser
tree_A = etree.parse(fpa,parser)
gbxml_A = tree_A.getroot()


# open: the file using the lxml parser
tree_B = etree.parse(fpb,parser)
gbxml_B = tree_B.getroot()


# # render: the gbXML etree
# ax = gbxml_B.Campus.render()
# ax.figure.set_size_inches(8, 8)
# ax.set_title('gbXML B_Openings.xml')
# st.set_option('deprecation.showPyplotGlobalUse', False) #hides deprecation warning on webpage

# st.pyplot()


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
            e = tp.Edge.ByStartVertexEndVertex(v1, v2)
            if e:
                edges.append(e)
        except:
            continue

    v1 = vertices[-1]
    v2 = vertices[0]
    # print("V1:", v1.X(), v1.Y(), v1.Z())
    # print("V2:", v2.X(), v2.Y(), v2.Z())
    try:
        e = tp.Edge.ByStartVertexEndVertex(v1, v2)
        if e:
            edges.append(e)
    except:
        print("Edge creation failed!")
        pass
    # print("I managed to create",len(edges),"edges")
    if len(edges) >= 3:
        c = tp.Cluster.ByTopologies(edges, False)
        w = c.SelfMerge()
        if w.Type() == tp.Wire.Type() and w.IsClosed():
            f = tp.Face.ByExternalBoundary(w)
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
        o.append(tp.Vertex.ByCoordinates(c[0],c[1],c[2]))
    ocs.append(tp.Topology.Centroid(faceByVertices(o)))


# get: gbxml_C exterior surfaces (exsu)
# make: gbxml_C surface faces (sfs)
exsu = []
sfs = []
for su in gbxml_C.Campus.Surfaces:
    if su.get_attribute('surfaceType') in ['ExteriorWall', 'Roof']:
        exsu.append(su)
        s = []
        for c in su.PlanarGeometry.get_coordinates():
            s.append(tp.Vertex.ByCoordinates(c[0],c[1],c[2]))
        sfs.append(faceByVertices(s))


# test: gbxml_B opening centroid IsInside(face,point,tolerance) of gbxml_C surface face (vin)
vin = []
for oc in ocs:
    r = []
    for sf in sfs:
        r.append(tp.FaceUtility.IsInside(sf,oc,0.01))
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
        
    
# insert: gbxml_B opening into gbxml_C surface object
i = 0
for sf in sfoc:
    if sf==False:
        i+=1
    else:    
        exsu[sf].insert(3, ops[i])
        i+=1
      

# render: the gbXML etree
ax = gbxml_C.Campus.render()
ax.figure.set_size_inches(8, 8)
ax.set_title('Merged gbXML')
st.set_option('deprecation.showPyplotGlobalUse', False) #hides deprecation warning on webpage

st.pyplot()


# download: the gbXML_C etree to a local file
st.download_button("Download Merged gbXML", etree.tostring(etree_C, pretty_print=True), file_name = fpo)

# embed streamlit docs in a streamlit app
components.iframe("https://www.ladybug.tools/spider/gbxml-viewer/r14/gv-cor-core/gv-cor.html", width=900, height=600)
