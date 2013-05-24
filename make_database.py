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
    """this iterates through stop_times,
    which is trip_id -> list of (stop_id, sequence, arrival_seconds, depart_seconds)

    It looks for a set of times which are all the same difference from each other and stores that
    in arrivals_map. Many trips may use the same arrivals_map. Stops are stored

    it returns three maps:
    ret is trip_id -> arrivals_id, stop_list_id, offset
    """

    ret = {}
    arrivals_map = {}
    arrivals_reverse_map = {}
    stops_map = {}
    stops_reverse_map = {}


    for trip_id, stop_lst in stop_times.items():
        min_seconds = 48 * 60 * 60
        for tup in stop_lst:
            stop_id, sequence, arrival_seconds, depart_seconds = tup
            min_seconds = min(min_seconds, arrival_seconds, depart_seconds)
        new_arrivals_lst = tuple([(tup[2] - min_seconds, tup[3] - min_seconds) for tup in stop_lst])
        new_stop_lst = tuple([(tup[0], tup[1]) for tup in stop_lst])
        if new_arrivals_lst in arrivals_reverse_map:
            arrivals_id = arrivals_reverse_map[new_arrivals_lst]
        else:
            arrivals_id = len(arrivals_map)
            arrivals_map[arrivals_id] = new_arrivals_lst
            arrivals_reverse_map[new_arrivals_lst] = arrivals_id

        if new_stop_lst in stops_reverse_map:
            stop_list_id = stops_reverse_map[new_stop_lst]
        else:
            stop_list_id = len(stops_map)
            stops_map[stop_list_id] = new_stop_lst
            stops_reverse_map[new_stop_lst] = stop_list_id

        ret[trip_id] = (arrivals_id, stop_list_id, min_seconds)

    return ret, arrivals_map, stops_map

def write_stop_times_table(out_file, stop_times, trip_id_map):
    out_file.write("CREATE TABLE stop_times (trip_id INTEGER, arrival_id INTEGER,"
                   " stop_list_id INTEGER, offset INTEGER);\n")
    for trip_id, tup in stop_times.items():
        arrival_id, stop_list_id, offset = tup
        out_file.write("INSERT INTO stop_times VALUES (%d, %d, %d, %d);\n" % (
            trip_id_map[trip_id], arrival_id, stop_list_id, offset
        ))

def write_arrivals_table(out_file, arrivals_map):
    out_file.write("CREATE TABLE arrivals (id INTEGER PRIMARY KEY, blob STRING);\n")
    for arrival_id, lst in arrivals_map.items():
        box = Box()
        box.add_short(len(lst))

        for arrival_seconds, departure_seconds in lst:
            if arrival_seconds % 60 != 0:
                raise Exception("arrival_seconds % 60 != 0")
            if (arrival_seconds / 60) > 0xffff or arrival_seconds < 0:
                raise Exception("arrival_seconds out of range")
            box.add_short(arrival_seconds/60)
            #box.add_int(departure_seconds)

        out_file.write("INSERT INTO arrivals VALUES (%d, %s);\n" % (
            arrival_id, box.get_blob_string()
        ))

def write_stop_list_table(out_file, stop_list_map):
    out_file.write("CREATE TABLE trip_stops (id INTEGER PRIMARY KEY, blob STRING);\n")
    for stop_list_id, lst in stop_list_map.items():
        box = Box()
        box.add_short(len(lst))

        for stop_id, sequence in lst:
            box.add_string(stop_id)
            box.add_byte(sequence)

        out_file.write("INSERT INTO trip_stops VALUES (%d, %s);\n" % (
            stop_list_id, box.get_blob_string()
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
        stop_times = read_stop_times_table(os.path.join(args.path, "stop_times.txt"))
        compressed_stop_times, arrivals_map, stop_list_map = compress_stop_times_table(stop_times)
        write_stop_times_table(f, compressed_stop_times, trip_ids_map)
        write_arrivals_table(f, arrivals_map)
        write_stop_list_table(f, stop_list_map)

        f.write("END TRANSACTION;\n")

if __name__ == "__main__":
    main()







