import os
import sys
import xml.etree.ElementTree as ET

out_extention = '.rou.xml'
node_extention = '.nod.xml'
edge_extention = '.edg.xml'
dead_end_nodes = []
startingEdges = []
endingEdges = []
departPos = 'base'
flow_id = 'flow_'
flow_type = 'CAR'
spawn_prob = 0.02
xml_routes_string = '<?xml version="1.0" encoding="UTF-8"?>\n<routes>\n</routes>'
FILENAME = 'grid/grid'

DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.basename(DIR)
FILE = os.path.splitext(sys.argv[0])[0]

node_data = ET.parse(os.path.join(DIR, FILENAME + node_extention)).getroot()
for node in node_data:
    if node.tag == 'node' and node.attrib.get('type') == 'dead_end':
        dead_end_nodes.append(node.attrib.get('id'))

print(dead_end_nodes)

edge_data = ET.parse(os.path.join(DIR, FILENAME + edge_extention)).getroot()
for edge in edge_data:
    if edge.tag == 'edge':
        if edge.attrib.get('from') in dead_end_nodes:
            startingEdges.append(edge.attrib.get('id'))
        elif edge.attrib.get('to') in dead_end_nodes:
            endingEdges.append(edge.attrib.get('id'))

print(startingEdges, endingEdges)

routes_file = open(os.path.join(DIR, FILE + out_extention), 'w')
routes_file.write(xml_routes_string)
routes_file.close()
routes_file = ET.parse(os.path.join(DIR, FILE + out_extention))
routes_data = routes_file.getroot()
index = 0
for start in startingEdges:
    for end in endingEdges:
        ET.SubElement(routes_data, 'flow', attrib={'id': flow_id + str(index), 'type': flow_type,
                                                   'from': start, 'to': end, 'probability': str(spawn_prob), 'departPos': departPos})
        index += 1

routes_file.write(os.path.join(DIR, FILE + out_extention))
