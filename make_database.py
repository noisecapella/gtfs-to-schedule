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
    out_file.write("CREATE TABLE trip_ids (id INTEGER PRIMARY KEY, trip_id STRING, route_id STRING);\n")
    count = 0
    with open(csv_path) as csv_file:
        reader = csv.reader(csv_file)

        header = make_index_map(next(reader))
        for row in reader:
            trip_id = row[header["trip_id"]]
            route_id = row[header["route_id"]]
            out_file.write("INSERT INTO trip_ids VALUES (%d, '%s', '%s');\n" % (count, trip_id, route_id))
            if trip_id in ret:
                raise Exception("Duplicate trip: %s" % trip_id)
            ret[trip_id] = count
            count += 1
    return ret

def read_stop_times_table(csv_path):
    # returns trip_id -> [(stop_id, arrival, departure), etc...]
    ret = defaultdict(list)

    with open(csv_path) as csv_file:
        reader = csv.reader(csv_file)

        header = make_index_map(next(reader))
        for row in reader:
            trip_id = row[header["trip_id"]]
            stop_id = row[header["stop_id"]]
            arrival_seconds = parse_time(row[header["arrival_time"]])
            departure_seconds = parse_time(row[header["departure_time"]])
            sequence = int(row[header["stop_sequence"]])

            m = ret[trip_id]
            if stop_id in m:
                raise Exception("Stop id %s specified twice for a given trip %s" % (stop_id, trip_id))
            tup = stop_id, sequence, arrival_seconds, departure_seconds
            m.append(tup)
    return ret


def compress_stop_times_table(stop_times):
    # stop_times is return value of read_stop_times_table
    # returns (arrivals_map, trip_id -> (seconds, Arrivals))
    # where arrivals_map is arrival_id -> Arrival

    ret = {}
    arrivals_map = {}
    arrivals_reverse_map = {}
    for trip_id, stop_lst in stop_times.items():
        min_seconds = 48 * 60 * 60
        for tup in stop_lst:
            _, _, arrival_seconds, depart_seconds = tup
            min_seconds = min(min_seconds, arrival_seconds, depart_seconds)
        new_lst = tuple([(tup[0], tup[1], tup[2] - min_seconds, tup[3] - min_seconds) for tup in stop_lst])
        if new_lst in arrivals_reverse_map:
            arrivals_id = arrivals_reverse_map[new_lst]
        else:
            arrivals_id = len(arrivals_map)
            arrivals_map[arrivals_id] = new_lst
            arrivals_reverse_map[new_lst] = arrivals_id
        ret[trip_id] = (arrivals_id, min_seconds)

    return ret, arrivals_map

def write_stop_times_table(out_file, stop_times, trip_id_map):
    out_file.write("CREATE TABLE stop_times (trip_id INTEGER, arrival_id INTEGER, offset INTEGER);\n")
    for trip_id, tup in stop_times.items():
        arrival_id, offset = tup
        out_file.write("INSERT INTO stop_times VALUES (%d, %d, %d);\n" % (
            trip_id_map[trip_id], arrival_id, offset
        ))

def write_arrivals_table(out_file, arrivals_map, stop_ids_map):
    out_file.write("CREATE TABLE arrivals (id INTEGER, sequence_id INTEGER,"
                   " stop_id INTEGER, arrival_seconds INTEGER);\n")
    for arrival_id, lst in arrivals_map.items():
        for stop_id, sequence, arrival_seconds, departure_seconds in lst:
            out_file.write("INSERT INTO arrivals VALUES (%d, %d, %d, %d);\n" % (
                arrival_id, sequence, stop_ids_map[stop_id], arrival_seconds
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
        stop_times = read_stop_times_table(os.path.join(args.path, "stop_times.txt"))
        compressed_stop_times, arrivals_map = compress_stop_times_table(stop_times)
        write_stop_times_table(f, compressed_stop_times, trip_ids_map)
        write_arrivals_table(f, arrivals_map, stop_ids_map)

        f.write("END TRANSACTION;\n")

if __name__ == "__main__":
    main()







