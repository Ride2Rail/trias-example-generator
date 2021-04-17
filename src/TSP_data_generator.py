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
from copy import deepcopy

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
    'likelihood_of_delays': 0.1,
    'last_minute_changes': 0.1,
    'frequency_of_service': 0.1,
    'user_feedback': 0.1,
    'cleanliness': 0.1,
    'seating_quality': 0.1,
    'space_available': 0.1,
    'silence_area_presence': 0.1,
    'privacy_level': 0.1,
    'bike_on_board': 0.1,
    'business_area_presence': 0.1,
    'internet_availability': 0.1,
    'plugs_or_charging_points': 0.1,
    'number_of_persons_sharing_trip': 0.1,
    'shared_with_other_passengers': 0.1,
    'safety_features': 0.1,
    'vehicle_age': 0.1,
    'passenger_feedback': 0.1,
    'certified_driver': 0.1,
    'driver_license_issue_date': 0.1,
    'repeated_trip': 0.1
}

# increase the probability to 0.5
for k in factor_probabilitites_dict.keys():
    factor_probabilitites_dict[k] = 0.5

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

def err_print(text):
    print(text, file=sys.stderr)


# creates a subelement with given text
def create_SubElement(_parent, _tag, attrib={}, _text=None, nsmap=None, **_extra):
    result = etree.SubElement(_parent, _tag, attrib, nsmap, **_extra)
    result.text = _text
    return result


# this code adds tsp_info to an element
def add_TSP_info(_code=None, _legid=None, _value=None, _parent_el=None, nsmap=None, attrib={}, **_extra):
    parent_elem = create_SubElement(_parent_el, '{http://shift2rail.org/project/coactive}OfferItemContext', nsmap=nsmap)
    if _legid is not None:
        _code = _code + ":" + str(_legid)
    create_SubElement(parent_elem, "{http://shift2rail.org/project/coactive}Code", _text=_code, nsmap=nsmap)
    create_SubElement(parent_elem, "{http://shift2rail.org/project/coactive}Value", _text=str(_value), nsmap=nsmap)
    return parent_elem

# appends user id and if needed changes it to "Traveller"
def change_append_user_id(gg_parent, text_append):
    for el in gg_parent.findall(".//coactive:UserId", NS):
        if el.getparent().tag == "{http://shift2rail.org/project/coactive}User" or \
                el.getparent().tag == "{http://shift2rail.org/project/coactive}Traveller":
            el.text = el.text + text_append


def get_mode(trip_res, legid):
    # find the tripleg by the leg id
    tripleg = trip_res.xpath(".//ns3:LegId[text() = '" + legid + "']", namespaces=NS)[0] \
        .getparent()
    mode = tripleg.findall(".//ns3:Mode/ns3:PtMode", NS)
    if mode:
        return mode[0]
    else:
        walk = tripleg.findall(".//ns3:Service/ns3:IndividualMode", NS)
        if walk:
            return walk[0]
        else:
            err_print('mode ' + mode + ' not found')
            return 0



# if the time is negative add it to unix time
def datetime_to_unix(time_in_seconds):
    if time_in_seconds < 0:
        return datetime(1970, 1, 1) + timedelta(seconds=time_in_seconds)
    else:
        return datetime.utcfromtimestamp(time_in_seconds)


# helping function for random date generation
# inspired by
# https://stackoverflow.com/questions/553303/generate-a-random-date-between-two-other-dates
def my_str_time_prop(start, end, prop, format, ):
    # substraction is for the case if the date is before unix time
    stime = (datetime.strptime(start, format) - datetime(1970, 1, 1)).total_seconds()
    etime = (datetime.strptime(end, format) - datetime(1970, 1, 1)).total_seconds()
    ptime = stime + prop * (etime - stime)
    # for whole seconds
    ptime = round(ptime)
    form_time = datetime_to_unix(ptime)
    return form_time.strftime(format)[0:-4] + "Z"

# generate random date
def random_date(start, end, prop, format='%Y-%m-%dT%H:%M:%S.%fZ'):
    return my_str_time_prop(start, end, prop, format)


def generate_value(val_dict, factor):
    i_list = val_dict[factor]
    if i_list[0] == 'real':
        return round(random.uniform(i_list[1], i_list[2]), 2)
    elif i_list[0] == 'int':
        return random.randint(i_list[1], i_list[2])
    elif i_list[0] == 'date':
        return random_date(i_list[1], i_list[2], random.random())
    else:
        err_print('unsupported type of date')


# time.mktime(time.strptime('1980-1-1T00:00:00.000Z', '%Y-%m-%dT%H:%M:%S.%fZ'))

# enricher for trip result
def enrich_trip_result(trip_result,
                       modes_factors_dict=modes_factors_dict,
                       factor_probabilitites_dict=factor_probabilitites_dict,
                       factors_values_dict=factors_values_dict):
    for leg in trip_result.findall('.//ns3:TripLeg', NS):
        # check if it is not a walk
        transp_mode = leg.find(".//ns3:IndividualMode", NS)
        if transp_mode is not None:
            transp_mode = transp_mode.text
            if transp_mode == 'walk':
                continue
        legid = leg[0].text
        if transp_mode is None:
            transp_mode = leg.find(".//ns3:PtMode", namespaces=NS).text
        # if the mode is unknown skip the trip_leg
        if transp_mode == "unknown":
            continue
        # generate the factor values and add them to dictionary
        tmp_fact_val_dict = {}
        for factor in modes_factors_dict[transp_mode]:
            if random.uniform(0, 1) < factor_probabilitites_dict[factor]:
                tmp_fact_val_dict[factor] = generate_value(factors_values_dict, factor)
        # find assigned travelEpisodeId
        trip_res = leg.getparent().getparent()
        if trip_res.tag != "{http://www.vdv.de/trias}TripResult":
            err_print('Parent of tripleg with legid: ' + legid + ' is not a TripResult!')
            continue
        offerid = trip_res.xpath(".//coactive:TravelEpisodeId[text() = '" + legid + "']",
                                 namespaces=NS)[0]
        # find extension
        extension = offerid.getparent().getparent()
        # check if extension is really an extension
        if extension.tag != '{http://www.vdv.de/trias}Extension':
            err_print('Element under legid:' + legid + 'is not an extension!')
            continue
        # add generated data to the leg
        for code, val in tmp_fact_val_dict.items():
            add_TSP_info(_code=code, _legid=legid, _value=val, _parent_el=extension, nsmap=NS)
    return True


def generate_examples(path_dict, probabilities=[0.25, 0.5, 0.75]):
    for enriched_ver in range(1, 4):
        for key in factor_probabilitites_dict.keys():
            factor_probabilitites_dict[key] = probabilities[enriched_ver - 1]
        # append file name to the end of the string
        for i in path_dict['file_num']:
            file = path_dict['example_path'] + str(i) + '.xml'
            if os.path.isfile(file):
                example_root = etree.parse(file, parser=parser).getroot()
                change_append_user_id(example_root, '-v-' + str(enriched_ver))
                for trip_res in example_root.findall(".//ns3:TripResult", NS):
                    enrich_trip_result(trip_res)
                path = path_dict['generation_dir'] + path_dict['xml_name']
                if path_dict['generation_dir'] == '../output_files/basic_examples_TSP/example_':
                    path = path_dict['generation_dir'] + str(i) + "/" + path_dict['xml_name']
                etree.ElementTree(example_root).write(path + str(i) + '_v_' + str(enriched_ver) + '.xml',
                                                      pretty_print=True, xml_declaration=True, encoding='UTF-8',
                                                      standalone='yes')
            else:
                err_print('File' + file + 'seems not like a valid file')


######################################################################################
# Code to run is below
#


# for all examples
all_examples = {
    'example_path': '../xml_examples/basic_examples/sing_mob_exmpl_',
    'file_num': list(range(0, 11)),
    'generation_dir': '../xml_examples/basic_examples_TSP/example_',
    'xml_name': 'enriched_example_'
}

# for examples with RS data
rs_examples = {
    'example_path': '../xml_examples/RS_examples_/rs_exmpl_',
    'file_num': [1, 3, 10],
    'generation_dir': '../xml_examples/RS_examples_TSP/',
    'xml_name': 'rs_tsp_example_'
}

factor_probability_values = [0.25, 0.5, 0.75]

# set seed
random.seed(123)

# generate TSP data
generate_examples(all_examples, factor_probability_values)
# generate ridesharing TSP data
generate_examples(rs_examples, factor_probability_values)

# inverse map of factors for each transport mode
# imap = {
#     'bus': ['likelihood_of_delays', 'last_minute_changes', 'frequency_of_service', 'user_feedback', 'cleanliness',
#             'seating_quality', 'space_available', 'likelihood_of_delays', 'last_minute_changes', 'frequency_of_service',
#             'user_feedback', 'cleanliness', 'seating_quality', 'space_available', 'privacy_level', 'bike_on_board',
#             'internet_availability', 'plugs_or_charging_points', 'safety_features', 'passenger_feedback'],
#     'tram': ['likelihood_of_delays', 'last_minute_changes', 'frequency_of_service', 'user_feedback', 'cleanliness',
#              'seating_quality', 'space_available', 'likelihood_of_delays', 'last_minute_changes', 'frequency_of_service',
#              'user_feedback', 'cleanliness', 'seating_quality', 'space_available', 'privacy_level', 'bike_on_board',
#              'internet_availability', 'plugs_or_charging_points', 'safety_features', 'passenger_feedback'],
#     'rail': ['likelihood_of_delays', 'last_minute_changes', 'frequency_of_service', 'user_feedback', 'cleanliness',
#              'seating_quality', 'space_available', 'likelihood_of_delays', 'last_minute_changes', 'frequency_of_service',
#              'user_feedback', 'cleanliness', 'seating_quality', 'space_available', 'silence_area_presence',
#              'privacy_level', 'bike_on_board', 'business_area_presence', 'internet_availability',
#              'plugs_or_charging_points', 'safety_features', 'passenger_feedback'],
#     'metro': ['likelihood_of_delays', 'last_minute_changes', 'frequency_of_service', 'user_feedback', 'cleanliness',
#               'seating_quality', 'space_available', 'likelihood_of_delays', 'last_minute_changes',
#               'frequency_of_service', 'user_feedback', 'cleanliness', 'seating_quality', 'space_available',
#               'privacy_level', 'bike_on_board', 'internet_availability', 'plugs_or_charging_points',
#               'safety_features', 'passenger_feedback'],
#     'air': ['likelihood_of_delays', 'last_minute_changes', 'frequency_of_service', 'user_feedback', 'cleanliness',
#             'seating_quality', 'space_available', 'likelihood_of_delays', 'last_minute_changes', 'frequency_of_service',
#             'user_feedback', 'cleanliness', 'seating_quality', 'space_available', 'privacy_level', 'bike_on_board',
#             'business_area_presence', 'internet_availability', 'plugs_or_charging_points', 'safety_features', 'passenger_feedback'],
#     'urbanRail': ['likelihood_of_delays', 'last_minute_changes', 'frequency_of_service', 'user_feedback', 'cleanliness',
#                   'seating_quality', 'space_available', 'likelihood_of_delays', 'last_minute_changes',
#                   'frequency_of_service', 'user_feedback', 'cleanliness', 'seating_quality', 'space_available',
#                   'privacy_level', 'bike_on_board', 'internet_availability', 'plugs_or_charging_points',
#                   'safety_features', 'passenger_feedback'],
#     'others-drive-car': ['likelihood_of_delays', 'last_minute_changes', 'frequency_of_service', 'user_feedback',
#                      'cleanliness', 'seating_quality', 'space_available', 'likelihood_of_delays', 'last_minute_changes',
#                      'frequency_of_service', 'user_feedback', 'cleanliness', 'seating_quality', 'space_available',
#                      'privacy_level', 'bike_on_board', 'internet_availability', 'plugs_or_charging_points',
#                      'number_of_persons_sharing_trip', 'shared_with_other_passengers', 'safety_features', 'vehicle_age',
#                      'passenger_feedback', 'certified_driver', 'driver_license_issue_date', 'repeated_trip']
# }
