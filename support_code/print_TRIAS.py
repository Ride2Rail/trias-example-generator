from lxml import etree
from sys import stdout, stdin
import os



def print_TRIAS(FileTRIAS):
    # used namespaces
    print("File = ", FileTRIAS)
    NS3 = {'ns3': "http://www.vdv.de/trias", 'coactive': 'http://shift2rail.org/project/coactive'}

    parser         = etree.XMLParser(remove_blank_text=True, recover=True, encoding='utf-8')
    trias_big_root = etree.parse(FileTRIAS, parser=parser).getroot()

    # find all trips
    trip_list = trias_big_root.findall(".//ns3:Trip", NS3)

    # process trips one by one
    trip_i = 1
    for trip in trip_list:
        print("______________________________________")
        print("Trip: ", trip_i)
        # find all trip legs in a given trip
        trip_legs_list = trip.findall(".//ns3:TripLeg", NS3)
        trip_leg_i = 1
        for trip_leg in trip_legs_list:
            print("\t ******** Trip Leg:", trip_leg_i,"**********")
            # print("\t**************")
            for child in trip_leg:
                # TimedLeg
                if child.tag == "{http://www.vdv.de/trias}TimedLeg":
                    # extract from LegBoard info out the LocationName and Time
                    for child2 in child:
                        if child2.tag == "{http://www.vdv.de/trias}LegBoard":
                            for child3 in child2:
                                if child3.tag == "{http://www.vdv.de/trias}StopPointName":
                                    for child4 in child3:
                                        if child4.tag == "{http://www.vdv.de/trias}Text":
                                            print("\t Start: ", child4.text)
                                if child3.tag == "{http://www.vdv.de/trias}ServiceDeparture":
                                    for child4 in child3:
                                        if child4.tag == "{http://www.vdv.de/trias}TimetabledTime":
                                            print("\t Start Time: ", child4.text)
                    # extract from LegAlight info out the LocationName and Time
                    for child2 in child:
                        if child2.tag == "{http://www.vdv.de/trias}LegAlight":
                            for child3 in child2:
                                if child3.tag == "{http://www.vdv.de/trias}StopPointName":
                                    for child4 in child3:
                                        if child4.tag == "{http://www.vdv.de/trias}Text":
                                            print("\t End: ", child4.text)
                                if child3.tag == "{http://www.vdv.de/trias}ServiceArrival":
                                    for child4 in child3:
                                        if child4.tag == "{http://www.vdv.de/trias}TimetabledTime":
                                            print("\t End Time: ", child4.text)
                    # extract from Service Mode info
                    for child2 in child:
                        if child2.tag == "{http://www.vdv.de/trias}Service":
                            for child3 in child2:
                                if child3.tag == "{http://www.vdv.de/trias}ServiceSection":
                                    for child4 in child3:
                                        if child4.tag == "{http://www.vdv.de/trias}Mode":
                                            for child5 in child4:
                                                if child5.tag == "{http://www.vdv.de/trias}PtMode":
                                                    print("\t Mode: ", child5.text)

                # Continuous Leg
                if child.tag == "{http://www.vdv.de/trias}ContinuousLeg":
                    # extract from LegStart info out the LocationName and Time
                    for child2 in child:
                        if child2.tag == "{http://www.vdv.de/trias}LegStart":
                            for child3 in child2:
                                if child3.tag == "{http://www.vdv.de/trias}LocationName":
                                    for child4 in child3:
                                        if child4.tag == "{http://www.vdv.de/trias}Text":
                                            print("\t Start: ", child4.text)
                        if child2.tag == "{http://www.vdv.de/trias}TimeWindowStart":
                            print("\t Start Time: ", child2.text)
                    # extract from LegEnd info out the LocationName and Time
                    for child2 in child:
                        if child2.tag == "{http://www.vdv.de/trias}LegEnd":
                            for child3 in child2:
                                if child3.tag == "{http://www.vdv.de/trias}LocationName":
                                    for child4 in child3:
                                        if child4.tag == "{http://www.vdv.de/trias}Text":
                                            print("\t Start: ", child4.text)
                        if child2.tag == "{http://www.vdv.de/trias}TimeWindowEnd":
                            print("\t Start Time: ", child2.text)
                    # extract from Service Mode info
                    for child2 in child:
                        if child2.tag == "{http://www.vdv.de/trias}Service":
                            for child3 in child2:
                                if child3.tag == "{http://www.vdv.de/IndividualMode}":
                                    print("\t Mode: ", child3.text)
            trip_leg_i = trip_leg_i + 1
        trip_i = trip_i + 1
    return 0

directory = "/home/lubos/Downloads/20210518-trias_r2r_examples"

files = os.listdir(directory)
for file in files:
    print("****************** File = " + file + "******************" )
    print_TRIAS(directory +"/" +file)
    print("************************************")