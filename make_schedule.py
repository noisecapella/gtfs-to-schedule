#!/usr/bin/env python

import argparse
import os
import csv
from collections import defaultdict

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

def time_to_string(time):
    """Seconds from beginning of day to string"""

    hour = time / (60*60)
    time -= hour*60*60

    minute = time/60
    time -= minute*60

    second = time

    return "%02d:%02d:%02d" % (hour,minute,second)

class Schedule:
    """A compressed schedule"""
    def __init__(self):
        self.pieces = []
        self.trip = None

    def add_time(self, arrival_time):
        i = 0
        for piece in self.pieces:
            start_time, inc, count = piece

            if arrival_time <= start_time:
                i -= 1
                break
            
            i += 1

        if i < 0:
            self.pieces.insert(0, (arrival_time, 0, 0))
        elif i >= len(self.pieces):
            self.pieces.append((arrival_time, 0, 0))
        else:
            piece = self.pieces[i]
            start_time, inc, count = piece
            
            diff = arrival_time - start_time
            if inc == 0:
                self.pieces[i] = start_time, diff, 1
            elif diff % inc == 0:
                self.pieces[i] = start_time, inc, count+1
            else:
                self.pieces.insert(i+1, (arrival_time, 0, 0))

    def __str__(self):
        ret = ""

        for piece in self.pieces:
            start_time, inc, count = piece
            ret += "        start at %s, repeat every %d minutes %d times\n" % (time_to_string(start_time), inc/60, count) 

        return ret

def read_map(path, key):
    ret = {}

    with open(path) as f:
        reader = csv.DictReader(f)

        for row in reader:
            ret[row[key]] = row

    return ret

def parse(path):
    print "reading routes..."
    routes = read_map(os.path.join(path, "routes.txt"), "route_id")
    print "reading stops..."
    stops = read_map(os.path.join(path, "stops.txt"), "stop_id")
    print "reading trips..."
    trips = read_map(os.path.join(path, "trips.txt"), "trip_id")
    print "reading calendar..."
    calendar = read_map(os.path.join(path, "calendar.txt"), "service_id")

    calendar_map = defaultdict(dict)
    for key, value in calendar.iteritems():
        calendar_map[key] = (int(value["monday"]), int(value["tuesday"]), int(value["wednesday"]), int(value["thursday"]), int(value["friday"]), int(value["saturday"]), int(value["sunday"]))
    

    print "reticulating splines..."
    # mapping of (stop, direction) to list of (start_time, increment, count)
    schedule = defaultdict(Schedule)

    with open(os.path.join(path, "stop_times.txt")) as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["stop_sequence"] != "1":
                continue
            trip = row["trip_id"]
            key = row["stop_id"], trips[trip]["trip_headsign"], trips[trip]["route_id"], calendar_map[trips[trip]["service_id"]]

            sched = schedule[key]
            sched.trip = trip

            arrival_time = parse_time(row["arrival_time"])
            sched.add_time(arrival_time)
        
    # mapping of route to list of mappings from directions to a compressed schedule
    ret = defaultdict(lambda: defaultdict(dict))

    for key, sched in schedule.iteritems():
        stop, direction, route, service = key

        ret[route][direction][service] = sched

    return ret

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

    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print("%s is not a valid directory" % args.path)
        exit(-1)

    schedule = parse(args.path)

    for route, direction_map in schedule.iteritems():
        print "Route: %s" % route
        for direction, service_map in direction_map.iteritems():
            print "    Direction: %s" % direction
            for service, sched in service_map.iteritems():
                print "    Service: %s" % weekdays_to_name(service)
                print "    Schedule: %s" % str(sched)

if __name__ == "__main__":
    main()
