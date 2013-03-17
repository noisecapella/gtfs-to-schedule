#!/usr/bin/env python

import argparse
import os
import csv
from collections import defaultdict, OrderedDict
from time import strptime
from datetime import date

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
    def __init__(self):
        self.schedules = {}
        self.stops = OrderedDict()

    def add_time(self, arrival_time, stop):
        if stop not in self.stops:
            self.stops[stop] = True
            self.schedules[stop] = StopSchedule()

        self.schedules[stop].add_time(arrival_time)

    def compress(self):
        # if schedule is exactly some number of minutes different from previous
        # replace with number

        prev_sched = None
        for stop, _ in self.stops.iteritems():
            current_sched = self.schedules[stop]
            current_sched.compress()
            if prev_sched:
                diff = prev_sched.diff(current_sched)
                if diff != None:
                    self.schedules[stop] = diff

            prev_sched = current_sched

    def __str__(self):
        ret = ""

        for stop, _ in self.stops.iteritems():
            current_sched = self.schedules[stop]
            if type(current_sched) == int:
                if current_sched % 60 == 0:
                    ret += "     whole schedules is exactly %d minutes from previous\n" % (current_sched/60)
                else:
                    ret += "     whole schedules is exactly %d seconds from previous\n" % (current_sched)
            else:
                ret += str(current_sched)

        return ret

            
class StopSchedule:
    """A compressed schedule for a stop"""
    def __init__(self):
        self.pieces = []
        self.trip = None

    def diff(self, next_sched):
        if len(next_sched.pieces) != len(self.pieces):
            return None

        current_diff = None
        for i, piece in enumerate(self.pieces):
            start_time, inc, count = piece

            next_start_time, next_inc, next_count = next_sched.pieces[i]

            if next_inc == inc and next_count == count:
                diff = next_start_time - start_time
                if current_diff == None:
                    current_diff = diff
                elif current_diff != diff:
                    return None
        return current_diff

    def add_time(self, arrival_time):
        i = 0
        for piece in self.pieces:
            start_time, inc, count = piece

            if arrival_time < start_time:
                break
            else:
                i += 1
        self.pieces.insert(i, (arrival_time, 0, 0))

    def compress(self):
        new_pieces = []

        for piece in self.pieces:
            start_time, inc, count = piece
            if len(new_pieces) == 0:
                new_pieces.append(piece)
            else:
                new_start_time, new_inc, new_count = new_pieces[-1]
                diff = start_time - new_start_time
                if diff == 0:
                    pass
                elif new_count == 0:
                    new_pieces[-1] = new_start_time, diff, 1
                elif diff % new_inc == 0:
                    new_pieces[-1] = new_start_time, new_inc, new_count + 1
                else:
                    new_pieces.append(piece)

        self.pieces = new_pieces

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

def make_days(calendar, service):
    row = calendar[service]
    return (int(row["monday"]), int(row["tuesday"]), int(row["wednesday"]), int(row["thursday"]), int(row["friday"]), int(row["saturday"]), int(row["sunday"]))

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
    for route, direction_map in ret_with_service.iteritems():
        for direction, service_map in direction_map.iteritems():
            # mapping of weekdays to service
            m = {}
            for service, _ in service_map.iteritems():
                # make sure service we choose is the one of maximum duration
                row = calendar[service]
                tup = make_days(calendar, service)

                if tup not in m:
                    m[tup] = service
                elif duration(calendar, m[tup]) < duration(calendar, service):
                    m[tup] = service
                #else leave the old one there

            for service, sched in service_map.iteritems():
                tup = make_days(calendar, service)
                if m[tup] == service:
                    ret_with_stops[route][direction][weekdays_to_name(tup)] = sched
    return ret_with_stops

def parse(path):
    print "reading routes..."
    routes = read_map(os.path.join(path, "routes.txt"), "route_id")
    print "reading stops..."
    stops = read_map(os.path.join(path, "stops.txt"), "stop_id")
    print "reading trips..."
    trips = read_map(os.path.join(path, "trips.txt"), "trip_id")
    print "reading calendar..."
    calendar = read_map(os.path.join(path, "calendar.txt"), "service_id")

    

    print "reticulating splines..."
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
        
    # mapping of route to list of mappings from directions to a compressed schedule
    ret_with_service = defaultdict(lambda: defaultdict(dict))

    for key, sched in schedule.iteritems():
        direction, route, service = key

        ret_with_service[route][direction][service] = sched

        sched.compress()

    ret = convert_service_to_weekdays(ret_with_service, calendar)

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
                print "    Service: %s" % service
                print "    Schedule: %s" % str(sched)

if __name__ == "__main__":
    main()
