#####
# adds data as the last leg of a trip
# data is taken from the rs_dict dictionary
from lxml import etree
from copy import deepcopy
import sys

ns3_prefix = '{http://www.vdv.de/trias}'

NS = {'coactive': 'http://shift2rail.org/project/coactive', 'ns2': 'http://www.siri.org.uk/siri',
      'ns3': 'http://www.vdv.de/trias',
      'ns5': 'http://www.ifopt.org.uk/acsb', 'ns6': 'http://www.ifopt.org.uk/ifopt',
      'ns7': 'http://datex2.eu/schema/1_0/1_0', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}


def err_print(text):
    print(text, file=sys.stderr)


# creates an subelement with text
def create_SubElement(_parent, _tag, attrib={}, _text=None, nsmap=None, **_extra):
    result = etree.SubElement(_parent, _tag, attrib, nsmap, **_extra)
    result.text = _text
    return result


# creates subtree of LegStart or LegEnd with given location reference and location name
def createStopRefSubtree(leg_el, leg_ref, point_location_text, address=False, nsmap=NS):
    stop_ref = 'StopPointRef'
    if address:  # if it is not an StopPoint but address
        stop_ref = 'AddressRef'
    create_SubElement(leg_el, _tag=ns3_prefix + stop_ref, _text=leg_ref, nsmap=nsmap)
    point_location_name = create_SubElement(leg_el, _tag=ns3_prefix + 'LocationName', nsmap=nsmap)
    create_SubElement(point_location_name, _tag=ns3_prefix + 'Text', _text=point_location_text, nsmap=nsmap)


# adds leg containing ridesharing data
def add_rs_leg(trip, rs_dict, ns3_prefix):
    trip_leg = create_SubElement(trip, _tag=ns3_prefix + 'TripLeg', nsmap=NS)
    create_SubElement(trip_leg, _tag=ns3_prefix + 'LegId', _text=rs_dict['LegId'], nsmap=NS)
    continuous_leg = create_SubElement(trip_leg, _tag=ns3_prefix + 'ContinuousLeg', nsmap=NS)

    tag_list = ['LegStart', 'LegEnd', 'Service', 'TimeWindowStart', 'TimeWindowEnd', 'Duration']
    for t, v in zip(tag_list, [rs_dict[k] for k in tag_list]):
        create_SubElement(continuous_leg, _tag=ns3_prefix + t, _text=v, nsmap=NS)
    extension_el = create_SubElement(continuous_leg, _tag=ns3_prefix + 'Extension',
                                     attrib={'{http://www.w3.org/2001/XMLSchema-instance}type':
                                                 'coactive:LegExtension'}, nsmap=NS)
    create_SubElement(extension_el, _tag='{http://shift2rail.org/project/coactive}' + 'TravelExpertId',
                      _text=rs_dict['TravelExpertId'], nsmap=NS)
    createStopRefSubtree(continuous_leg[0], rs_dict['LegStartRef'], rs_dict['start_point_loc_text'], address=True)
    createStopRefSubtree(continuous_leg[1], rs_dict['LegStopRef'], rs_dict['end_point_loc_text'])

    service_el = trip_leg.find('.//ns3:Service', namespaces=NS)
    create_SubElement(service_el, _tag=ns3_prefix + 'IndividualMode', _text='others-drive-car', nsmap=NS)
    sharing_ser_el = create_SubElement(service_el, _tag=ns3_prefix + 'SharingService', nsmap=NS)

    tag_list = ['OperatorRef', 'Name', 'InfoUrl']
    info_url_el = None
    for t, v in zip(tag_list, [rs_dict[k] for k in tag_list]):
        el = create_SubElement(sharing_ser_el, _tag=ns3_prefix + t, _text=v, nsmap=NS)
        if t == 'InfoUrl':
            info_url_el = el

    label_el = create_SubElement(info_url_el, _tag=ns3_prefix + 'Label', nsmap=NS)
    create_SubElement(label_el, _tag=ns3_prefix + 'Text', _text=rs_dict['CarModelText'], nsmap=NS)
    create_SubElement(info_url_el, _tag=ns3_prefix + 'Url', _text=rs_dict['CarURL'], nsmap=NS)


###############################################################
# Script part which has to be changed to enrich the examples
################################################################

# Define XML parser
parser = etree.XMLParser(remove_blank_text=True, recover=True, encoding='utf-8')

# Parse the first example
example_root = etree.parse('../xml_examples/basic_examples/sing_mob_exmpl_1.xml',
                           parser=parser).getroot()
# # Copy the trip
# xmpl_trip = deepcopy(example_root.findall(".//ns3:Trip", NS)[1])
# # check the trip
# print(xmpl_trip.tag == '{http://www.vdv.de/trias}Trip')

# define the dictionary for the first ridesharing leg
rs_dict1 = {
    'LegId': 'RS-leg-id-01',
    'LegStart': None,
    'LegEnd': None,
    'LegStartRef': 'http://it2rail.org/infrastructure/tmb/3:par_5_46-R',
    'LegStopRef': 'http://it2rail.org/infrastructure/tmb/3:par_5_77-R',
    'start_point_loc_text': 'MENDEZ ALVARO',
    'end_point_loc_text': 'SERNA LA',
    'Service': None,
    'TimeWindowStart': '2020-11-10T07:30:00.000Z',
    'TimeWindowEnd': '2020-11-10T07:51:00.000Z',
    'Duration': 'PT31M',
    'TravelExpertId': 'rs_expert',
    'OperatorRef': 'RSOperator_1',
    'Name': 'Driver_Joe1',
    'InfoUrl': None,
    'CarModelText': 'BMW_X5_xDrive40e',
    'CarURL': 'https://en.wikipedia.org/wiki/BMW_X5_(F15)#X5_xDrive40e'
}


# extract the root
example_root = etree.parse('../xml_examples/basic_examples/sing_mob_exmpl_1.xml',
                           parser=parser).getroot()
# extract xml trip
xmpl_trip = deepcopy(example_root.xpath(".//ns3:ResultId[text() = '38e36a2a-b515-4f7f-a1be-bebf38b3757f']",
                                        namespaces=NS)[0].getparent()[1])
# check if it is a trip
print(xmpl_trip.tag == '{http://www.vdv.de/trias}Trip')

# add the ridesharing leg based on the rs_dictionary attributes
add_rs_leg(xmpl_trip, rs_dict=rs_dict1, ns3_prefix=ns3_prefix)
# print the trip
print(etree.tostring(xmpl_trip, encoding="unicode", pretty_print=True))

#################
# Second example

# define dictionary for the second ridesharing leg
rs_dict3 = {
    'LegId': 'RS-leg-id-03',
    'LegStart': None,
    'LegEnd': None,
    'LegStartRef': 'http://it2rail.org/infrastructure/tmb/1:par_6_92-B',
    'LegStopRef': 'http://it2rail.org/infrastructure/tmb/3:par_5_77-R',
    'start_point_loc_text': 'Méndez Álvaro-Estación Sur',
    'end_point_loc_text': 'SERNA LA',
    'Service': None,
    'TimeWindowStart': '2020-11-12T07:18:20.000Z',
    'TimeWindowEnd': '2020-11-12T07:46:00.000Z',
    'Duration': 'PT27M40S + ',
    'TravelExpertId': 'rs_expert',
    'OperatorRef': 'RSOperator_1',
    'Name': 'Driver_Joe1',
    'InfoUrl': None,
    'CarModelText': 'BMW_X5_xDrive40e',
    'CarURL': 'https://en.wikipedia.org/wiki/BMW_X5_(F15)#X5_xDrive40e'
}

example_root = etree.parse('../xml_examples/basic_examples/sing_mob_exmpl_3.xml',
                           parser=parser).getroot()
xmpl_trip = deepcopy(example_root.xpath(".//ns3:ResultId[text() = '728f1f64-2d90-4da1-84b4-0e49ad4bf331']",
                                        namespaces=NS)[0].getparent()[1])

xmpl_trip.find
print(xmpl_trip.tag == '{http://www.vdv.de/trias}Trip')
add_rs_leg(xmpl_trip, rs_dict=rs_dict3, ns3_prefix=ns3_prefix)
print(etree.tostring(xmpl_trip, encoding="unicode", pretty_print=True))

rs_dict10 = {
    'LegId': 'RS-leg-id-10',
    'LegStart': None,
    'LegEnd': None,
    'LegStartRef': 'A=2@O=Málaga, Calle Quasimodo 13-5@X=-4465409@Y=36709393@u=0@U=103@L=981016558@',
    'LegStopRef': 'GenericStation_Lon:-4.456350803375244_Lat:36.691253662109375',
    'start_point_loc_text': 'Málaga, Calle Quasimodo 13-5',
    'end_point_loc_text': 'Avda. de Velázquez (Avda. Moliére)',
    'Service': None,
    'TimeWindowStart': '2020-11-28T07:27:00.000Z',
    'TimeWindowEnd': '2020-11-28T07:56:00.000Z',
    'Duration': 'PT29M',
    'TravelExpertId': 'rs_expert',
    'OperatorRef': 'RSOperator_1',
    'Name': 'Driver_Joe1',
    'InfoUrl': None,
    'CarModelText': 'BMW_X5_xDrive40e',
    'CarURL': 'https://en.wikipedia.org/wiki/BMW_X5_(F15)#X5_xDrive40e'
}

# replaced legs
# 89fa567a-c73f-4a21-b9d9-db9155a25a9e
# IDa84a35bb-6627-4c50-a0d0-02ca12e149a6

example_root = etree.parse('../xml_examples/basic_examples/sing_mob_exmpl_10.xml',
                           parser=parser).getroot()
xmpl_trip = deepcopy(example_root.xpath(".//ns3:ResultId[text() = 'f94e653a-8dcf-4b2c-8986-55bbd3ffc25d']",
                                        namespaces=NS)[0].getparent()[1])
print(xmpl_trip.tag == '{http://www.vdv.de/trias}Trip')
add_rs_leg(xmpl_trip, rs_dict=rs_dict10, ns3_prefix=ns3_prefix)
print(etree.tostring(xmpl_trip, encoding="unicode", pretty_print=True))

######################################################################################
# Section serves to edit tickets

# new example
tripid = '38e36a2a-b515-4f7f-a1be-bebf38b3757f'
example_root = etree.parse('../xml_examples/basic_examples/sing_mob_exmpl_1.xml',
                           parser=parser).getroot()
xmpl_trip = deepcopy(example_root.xpath(".//ns3:ResultId[text() = '" + tripid + "']", namespaces=NS)[0].getparent())
add_rs_leg(xmpl_trip.find('{http://www.vdv.de/trias}Trip', NS), rs_dict=rs_dict1, ns3_prefix=ns3_prefix)
# print(etree.tostring(xmpl_trip, encoding="unicode", pretty_print=True))

# replace string behind last split char with the append_text
# @text - string which is parsed
# @append_text - text to append
# @split_char - character based on which is the string splitted
def replace_last_string(text, append_text, split_char='-'):
    str_list = text.split(split_char)
    str_list[-1] = append_text
    return split_char.join(str_list)


# used to better distinguish between the trips
# replace string of the passed trip_result at a given element (element_name, element_id)
# behind the last "-" with the append_text
# @trip_result - trip result element
# @element_name - name of the element, please add correct prefix, e.g. if element_id passed, "ns3:" should be added
#                 instead of "{http://www.vdv.de/trias}" as the xpath is used there
# @append_text - text to append
# @element_id - if of the element
def replace_tag_rs1(trip_result, element_name, append_text='rs1', element_id=None, replace_whole_string=False):
    elem_list = None
    if element_id is None:
        elem_list = trip_result.findall('.//' + element_name, NS)
    else:
        elem_list = trip_result.xpath(".//" + element_name + "[text() = '" + element_id + "']", namespaces=NS)
    if len(elem_list) == 0:
        err_print('Element ' + element_name + ' with text ' + element_id + ' was not found')
        return
    for element in elem_list:
        if replace_whole_string:
            element.text = append_text
        else:
            element.text = replace_last_string(element.text, append_text)


# adds the given offer item context
# @_code - code for the Code element
# @_value - value for the Value element
# @_parent_el - parent element to which the item will be added
def add_offer_item_context(_code=None, _value=None, _parent_el=None, nsmap=None, attrib={}, **_extra):
    parent_elem = create_SubElement(_parent_el, '{http://shift2rail.org/project/coactive}OfferItemContext', nsmap=nsmap)
    create_SubElement(parent_elem, "{http://shift2rail.org/project/coactive}Code", _text=_code, nsmap=nsmap)
    create_SubElement(parent_elem, "{http://shift2rail.org/project/coactive}Value", _text=_value, nsmap=nsmap)


# modifies the leg according to provided parameters to a ridesharing leg
# changes leg id, offer id, ticket id, and provides additional
# @trip - trip element
# @leg_id - id of leg
# @offer_id - id of offer
# @ticket_id - id of ticket
# @new_rs_leg_id - new id of RS leg
def modify_trip_rs(trip, leg_id, offer_id, ticket_id, new_rs_leg_id = 'RS-leg-id-1'):
    # extend trip id
    replace_tag_rs1(trip, '{http://www.vdv.de/trias}TripId')
    # change leg id
    replace_tag_rs1(trip, 'ns3:LegId', append_text=new_rs_leg_id,
                    element_id=leg_id, replace_whole_string=True)

    rs_ticket = trip.xpath(".//ns3:TicketId[text() = '" + ticket_id + "']", namespaces=NS)[0].getparent()
    # dict: offer id
    replace_tag_rs1(trip, 'coactive:OfferId', element_id=offer_id)
    replace_tag_rs1(trip, '{http://shift2rail.org/project/coactive}TripId')
    # ticket name
    replace_tag_rs1(rs_ticket, 'ns3:TicketName', append_text='RideSharing Ticket',
                    element_id='Standard Ticket', replace_whole_string=True)
    replace_tag_rs1(rs_ticket, 'ns3:FaresAuthorityRef', append_text='RS authority',
                    replace_whole_string=True)
    replace_tag_rs1(rs_ticket, 'ns3:FaresAuthorityText', append_text='RS authority',
                    replace_whole_string=True)
    # modify ticketId
    replace_tag_rs1(rs_ticket, 'ns3:TicketId', append_text='rs1',
                    element_id=ticket_id)

    # dict: TravelEpisodeId, legid
    travel_episode_id = \
        trip.xpath(".//coactive:TravelEpisodeId[text() = '" + leg_id + "']", namespaces=NS)[0]
    validity_el = travel_episode_id.getparent()
    # keep only ridesharing ticket in validity element
    for child in list(validity_el):
        if child.text != leg_id:
            validity_el.remove(child)
    #
    add_offer_item_context('PASSENGER_REF', 'pasenger_id_1', validity_el.getparent(), NS)
    # replace only ticket
    replace_tag_rs1(rs_ticket, 'coactive:TravelEpisodeId', append_text=new_rs_leg_id,
                    element_id=leg_id, replace_whole_string=True)
    return xmpl_trip


# print the ticket
# modify the ids below to the one you would like to replace
print(etree.tostring(
    modify_trip_rs(xmpl_trip,
                   leg_id = 'IDa9764c79-2634-49d6-9a2e-48f6b32d57a4',
                   offer_id= '2a8e0e6c-285d-4c8c-b98f-76a54b358257',
                   ticket_id= 'ID4cea6534-9e18-4fdc-85d6-bdded89af6b9'),
    encoding="unicode", pretty_print=True))


