#!/usr/bin/env python3

from make_schedule import parse
import argparse
import os
import csv
from collections import defaultdict

from box import Box

from make_schedule import (
    make_days,
    make_days_hash,
    parse_time,
    )

from schedules import (
    StopSchedule,
    Schedule,

)

def escaped(s):
    return s.replace("'", "''")


def print_stop_times_table(f, stop_times):
    for trip_id, stop_times_map in stop_times.items():
        for stop_id, times_tuple in stop_times_map.items():
            arrival_seconds, depart_seconds = times_tuple



def make_index_map(array):
    ret = {}
    for i, item in enumerate(array):
        ret[item] = i
    return ret

def write_stop_ids_table(out_file, csv_path):
    ret = {}
    out_file.write("CREATE TABLE stop_ids (id INTEGER PRIMARY KEY, stop_id STRING);\n")
    count = 0
    with open(csv_path) as csv_file:
        reader = csv.reader(csv_file)

        header = make_index_map(next(reader))
        for row in reader:
            stop_id = row[header["stop_id"]]
            out_file.write("INSERT INTO stop_ids VALUES (%d, '%s');\n" % (count, stop_id))
            if stop_id in ret:
                raise Exception("Duplicate stop: %s" % stop_id)
            ret[stop_id] = count
            count += 1
    return ret

def write_trip_ids_table(out_file, csv_path):
    ret = {}
    out_file.write("CREATE TABLE trip_ids (id INTEGER PRIMARY KEY, trip_id STRING);\n")
    count = 0
    with open(csv_path) as csv_file:
        reader = csv.reader(csv_file)

        header = make_index_map(next(reader))
        for row in reader:
            trip_id = row[header["trip_id"]]
            out_file.write("INSERT INTO trip_ids VALUES (%d, '%s');\n" % (count, trip_id))
            if trip_id in ret:
                raise Exception("Duplicate trip: %s" % trip_id)
            ret[trip_id] = count
            count += 1
    return ret

def write_stop_times_table(out_file, csv_path, stop_id_map, trip_id_map):
    out_file.write("CREATE TABLE stop_times (trip_id INTEGER, stop_id INTEGER, "
                   "arrival_seconds INTEGER, depart_seconds INTEGER);\n")
    with open(csv_path) as csv_file:
        reader = csv.reader(csv_file)

        header = make_index_map(next(reader))
        for row in reader:
            trip_id = row[header["trip_id"]]
            stop_id = row[header["stop_id"]]
            arrival_seconds = parse_time(row[header["arrival_time"]])
            departure_seconds = parse_time(row[header["departure_time"]])

            out_file.write("INSERT INTO stop_times VALUES (%d, %d, %d, %d);\n" % (
                trip_id_map[trip_id], stop_id_map[stop_id], arrival_seconds, departure_seconds
            ))


def main():
    parser = argparse.ArgumentParser(description='Parses GTFS data into general schedule')
    parser.add_argument('path', help='Path of directory containing GTFS data')
    parser.add_argument('output_file', help='File to write SQL output to')

    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print("%s is not a valid directory" % args.path)
        exit(-1)

    if os.path.exists(args.output_file):
        print("Output file %s already exists, delete it and try again" % args.output_file)
        exit(-1)

    with open(args.output_file, "w") as f:
        f.write("BEGIN TRANSACTION;\n")
        trip_ids_map = write_trip_ids_table(f, os.path.join(args.path, "trips.txt"))
        stop_ids_map = write_stop_ids_table(f, os.path.join(args.path, "stops.txt"))
        write_stop_times_table(f, os.path.join(args.path, "stop_times.txt"), stop_ids_map, trip_ids_map)

        f.write("END TRANSACTION;\n")

if __name__ == "__main__":
    main()







