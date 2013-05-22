#!/usr/bin/env python3

import argparse
import os
import csv
from collections import defaultdict, OrderedDict
from time import strptime
from datetime import date

from schedules import (
    Schedule,
    StopSchedule,
)

def parse_time(s):
    """Returns seconds from beginning of day. May go into tomorrow slightly"""
    hour, minute, second = s.split(":")
    hour = int(hour)
    minute = int(minute)
    second = int(second)

    if hour >= 24:
        day = 1
        hour -= 24
    else:
        day = 0

    return second + 60*minute + 60*60*hour + 24*60*60*day


def read_map(path, key):
    ret = {}

    with open(path) as f:
        reader = csv.DictReader(f)

        for row in reader:
            ret[row[key]] = row

    return ret

def make_days(calendar, service):
    row = calendar[service]
    return int(row["monday"]), int(row["tuesday"]), int(row["wednesday"]), int(row["thursday"]), int(row["friday"]), int(row["saturday"]), int(row["sunday"])

def make_days_hash(arr):
    """Inputs array of seven days, starting with Monday, where value is 1 or 0. Returns integer of equivalent bits"""
    ret = 0
    for i in range(len(arr)):
        if arr[i]:
            ret |= 2**i

    return ret

def duration(calendar, service):
    row = calendar[service]

    end_tup = strptime(row['end_date'], '%Y%m%d')
    start_tup = strptime(row['start_date'], '%Y%m%d')

    end = date(end_tup[0], end_tup[1], end_tup[2])
    start = date(start_tup[0], start_tup[1], start_tup[2])
    return (end-start).days

def convert_service_to_weekdays(ret_with_service, calendar):
    """this block of code converts service to a tuple of weekdays"""



    # mapping of route to map of direction to sched
    ret_with_stops = defaultdict(lambda: defaultdict(dict))
    for route, direction_map in ret_with_service.items():
        for direction, service_map in direction_map.items():
            # mapping of weekdays to service
            m = {}
            for service, _ in service_map.items():
                # make sure service we choose is the one of maximum duration
                row = calendar[service]
                tup = make_days(calendar, service)

                if tup not in m:
                    m[tup] = service
                elif duration(calendar, m[tup]) < duration(calendar, service):
                    m[tup] = service
                #else leave the old one there

            for service, sched in service_map.items():
                tup = make_days(calendar, service)
                if m[tup] == service:
                    ret_with_stops[route][direction][weekdays_to_name(tup)] = sched
    return ret_with_stops

def parse(path):
    print("reading routes...")
    routes = read_map(os.path.join(path, "routes.txt"), "route_id")
    print("reading stops...")
    stops = read_map(os.path.join(path, "stops.txt"), "stop_id")
    print("reading trips...")
    trips = read_map(os.path.join(path, "trips.txt"), "trip_id")
    print("reading calendar...")
    calendar = read_map(os.path.join(path, "calendar.txt"), "service_id")

    

    print("reticulating splines...")
    # mapping of (stop, direction) to list of (start_time, increment, count)
    schedule = defaultdict(Schedule)

    with open(os.path.join(path, "stop_times.txt")) as f:
        reader = csv.DictReader(f)

        for row in reader:
            trip = row["trip_id"]
            key = trips[trip]["trip_headsign"], trips[trip]["route_id"], trips[trip]["service_id"]

            sched = schedule[key]
            sched.trip = trip

            arrival_time = parse_time(row["arrival_time"])
            sched.add_time(arrival_time, row["stop_id"])
        
    # mapping route -> direction -> service -> sched
    ret_with_service = defaultdict(lambda: defaultdict(dict))

    for key, sched in schedule.items():
        direction, route, service = key

        ret_with_service[route][direction][service] = sched

        sched.compress()

    #ret = convert_service_to_weekdays(ret_with_service, calendar)

    return ret_with_service, trips, calendar

def weekdays_to_name(weekdays):
    all_weekdays = weekdays[0] and weekdays[1] and weekdays[2] and weekdays[3] and weekdays[4]

    if all_weekdays:
        return "All weekdays"

    else:
        array = []
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, value in enumerate(weekdays):
            if value:
                array.append(days[i])

        return ", ".join(array)

def main():
    parser = argparse.ArgumentParser(description='Parses GTFS data into general schedule')
    parser.add_argument('path', help='Path of directory containing GTFS data')
    parser.add_argument('output_file', help='File to output schedule to')

    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print("%s is not a valid directory" % args.path)
        exit(-1)

    if os.path.exists(args.output_file):
        print("Output file %s exists, please delete and try again if this is what you want" % args.output_file)
        exit(-1)

    with open(args.output_file, "w") as f:
        # test that we can write
        f.write("\n")

        schedule, trips, calendar = parse(args.path)

        for route, direction_map in schedule.items():
            f.write("Route: %s\n" % route)
            for direction, service_map in direction_map.items():
                f.write("    Direction: %s\n" % direction)
                for service, sched in service_map.items():
                    f.write("    Service: %s\n" % service)
                    f.write("    Schedule: %s\n" % str(sched))

if __name__ == "__main__":
    main()
