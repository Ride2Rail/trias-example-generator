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
# as first create a dictionary for each transport mode with the available factors
# then load probablilities from as csv file

# from: https://stackoverflow.com/questions/6740918/creating-a-dictionary-from-a-csv-file
# import csv
# reader = csv.reader(open('filename.csv', 'r'))
# d = {}
# for row in reader:
#    k, v = row
#    d[k] = v


NS = {'coactive': 'http://shift2rail.org/project/coactive', 'ns2': 'http://www.siri.org.uk/siri',
      'ns3': 'http://www.vdv.de/trias',
      'ns5': 'http://www.ifopt.org.uk/acsb', 'ns6': 'http://www.ifopt.org.uk/ifopt',
      'ns7': 'http://datex2.eu/schema/1_0/1_0', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

factor_probabilitites_dict = {
    'likelihood_of_delays': 0.25,
    'last_minute_changes': 0.25,
    'frequency_of_service': 0.25,
    'user_feedback': 0.25,
    'cleanliness': 0.25,
    'seating_quality': 0.25,
    'space_available': 0.25,
    'silence_area_presence': 0.25,
    'privacy_level': 0.25,
    'bike_on_board': 0.25,
    'business_area_presence': 0.25,
    'internet_availability': 0.25,
    'plugs_or_charging_points': 0.25,
    'number_of_persons_sharing_trip': 0.25,
    'shared_with_other_passengers': 0.25,
    'safety_features': 0.25,
    'vehicle_age': 0.25,
    'passenger_feedback': 0.25,
    'certified_driver': 0.25,
    'driver_license_issue_date': 0.25,
    'repeated_trip': 0.25
}

factors_modes_dict = {
    'likelihood_of_delays': 'all',
    'last_minute_changes': ['bus', 'tram', 'rail', 'metro', 'air', 'urbanRail', 'others-drive-car'],
    'frequency_of_service': ['bus', 'tram', 'rail', 'metro', 'air', 'urbanRail', 'others-drive-car'],
    'user_feedback': 'all',
    'cleanliness': ['bus', 'tram', 'rail', 'metro', 'air', 'urbanRail', 'others-drive-car'],
    'seating_quality': 'all',
    'space_available': 'all',
    'silence_area_presence': 'rail',
    'privacy_level': 'all',
    'bike_on_board': ['bus', 'tram', 'rail', 'metro', 'air', 'urbanRail', 'others-drive-car'],
    'business_area_presence': ['rail', 'air'],
    'internet_availability': ['bus', 'tram', 'rail', 'metro', 'air', 'urbanRail', 'others-drive-car'],
    'plugs_or_charging_points': ['bus', 'tram', 'rail', 'metro', 'air', 'urbanRail', 'others-drive-car'],
    'number_of_persons_sharing_trip': 'others-drive-car',
    'shared_with_other_passengers': 'others-drive-car',
    'safety_features': ['bus', 'tram', 'rail', 'metro', 'air', 'urbanRail', 'others-drive-car'],
    'vehicle_age': 'others-drive-car',
    'passenger_feedback': ['bus', 'tram', 'rail', 'metro', 'air', 'urbanRail', 'others-drive-car'],
    'certified_driver': 'others-drive-car',
    'driver_license_issue_date': 'others-drive-car',
    'repeated_trip': 'others-drive-car'
}

# dictionary for factors_modes_dict invertion
modes_factors_dict = {
    'bus': [],
    'tram': [],
    'rail': [],
    'metro': [],
    'air': [],
    'urbanRail': [],
    'others-drive-car': []
}

# invert the previous dictionary factors_modes_dict dictionary
for k, v in factors_modes_dict.items():
    if v == 'all':
        for tm in modes_factors_dict.keys():
            modes_factors_dict[tm].append(k)
    elif type(v) == str:
        modes_factors_dict[v].append(k)
    else:
        for tm in v:
            modes_factors_dict[tm].append(k)

factors_values_dict = {
    'likelihood_of_delays': ['real', 0, 1],
    'last_minute_changes': ['real', 0, 1],
    'frequency_of_service': ['int', 1, 20],
    'user_feedback': ['real', 1, 5],
    'cleanliness': ['real', 1, 5],
    'seating_quality': ['real', 1, 5],
    'space_available': ['real', 1, 5],
    'silence_area_presence': ['int', 0, 1],
    'privacy_level': ['real', 1, 5],
    'bike_on_board': ['int', 0, 1],
    'business_area_presence': ['int', 0, 1],
    'internet_availability': ['int', 0, 1],
    'plugs_or_charging_points': ['int', 0, 1],
    'number_of_persons_sharing_trip': ['int', 1, 20],
    'shared_with_other_passengers': ['int', 0, 1],
    'safety_features': ['real', 1, 5],
    'vehicle_age': ['int', 0, 25],
    'passenger_feedback': ['real', 1, 5],
    'certified_driver': ['int', 0, 1],
    'driver_license_issue_date': ['date', '1960-1-1T00:00:00.000Z', '2020-1-1T00:00:00.000Z'],
    'repeated_trip': ['int', 0, 1]
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
def generate_values_to_dict(transp_mode, modes_factors_dict, factor_probabilitites_dict, factors_values_dict):
    # generate the factor values and add them to dictionary
    tmp_fact_val_dict = {}
    for factor in modes_factors_dict[transp_mode]:
        if random.uniform(0, 1) < factor_probabilitites_dict[factor]:
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
        err_print("Transport mode " + transport_mode + " is not defined at leg id: " + leg_id )
        return True


# enriches the trip_result based on the provided dictionaries
# if the legs reoccur in tickes, the generated values are the same
def enrich_tickets_tripresult(trip_result, modes_factors_dict, factor_probabilitites_dict, factors_values_dict):
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
                                                          factor_probabilitites_dict, factors_values_dict)
                trip_generated_dict[leg_id] = factor_gen_dict
            extension = ticket.find(".//{http://www.vdv.de/trias}Extension")
            if extension is None:
                err_print('Ticket with id: ' + ticket_id.text + ' has not an Extension element!')
                continue
            # generate the factors with values into the extension element
            for code, val in factor_gen_dict.items():
                add_TSP_info(_code=code, _legid=leg_id, _value=val, _parent_el=extension, nsmap=NS)


def generate_examples(path_dict, modes_factors_dict, factor_probabilitites_dict, factors_values_dict,
                      probabilities=None, subfolders=True):
    if probabilities is None:
        probabilities = [0.25, 0.5, 0.75]
    for enriched_ver in range(len(probabilities)):
        # change the dictionary probabilities to the provided probabilities
        for key in factor_probabilitites_dict.keys():
            factor_probabilitites_dict[key] = probabilities[enriched_ver]
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
                    enrich_tickets_tripresult(trip_res, modes_factors_dict, factor_probabilitites_dict, factors_values_dict)
                # concatenate the path
                path = path_dict['generation_dir'] + path_dict['xml_name']
                # split into subfolders if the path are basic examples
                if subfolders:
                    path = path_dict['generation_dir'] + str(i) + "/" + path_dict['xml_name']
                objectify.deannotate(example_root, cleanup_namespaces=True)
                # write the tree into XML with concatenating the name
                etree.ElementTree(example_root).write(path + str(i) + '_v_' + str(enriched_ver + 1) + '.xml',
                                                      pretty_print=True, xml_declaration=True, encoding='UTF-8',
                                                      standalone='yes')
            else:
                err_print('File: ' + file + ' seems not like a valid file')


######################################################################################
# Code to run is below
#

example_root = etree.parse("../xml_examples/hacon_examples/r2r_example_4.xml", parser=parser).getroot()
for trip_res in example_root.findall(".//ns3:TripResult", NS):
    enrich_tickets_tripresult(trip_res, modes_factors_dict, factor_probabilitites_dict, factors_values_dict)


examples_dir = "../xml_examples/"

if not path.isdir(examples_dir):
    err_print(examples_dir + " is not a valid directory! Please create a valid directory or change its path.")
    exit()

# for all examples
# all_examples = {
#     'example_path': examples_dir + 'basic_examples/sing_mob_exmpl_',
#     'file_num': list(range(0, 11)),
#     'generation_dir': examples_dir + 'basic_examples_TSP/example_',
#     'xml_name': 'enriched_example_'
# }

hacon_examples = {
    'example_path': examples_dir + 'hacon_examples/r2r_example_',
    'file_num': list(range(1, 10)),
    # 'file_num': list(range(1,2)),
    'generation_dir': examples_dir + 'hacon_enriched_examples/',
    'xml_name': 'enriched_example_'
}

# for examples with RS data
rs_examples = {
    'example_path': examples_dir + 'RS_examples/rs_exmpl_',
    'file_num': [1, 3, 10],
    'generation_dir': examples_dir + 'RS_examples_TSP/',
    'xml_name': 'rs_tsp_example_'
}

factor_probability_values = [0.25, 0.5, 0.75]

# set seed
random.seed(123)

# generate TSP data
generate_examples(hacon_examples,
                  modes_factors_dict=modes_factors_dict,
                  factor_probabilitites_dict=factor_probabilitites_dict,
                  factors_values_dict=factors_values_dict,
                  probabilities=factor_probability_values,
                  subfolders=False)
# generate ridesharing TSP data
# generate_examples(rs_examples, factor_probability_values, subfolders=False)
