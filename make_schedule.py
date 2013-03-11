#!/usr/bin/env python

import argparse
import os
import csv
from collections import namedtuple

def read_map(path, key):
    ret = {}

    with open(path) as f:
        reader = csv.DictReader(f)

        for row in reader:
            ret[row[key]] = row

    return ret

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

def parse(path):
    print "reading routes..."
    routes = read_map(os.path.join(path, "routes.txt"), "route_id")
    print "reading stops..."
    stops = read_map(os.path.join(path, "stops.txt"), "stop_id")
    print "reading trips..."
    trips = read_map(os.path.join(path, "trips.txt"), "trip_id")

    print "reticulating splines..."
    # mapping of (stop, direction) to list of (start_time, increment, count)
    schedule = {}

    with open(os.path.join(path, "stop_times.txt")) as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["stop_sequence"] != "1":
                continue
            key = row["stop_id"], trips[row["trip_id"]]["direction_id"]

            lst = schedule.get(key, [])
            schedule[key] = lst

            arrival_time = parse_time(row["arrival_time"])
            if len(lst) >= 1:
                start_time, inc, count = lst[-1]
                diff = arrival_time - start_time
                if inc == 0:
                    lst[-1] = start_time, diff, 1
                elif diff % inc == 0:
                    lst[-1] = start_time, inc, count+1
                else:
                    lst.append((arrival_time, 0, 0))
            else:
                lst.append((arrival_time, 0, 0))
            

    return schedule


def main():
    parser = argparse.ArgumentParser(description='Parses GTFS data into general schedule')
    parser.add_argument('path', help='Path of directory containing GTFS data')

    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print("%s is not a valid directory" % args.path)
        exit(-1)

    schedule = parse(args.path)

    print schedule

if __name__ == "__main__":
    main()
