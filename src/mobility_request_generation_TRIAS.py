import numpy as np

from collections import Counter

from lxml import etree
from copy import deepcopy
from datetime import datetime
import sys
import pandas as pd
from statistics import mean

# function to extract start time
def extract_start_time(trip):
    trip_time = trip.xpath(".//ns3:StartTime/text()", namespaces=NS)
    if len(trip_time) < 1:
        print(trip[0].text, file=sys.stderr)
    return datetime.strptime(trip_time[0], "%Y-%m-%dT%H:%M:%S.%fZ")


# check if the time is within the pre-specified range
def time_within_range(trip_1, trip_2) -> bool:
    trip_1_start = extract_start_time(trip_1)
    trip_2_start = extract_start_time(trip_2)
    return abs((trip_1_start - trip_2_start)).total_seconds() < 3600

# etract list of stops from the data - other way
def extract_stops(trip):
    stop_list = trip.findall(".//ns3:Text", NS)
    stop_text_list = []
    for stop in stop_list:
        parent_el = stop.getparent()
        if parent_el.tag == '{http://www.vdv.de/trias}LocationName' or \
                parent_el.tag == '{http://www.vdv.de/trias}StopPointName':
            stop_text_list.append(stop)
    return stop_text_list


# check if start and end stop are equal
def start_stop_equal(trip_1, trip_2) -> bool:
    trip_1_stops = extract_stops(trip_1)
    trip_2_stops = extract_stops(trip_2)
    if len(trip_1_stops) < 2 or len(trip_2_stops) < 2:  # min(len(trip_1_stops), len(trip_2_stops)) < 2
        return False
    return trip_1_stops[0].text == trip_2_stops[0].text and trip_1_stops[-1].text == trip_2_stops[-1].text


def get_loc_list(trip_list):
    stop_ref_list = list()
    for trip_res in trip_list:
        trip1 = trip_res.find(".//ns3:Trip", namespaces=NS)
        for loc in trip1.findall(".//ns3:Text", NS):
            loc_parent = loc.getparent()
            # if its parent is a stoppoint or an address
            if loc_parent.tag == "{http://www.vdv.de/trias}StopPointName" or \
                    loc_parent.tag == "{http://www.vdv.de/trias}LocationName":
                prev = loc_parent.getprevious()
                # if the sibling is a StopPointRef or AddressRef we can add its text
                if prev is not None and (prev.tag == "{http://www.vdv.de/trias}StopPointRef" or
                                         prev.tag == "{http://www.vdv.de/trias}AddressRef"):
                    stop_ref_list.append(prev.text)
    return stop_ref_list


def get_stop_ref_list(stop_ref_list, stop_dict):
    val_list = list()
    prev_stop = None
    for stop_ref in stop_ref_list:
        # if the location is in defined locations
        if stop_ref in stop_dict:
            # if it is not equal to the previous stop
            if stop_ref != prev_stop:
                val_list.append(stop_dict[stop_ref])
        else:
            print("StopPointRef or AddressRef:" + stop_ref + 'was not found not in the locations defined on top of '
                                                             'the file', file=sys.stderr)
        prev_stop = stop_ref
    return val_list


# create TripResponseContext from list of stop references
def create_Locations_element(stop_ref_list):
    g_parent_loc = etree.Element('{http://www.vdv.de/trias}TripResponseContext', nsmap=NS)
    parent_loc = etree.Element('{http://www.vdv.de/trias}Locations', nsmap=NS)
    g_parent_loc.append(parent_loc)
    for loc in stop_ref_list:
        parent_loc.append(deepcopy(loc))
    return g_parent_loc

def change_user_id(gg_parent, example_id, user_str = "8d6ba330-fefd-44ef-87a5-exmpl"):
    for el in gg_parent.findall(".//coactive:UserId", NS):
        if el.getparent().tag == "{http://shift2rail.org/project/coactive}User" or\
           el.getparent().tag == "{http://shift2rail.org/project/coactive}Traveller":
            el.text = user_str + str(example_id)

# test for stop ref list
# my_loc_list = get_loc_list(sel_merged_trips[0])
# stop_ref_list = get_stop_ref_list(my_loc_list, stop_dict)
# parent = create_Locations_element(broader_test_stop_list)


# load the XML
parser = etree.XMLParser(remove_blank_text=True, recover=True, encoding='utf-8')
trias_big_root = etree.parse("../xml_examples/example-offers.xml", parser=parser).getroot()

# used namespaces
NS = {'coactive': 'http://shift2rail.org/project/coactive', 'ns2': 'http://www.siri.org.uk/siri',
      'ns3': 'http://www.vdv.de/trias',
      'ns5': 'http://www.ifopt.org.uk/acsb', 'ns6': 'http://www.ifopt.org.uk/ifopt',
      'ns7': 'http://datex2.eu/schema/1_0/1_0', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

# get list of all Trips
trip_big_res_list = trias_big_root.findall(".//ns3:Trip", NS)

# get list of all TripResults
trip_res_list = trias_big_root.findall(".//ns3:TripResult", NS)


merged_trip_res = [[trip_res_list[0]]]
# merge the trips having similar start time and same first and last stop into a list
for trip_res_1 in trip_res_list[1:]:
    merged = False
    for merged_group in merged_trip_res:
        trip_res_2 = merged_group[0]
        if start_stop_equal(trip_res_1[1], trip_res_2[1]) and time_within_range(trip_res_1[1], trip_res_2[1]):
            merged_group.append(trip_res_1)
            merged = True
            break
    if not merged:
        merged_trip_res.append([trip_res_1])

# select the single mobility requests
selected_merged_trips = [4, 6, 16, 17, 24, 29, 38, 41, 60, 63, 11]

# create list of merged trips
sel_merged_trips = [merged_trip_res[i] for i in selected_merged_trips]

###

# Obtain list of all locations
loc_list = trias_big_root.xpath(".//ns3:Locations", namespaces=NS)[0]

# create a dictionary of locations - K: StopPointRef or AddressCode text, V: StopPointRef or AddressCode element
location_dict = dict()
for loc in loc_list:
    location = loc.find(".//ns3:StopPointRef", namespaces=NS)
    if location is None:
        location = loc.find(".//ns3:AddressCode", namespaces=NS)
    # if there is a stop ref and it is not in location_dict, add the location to the dict
    if location is not None and not location.text in location_dict:
        location_dict[location.text] = loc

#  Old version of get_loc_list which shuffled stoppointrefs and addresses
# def get_loc_list(trip_list):
#     stop_ref_list = list()
#     for trip_res in trip_list:
#         trip1 = trip_res.find(".//ns3:Trip", namespaces=NS)
#         trip_stops = trip1.findall(".//ns3:StopPointRef", namespaces=NS) + \
#                      trip1.findall(".//ns3:AddressRef", namespaces=NS)  # this is the new code
#         for trip_stop in trip_stops:
#             stop_ref_list.append(trip_stop.text)
#     return stop_ref_list


###
# Save the XML

# create the main structure of the XML file
ggg_parent = etree.Element('{http://www.vdv.de/trias}Trias', nsmap=NS)
gg_parent = etree.Element('{http://www.vdv.de/trias}ServiceDelivery', nsmap=NS)
g_parent = etree.Element('{http://www.vdv.de/trias}DeliveryPayload', nsmap=NS)
parent = etree.Element('{http://www.vdv.de/trias}TripResponse', nsmap=NS)

ggg_parent.append(gg_parent)

# append the user info
for t_el in trias_big_root[0]:
    if t_el.tag == '{http://www.vdv.de/trias}DeliveryPayload':
        break
    gg_parent.append(deepcopy(t_el))

gg_parent.append(g_parent)

# create an xml file for each single mobility request (element of sel_merg_trips) and write it to an .xml file
for i, mer_trip_res in enumerate(sel_merged_trips):
    parent = etree.Element('{http://www.vdv.de/trias}TripResponse', nsmap=NS)
    g_parent.append(parent)
    # get stop references from trip list
    my_loc_list = get_loc_list(mer_trip_res)
    # get list of full locations
    stop_ref_list = get_stop_ref_list(my_loc_list, location_dict)
    loc_element = create_Locations_element(stop_ref_list)

    parent.append(loc_element)
    # deepcopy the trips into parent TripResponse
    for trip_res in mer_trip_res:
        parent.append(deepcopy(trip_res))
    # change the user ID according to the example
    change_user_id(gg_parent, i)
    et = etree.ElementTree(ggg_parent)
    et.write('../xml_examples/basic_examples/sing_mob_exmpl_' + str(i) + '.xml', pretty_print=True,
             xml_declaration=True, encoding='UTF-8', standalone='yes')
    # remove reference from parents
    parent.getparent().remove(parent)
    # loc_element.getparent().remove(loc_element)

merged_trip_stats = False

if merged_trip_stats:
    ###
    # calculate number of trips, number of trip legs, number of tickets, number of transport modes
    mode_counts = []
    trips_cnt_list = []
    legs_cnt_list = []
    tickets_cnt_list = []
    real_tickets_cnt_list = []
    for trip_res_list in sel_merged_trips:
        trips = 0
        legs = 0
        tickets = 0
        mode_cnt = Counter()
        real_tickets = 0
        for trip_res in trip_res_list:
            trips += len(trip_res.findall(".//ns3:Trip", namespaces=NS))
            legs += len(trip_res.findall(".//ns3:TripLeg", namespaces=NS))
            tickets += len(trip_res.findall(".//ns3:Ticket", namespaces=NS))
            mode_cnt += (Counter([a.text for a in trip_res.findall(".//ns3:PtMode", NS)])) + \
                        (Counter([a.text for a in trip_res.findall(".//ns3:IndividualMode", NS)]))
            for ticket in trip_res.findall(".//ns3:Ticket", namespaces=NS):
                if ticket[0].text != 'META' and ticket[0].text[0:5] != 'DUMMY':
                    real_tickets += 1
        trips_cnt_list.append(trips)
        legs_cnt_list.append(legs)
        tickets_cnt_list.append(tickets)
        real_tickets_cnt_list.append(real_tickets)
        mode_counts.append(mode_cnt)

    mydataset = {
        'example_id': list(range(len(sel_merged_trips))),
        'trip_counts': trips_cnt_list,
        'leg_count': legs_cnt_list,
        'ticket_count': tickets_cnt_list,
        'real_ticket_count': real_tickets_cnt_list,
        'rail_counts': [i['rail'] for i in mode_counts],
        'metro_counts': [i['metro'] for i in mode_counts],
        'bus_counts': [i['bus'] for i in mode_counts],
        'unknown_counts': [i['unknown'] for i in mode_counts],
        'urbanRail_counts': [i['urbanRail'] for i in mode_counts],
        'air_counts': [i['air'] for i in mode_counts],
        'tram_counts': [i['tram'] for i in mode_counts],
        'walk_counts': [i['walk'] for i in mode_counts]
    }

    myvar = pd.DataFrame(mydataset)

    myvar.to_csv("../xml_examples/sing_mob_stats.csv", sep=";", decimal=",")

    # count mean number of tickets per trip:
    mer_count_list = []
    for mer_trip in merged_trip_res:
        tr_count_list = []
        for trip in mer_trip:
            tr_count_list.append(len(trip.findall(".//ns3:Ticket", NS)))
        mer_count_list.append(mean(tr_count_list))

    mer_count_list


    # count specific elements in merged trips
    def merged_trip_element_counter(merged_trips, element_text):
        elem_counts = []
        for mer_trip in merged_trips:
            tr_count_list = []
            for trip in mer_trip:
                tr_count_list.append(len(trip.findall(".//ns3:" + element_text, NS)))
            elem_counts.append(mean(tr_count_list))
        return elem_counts


    # count modes in merged trips
    mode_counts = []
    for mer_trip in merged_trip_res:
        cnt = Counter()
        for trip in mer_trip:
            # count transport modes nd
            cnt += (Counter([a.text for a in trip.findall(".//ns3:PtMode", NS)])) + \
                   (Counter([a.text for a in trip.findall(".//ns3:IndividualMode", NS)]))
        mode_counts.append(cnt)

    # create a table containing statistics about merged trips, where one merged trip corresponds to a single roww
    # calculate all transport modes
    mydataset = {
        'trip_counts': [len(t) for t in merged_trip_res],
        'mean_ticket_count': mer_count_list,
        'mean_leg_count': merged_trip_element_counter(merged_trip_res, "TripLeg"),
        'mean_timed_leg_count': merged_trip_element_counter(merged_trip_res, "TimedLeg"),
        'rail_counts': [i['rail'] for i in mode_counts],
        'metro_counts': [i['metro'] for i in mode_counts],
        'bus_counts': [i['bus'] for i in mode_counts],
        'unknown_counts': [i['unknown'] for i in mode_counts],
        'urbanRail_counts': [i['urbanRail'] for i in mode_counts],
        'air_counts': [i['air'] for i in mode_counts],
        'tram_counts': [i['tram'] for i in mode_counts],
        'walk_counts': [i['walk'] for i in mode_counts]
    }

    myvar = pd.DataFrame(mydataset)

    myvar.to_csv("../xml_examples/mer_trip_stats.csv", sep=";", decimal=",")

# get the trips that cointain addresses
# address_trips = []
# for j,trip_list in enumerate(merged_trip_res):
#     for i,trip in enumerate(trip_list):
#         if trip.findall(".//ns3:AddressRef", namespaces=NS) != []:
#             print(str(i) + '(' + str(j) + '): ' + trip.find(".//ns3:TripId", namespaces=NS).text)
#             address_trips.append(trip)
#
