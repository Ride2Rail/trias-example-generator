from lxml import etree
from collections import Counter
import pandas as pd
import os
import xml.etree.ElementTree as ET


# element mapper class:
class ElementMapper:
    def __init__(self, tag, ns_url, ns_prefix=None):
        self.tag = tag
        self.ns_prefix = ns_prefix
        self.ns_url = ns_url
        self.count_list = []
    # returns count of given element by tag
    def count_xml(self, xml_root):
        return len(xml_root.findall(".//" + self.xml_url_tag()))

    # append an item to the count list, prefered to use with count_xml function
    def count_xml_append(self, xml_root):
        self.count_list.append(self.count_xml(xml_root))

    # returns element with xml tag
    def xml_tag(self):
        return self.ns_prefix + ":" + self.tag

    # returns element with xml tag
    def xml_url_tag(self):
        return "{" + self.ns_url + "}" +  self.tag


# returns dictionary of xml namespaces from a XML file provided via @xml_file parameter
def get_tag_dict(xml_file):
    return dict([node for _, node in ET.iterparse(xml_file, events=['start-ns'])])

# returns ns prefixes
def get_ns_prefix(ns_dict, namespace_url = "http://www.vdv.de/trias"):
    for key, value in ns_dict.items():
        if value == namespace_url:
            return key

# counts modes
def count_modes(xml_root, ns3_namespace):
    return (Counter([a.text for a in xml_root.findall(".//{" + ns3_namespace + "}PtMode")])) + \
    (Counter([a.text for a in xml_root.findall(".//{" + ns3_namespace + "}IndividualMode")]))

# counts real tickets
def count_real_tickets(xml_root, ns3_namespace):
    real_tickets = 0
    for ticket in xml_root.findall(".//{" + ns3_namespace + "}Ticket"):
        if ticket[0].text != 'META' and ticket[0].text[0:5] != 'DUMMY':
            real_tickets += 1
    return real_tickets

# counts the given elements
def count_elements(xml_root, em_obj_list, mode_count_list, ticket_count_list, ns3_namespace):
    # count other elements
    mode_count_list.append(count_modes(xml_root, ns3_namespace))
    ticket_count_list.append(count_real_tickets(xml_root, ns3_namespace))
    # go through object elements
    for em_obj in em_obj_list:
        em_obj.count_xml_append(xml_root)


parser = etree.XMLParser(remove_blank_text=True, recover=True, encoding='utf-8')

xml_dir = "C:/Users/Milan/Desktop/FRI_work/Era/R2R/TRIAS_data/updated_ride2rail_examples/"
xml_files = [xml_dir + x for x in os.listdir(xml_dir)]

filenames = os.listdir(xml_dir)

# get tags from the first file
ns_dictionary = get_tag_dict(xml_files[0])

# get prefix for "http://www.vdv.de/trias" namespace url
ns_3_val = get_ns_prefix(ns_dictionary)
# hacon files used this namespace for TripRequest and TripResponse
ns_3_empty_hacon = get_ns_prefix(ns_dictionary,"http://shift2rail.org/project/")

# create the dict for assembling the XML element counter objects
ns_cnt_dict = {
    "TripRequest": ns_3_empty_hacon,
    "TripResponse": ns_3_empty_hacon,
    "TripResult": ns_3_val,
    'Trip': ns_3_val,
    'TripLeg': ns_3_val,
    'Ticket': ns_3_val,
}

EM_obj_list = [ElementMapper(k,ns_dictionary[v], v) for k,v in ns_cnt_dict.items()]
mode_count_list = []
ticket_count_list = []

ns3 = "http://www.vdv.de/trias"

for file in xml_files:
    xml_file_root = etree.parse(file, parser=parser).getroot()
    count_elements(xml_file_root, EM_obj_list, mode_count_list, ticket_count_list, ns3)

count_el_dict =  {em.tag: em.count_list for em in EM_obj_list}

mydataset = {
    'file': filenames,
}
mydataset.update(count_el_dict)
mydataset.update({'ticket': ticket_count_list})
transport_mode_lists = ['rail', 'metro', 'bus', 'unknown', 'urbanRail', 'air', 'tram', 'walk', 'cycle']
tm_count_dict = {k: [] for k in transport_mode_lists}
for k in tm_count_dict.keys():
    tm_count_dict[k] = [i[k] for i in mode_count_list]

mydataset.update(tm_count_dict)

myvar = pd.DataFrame(mydataset)

myvar.to_csv("xml_examples/trip_hacon_new_stats.csv", sep=";", decimal=",")




