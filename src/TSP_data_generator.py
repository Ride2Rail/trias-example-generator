########
#  this files serves as generator of TSP data for the TRIAS XML files
#  it automatically generates TSP data for all the examples in the "single_mobility_request_examples" directory
#
import sys
from lxml import etree
import random
from datetime import datetime
from datetime import timedelta
import os
from os import path
from copy import deepcopy
from lxml import objectify

####
#

NS = {'coactive': 'http://shift2rail.org/project/coactive', 'ns2': 'http://www.siri.org.uk/siri',
      'ns3': 'http://www.vdv.de/trias',
      'ns5': 'http://www.ifopt.org.uk/acsb', 'ns6': 'http://www.ifopt.org.uk/ifopt',
      'ns7': 'http://datex2.eu/schema/1_0/1_0', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}


# list of available factors
factor_list = ['likelihood_of_delays', 'last_minute_changes', 'frequency_of_service', 'user_feedback', 'cleanliness',
               'seating_quality', 'space_available', 'silence_area_presence', 'privacy_level', 'bike_on_board',
               'business_area_presence', 'internet_availability', 'plugs_or_charging_points',
               'number_of_persons_sharing_trip', 'shared_with_other_passengers','can_share_cost', 'safety_features',
               'vehicle_age', 'passenger_feedback', 'certified_driver', 'driver_license_issue_date', 'repeated_trip',
               'ride_smoothness']

# dictionary of factor probabilities
factor_probabilities_dict = dict.fromkeys(factor_list, 0.25)

# all modes, except modes like walking and cycling which were not enriched as they do not have any attributes
all_modes = 'all'
public_transport = ['bus', 'tram', 'rail', 'metro', 'air', 'urbanRail']
ridesharing = 'others-drive-car'

# dic
factors_modes_dict = {
    'likelihood_of_delays': all_modes,
    'last_minute_changes': public_transport + [ridesharing],
    'frequency_of_service': public_transport,
    'user_feedback': all_modes,
    'cleanliness': public_transport + [ridesharing],
    'seating_quality': all_modes,
    'space_available': all_modes,
    'silence_area_presence': 'rail',
    'privacy_level': all_modes,
    'bike_on_board': public_transport + [ridesharing],
    'business_area_presence': ['rail', 'air'],
    'internet_availability': public_transport + [ridesharing],
    'plugs_or_charging_points': public_transport + [ridesharing],
    'number_of_persons_sharing_trip': ridesharing,
    'shared_with_other_passengers': ridesharing,
    'can_share_cost': ridesharing,
    'safety_features': public_transport + [ridesharing],
    'vehicle_age': ridesharing,
    'passenger_feedback': public_transport + [ridesharing],
    'certified_driver': ridesharing,
    'driver_license_issue_date': ridesharing,
    'repeated_trip': ridesharing,
    'ride_smoothness': ridesharing
}

# dictionary for factors_modes_dict invertion
modes_factors_dict = {k: [] for k in public_transport + [ridesharing]}

# invert the factors_modes_dict dictionary, so for each transport mode are as a value parameters provided
for k, v in factors_modes_dict.items():
    if v == 'all':
        for tm in modes_factors_dict.keys():
            modes_factors_dict[tm].append(k)
    elif type(v) == str:
        modes_factors_dict[v].append(k)
    else:
        for tm in v:
            modes_factors_dict[tm].append(k)

# predefined domain values
real_0_1 = ['real', 0, 1]  # <0, 1>
binary = ['int', 0, 1]  # 0 or 1
int_1_20 = ['int', 1, 20]  # range 1 to 20
stars_5 = ['real', 1, 5]  # 5 stairs

factors_values_dict = {
    'likelihood_of_delays': real_0_1,
    'last_minute_changes': real_0_1,
    'frequency_of_service': int_1_20,
    'user_feedback': stars_5,
    'cleanliness': stars_5,
    'seating_quality': stars_5,
    'space_available': stars_5,
    'silence_area_presence': binary,
    'privacy_level': stars_5,
    'bike_on_board': binary,
    'business_area_presence': binary,
    'internet_availability': binary,
    'plugs_or_charging_points': binary,
    'number_of_persons_sharing_trip': int_1_20,
    'shared_with_other_passengers': binary,
    'can_share_cost ': binary,
    'safety_features': stars_5,
    'vehicle_age': ['int', 0, 25],
    'passenger_feedback': stars_5,
    'certified_driver': binary,
    'driver_license_issue_date': ['date', '1960-1-1T00:00:00.000Z', '2020-1-1T00:00:00.000Z'],
    'repeated_trip': binary,
    'ride_smoothness': stars_5
}

parser = etree.XMLParser(remove_blank_text=True, recover=True, encoding='utf-8')


# rewrite this to get error print
def err_print(text):
    print(text, file=sys.stderr)


# adds to a element provided as _\_parent_ a subelement with a given tag, text and attributes
def create_SubElement(_parent, _tag, attrib={}, _text=None, nsmap=None, **_extra):
    result = etree.SubElement(_parent, _tag, attrib, nsmap, **_extra)
    result.text = _text
    return result


# adds provided TSP info to a specified element, as OfferitemContext element with two child Code and Value,
# where to the Code element is _code parameter added as text with a _legid appended to _code if provided.
# The _value is added as text to the Value element
def add_TSP_info(_code=None, _legid=None, _value=None, _parent_el=None, nsmap=None, attrib={}, **_extra):
    parent_elem = create_SubElement(_parent_el, '{http://shift2rail.org/project/coactive}OfferItemContext', nsmap=nsmap)
    if _legid is not None:
        _code = _code + ":" + str(_legid)
    create_SubElement(parent_elem, "{http://shift2rail.org/project/coactive}Code", _text=_code, nsmap=nsmap)
    create_SubElement(parent_elem, "{http://shift2rail.org/project/coactive}Value", _text=str(_value), nsmap=nsmap)
    objectify.deannotate(parent_elem, cleanup_namespaces=True)
    return parent_elem


# appends the text_append parameter to User or Traveller element's text
def change_append_user_id(gg_parent, text_append):
    for el in gg_parent.findall(".//coact"
                                "ive:UserId", NS):
        if el.getparent().tag == "{http://shift2rail.org/project/coactive}User" or \
                el.getparent().tag == "{http://shift2rail.org/project/coactive}Traveller":
            el.text = el.text + text_append


# function to convert datetime to unix timestamp
# if the time is below Unix 0 (negative) add it to Unix  time
def datetime_to_unix(time_in_seconds):
    if time_in_seconds < 0:
        return datetime(1970, 1, 1) + timedelta(seconds=time_in_seconds)
    else:
        return datetime.utcfromtimestamp(time_in_seconds)


# random date generation for a given range in a provided format
# prop parameter is the probability serving as a proportion between start and date which specifies exactly the date
# inspired by: https://stackoverflow.com/questions/553303/generate-a-random-date-between-two-other-dates
def random_date(start, end, prop, format='%Y-%m-%dT%H:%M:%S.%fZ'):
    # substraction is for the case if the date is before unix time
    stime = (datetime.strptime(start, format) - datetime(1970, 1, 1)).total_seconds()
    etime = (datetime.strptime(end, format) - datetime(1970, 1, 1)).total_seconds()
    ptime = stime + prop * (etime - stime)
    # for whole seconds
    ptime = round(ptime)
    form_time = datetime_to_unix(ptime)
    return form_time.strftime(format)[0:-4] + "Z"


# generate a value for a given factor, where the val_dict is a dictionary with factor names
# as keys and list of [domain, from, to] as values.
# The range domain is taken from the 0 index and the range from 1 and 2 indices of the list.
# If the domain is not from {'real', 'int', 'date'}, where int is also for binary values, it returns an error.
def generate_value(val_dict, factor):
    i_list = val_dict[factor]
    if i_list[0] == 'real':
        return round(random.uniform(i_list[1], i_list[2]), 2)
    elif i_list[0] == 'int':
        return random.randint(i_list[1], i_list[2])
    elif i_list[0] == 'date':
        return random_date(i_list[1], i_list[2], random.random())
    else:
        err_print('unsupported type of data domain')


# time.mktime(time.strptime('1980-1-1T00:00:00.000Z', '%Y-%m-%dT%H:%M:%S.%fZ'))


# returns transport mode for a given leg
def get_transport_mode(leg):
    # if the mode is a walk skip the trip_leg
    transp_mode = leg.find(".//ns3:IndividualMode", NS)
    if transp_mode is not None:
        return transp_mode.text
    # otherwise should be under PtMode
    transp_mode = leg.find(".//ns3:PtMode", namespaces=NS)
    if transp_mode is not None:
        return transp_mode.text
    else:
        return None


# returns dictionary of generated values for the given transport mode
def generate_values_to_dict(transp_mode, modes_factors_dict, factor_probabilities_dict, factors_values_dict):
    # generate the factor values and add them to dictionary
    tmp_fact_val_dict = {}
    for factor in modes_factors_dict[transp_mode]:
        if random.uniform(0, 1) < factor_probabilities_dict[factor]:
            tmp_fact_val_dict[factor] = generate_value(factors_values_dict, factor)
    return tmp_fact_val_dict


# returns true if the provided transport mode should be skipped
# provides additional warnings
def skip_transport_mode(transport_mode, leg_id):
    if transport_mode is None:
        err_print("Transport mode at leg: " + leg_id + " was not found under common elements (IndividualMode, PtMode)")
        return True
    # for these we do not generate
    if transport_mode in ('unknown', 'walk', 'cycle'):
        return True
    # if the mode is undefined
    elif transport_mode not in modes_factors_dict:
        err_print("Transport mode " + transport_mode + " is not defined at leg id: " + leg_id)
        return True


# enriches the trip_result based on the provided dictionaries
# if the legs reoccur in tickes, the generated values are the same
def enrich_tickets_tripresult(trip_result, modes_factors_dict, factor_probabilities_dict, factors_values_dict):
    # dictionary storing probabilities for reoccuring legs in tickets
    trip_generated_dict = {}
    for trip_fare in trip_result.findall('.//ns3:TripFares', NS):
        # for each tripfare check the ticket
        for ticket in trip_fare.findall('.//ns3:Ticket', NS):
            ticket_id = ticket.find('.//ns3:TicketId', NS)
            if ticket_id is None:
                err_print("Ticket has no TicketId!")
            # skip meta tickets
            if ticket_id.text == 'META':
                continue
            # extract leg id
            travel_episode_id = ticket.find(".//coactive:TravelEpisodeId", NS)
            # throw error if it misses travel episode
            if travel_episode_id is None:
                err_print("Travel episode is missing from the ticket with id: " + ticket_id.text)
                continue
            leg_id = travel_episode_id.text
            # fin leg by id
            leg = trip_result.xpath(".//ns3:LegId[text() = '" + leg_id + "']", namespaces=NS)
            # check if leg with provided id exists
            if not leg or leg[0].getparent().tag != "{http://www.vdv.de/trias}TripLeg":
                err_print("leg with id: " + leg_id + " was not found")
                continue
            leg = leg[0].getparent()
            # obtain transport mode of the leg
            transport_mode = get_transport_mode(leg)
            if skip_transport_mode(transport_mode, leg_id):
                continue
            factor_gen_dict = {}
            # check if the data was already generated for the given leg
            if leg_id in trip_generated_dict:
                factor_gen_dict = trip_generated_dict[leg_id]
            # otherwise generate values and add it to the dictionary
            else:
                factor_gen_dict = generate_values_to_dict(transport_mode, modes_factors_dict,
                                                          factor_probabilities_dict, factors_values_dict)
                trip_generated_dict[leg_id] = factor_gen_dict
            extension = ticket.find(".//{http://www.vdv.de/trias}Extension")
            if extension is None:
                err_print('Ticket with id: ' + ticket_id.text + ' has not an Extension element!')
                continue
            # generate the factors with values into the extension element
            for code, val in factor_gen_dict.items():
                add_TSP_info(_code=code, _legid=leg_id, _value=val, _parent_el=extension, nsmap=NS)


def generate_examples(path_dict, modes_factors_dict, factor_probabilities_dict, factors_values_dict,
                      probabilities=None, subfolders=True, prob_codes = None):
    if probabilities is None:
        probabilities = [0.25, 0.5, 0.75]
    if prob_codes is None:
        prob_codes = ['025', '050', '075']
    for enriched_ver in range(len(probabilities)):
        # change the dictionary probabilities to the provided probabilities
        for key in factor_probabilities_dict.keys():
            factor_probabilities_dict[key] = probabilities[enriched_ver]
        # iterate over all the provided file numbers
        for i in path_dict['file_num']:
            # concatenate the full path to the file
            file = path_dict['example_path'] + str(i) + '.xml'
            if os.path.isfile(file):
                # parse the XML
                example_root = etree.parse(file, parser=parser).getroot()
                change_append_user_id(example_root, '-v-' + str(enriched_ver + 1))
                # iterate over all tripresults
                for trip_res in example_root.findall(".//ns3:TripResult", NS):
                    enrich_tickets_tripresult(trip_res, modes_factors_dict, factor_probabilities_dict,
                                              factors_values_dict)
                # concatenate the path
                path = path_dict['generation_dir'] + path_dict['xml_name']
                # split into subfolders if the path are basic examples
                if subfolders:
                    path = path_dict['generation_dir'] + str(i) + "/" + path_dict['xml_name']
                # write the tree into XML with concatenating the name
                etree.ElementTree(example_root).write(path + "no_" + str(i) + '_tsp_' + prob_codes[enriched_ver] + '.xml',
                                                      pretty_print=True, xml_declaration=True, encoding='UTF-8',
                                                      standalone='yes')
            else:
                err_print('File: ' + file + ' seems not like a valid file')


######################################################################################
# Code to run is below
#

# example_root = etree.parse("../xml_examples/examples_subset_1/r2r_example_4.xml", parser=parser).getroot()
# for trip_res in example_root.findall(".//ns3:TripResult", NS):
#     enrich_tickets_tripresult(trip_res, modes_factors_dict, factor_probabilities_dict, factors_values_dict)

examples_dir = "../xml_examples/"

if not path.isdir(examples_dir):
    err_print(examples_dir + " is not a valid directory! Please create a valid directory or change its path.")
    exit()

#
# hacon_examples = {
#     'example_path': examples_dir + 'subset_1/subset_1_no_',
#     'file_num': [3, 9, 12, 18, 21, 22, 26, 37, 44, 50],
#     'generation_dir': examples_dir + 'enriched_subset_1/',
#     'xml_name': 'subset_1_'
# }


# hacon_examples = {
#     'example_path': examples_dir + 'subset_2/subset_2_no_',
#     'file_num': list(range(1, 11)),
#     'generation_dir': examples_dir + 'enriched_subset_2/',
#     'xml_name': 'subset_2_'
# }

## Ridesharing examples

hacon_examples = {
    'example_path': examples_dir + 'subset_3/subset_3_no_',
    'file_num': [3, 5, 9],
    'generation_dir': examples_dir + 'enriched_subset_3/',
    'xml_name': 'subset_3_'
}


factor_probability_values = [0.25, 0.5, 0.75]

# set seed
random.seed(123)

generate_examples(hacon_examples,
                  modes_factors_dict=modes_factors_dict,
                  factor_probabilities_dict=factor_probabilities_dict,
                  factors_values_dict=factors_values_dict,
                  probabilities=factor_probability_values,
                  subfolders=False)

