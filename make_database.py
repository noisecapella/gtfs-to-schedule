#!/usr/bin/env python3

from make_schedule import parse
import argparse
import os

from box import Box

from make_schedule import (
    make_days,
    make_days_hash,
    )

from schedules import (
    StopSchedule,
    Schedule,

)

def print_service_table(f, calendar):
    f.write("CREATE TABLE IF NOT EXISTS service (id INTEGER PRIMARY KEY, "
            "days_of_week INTEGER, start_date INTEGER, end_date INTEGER)\n")
    service_ids = {}
    count = 0
    for service_id, row in calendar.items():
        arr = make_days(calendar, service_id)
        h = make_days_hash(arr)

        f.write("INSERT INTO service VALUES (%d, %d, %d, %d)\n" %
                (count, h, int(row["start_date"]), int(row["end_date"])))
        service_ids[row["service_id"]] = count
        count += 1
    return service_ids

def print_schedule_table(f, schedule, service_ids, direction_ids):
    f.write("CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY, direction_id INTEGER, service_id INTEGER)\n")

    count = 0
    schedule_ids = {}
    for route, direction_map in schedule.items():
        for direction, service_map in direction_map.items():
            for service, sched in service_map.items():
                service_id = service_ids[service]
                direction_id = direction_ids[direction]

                f.write("INSERT INTO schedule VALUES (%d, %d, %d)\n" %
                        (count, direction_id, service_id))
                schedule_ids[(route, direction, service)] = count
                count += 1
    return schedule_ids

def escaped(s):
    return s.replace("'", "''")


def print_direction_table(f, schedule):
    f.write("CREATE TABLE IF NOT EXISTS gtfs_directions (id INTEGER PRIMARY KEY, title STRING)\n")
    count = 0
    direction_ids = {}
    for route, direction_map in schedule.items():
        for direction in direction_map.keys():
            direction_ids[direction] = count

            f.write("INSERT INTO gtfs_directions VALUES (%d, '%s')\n" % (count, escaped(direction)))
            count += 1

    return direction_ids


def print_stop_schedule_table(f, schedule, schedule_ids):
    f.write("CREATE TABLE IF NOT EXISTS stop_schedule (id INTEGER PRIMARY KEY, service_id INTEGER, stop_id STRING)\n")
    count = 0

    stop_schedule_ids = {}
    for route, direction_map in schedule.items():
        for direction, service_map in direction_map.items():
            for service, sched in service_map.items():
                for stop in sched.stops:
                    sched_key = (route, direction, service)
                    f.write("INSERT INTO stop_schedule VALUES (%d, %d, %s)\n" % (count, schedule_ids[sched_key], stop))
                    stop_schedule_ids[(service, stop)] = count

                    count += 1

    return stop_schedule_ids


def print_stop_schedule_row_table(f, schedule, stop_schedule_ids):
    f.write("CREATE TABLE IF NOT EXISTS stop_schedule_row (stop_schedule_id"
            " INTEGER, start_time INTEGER, repeats INTEGER, diff INTEGER)\n")

    count = 0
    for route, direction_map in schedule.items():
        for direction, service_map in direction_map.items():
            for service, sched in service_map.items():
                for stop in sched.stops:
                    stop_schedule_or_diff = sched.schedules[stop]
                    if type(stop_schedule_or_diff) == StopSchedule:
                        stop_schedule_id = stop_schedule_ids[(service, stop)]
                        for piece in stop_schedule_or_diff.pieces:
                            arrival_time, diff, repeat_count = piece
                            f.write("INSERT INTO stop_schedule_row VALUES (%d, %d, %d, %d)\n" %
                                    (stop_schedule_id, arrival_time, diff, repeat_count))
                            count += 1
                    # else it's a duplicate, handle in print_schedule_duplicate_table


def print_stop_schedule_duplicate_table(f, schedule, stop_schedule_ids, schedule_ids, diff_ids):
    f.write("CREATE TABLE IF NOT EXISTS stop_schedule_duplicate (id INTEGER PRIMARY KEY,"
            " schedule_id INTEGER, diff INTEGER)\n")
    # TODO: whole schedule for first stop is exactly d seconds from this stop
    count = 0
    for route, direction_map in schedule.items():
        for direction, service_map in direction_map.items():
            for service, sched in service_map.items():
                for stop in sched.stops:
                    stop_schedule_or_diff = sched.schedules[stop]
                    if type(stop_schedule_or_diff) == tuple:
                        prev_sched, diff = stop_schedule_or_diff
                        stop_schedule_id = stop_schedule_ids[(service, stop)]
                        schedule_id = schedule_ids[(route, direction, service)]
                        diff_id = diff_ids[tuple(diff)]
                        f.write("INSERT INTO stop_schedule_duplicate VALUES (%d, %d, %d)\n" %
                                (stop_schedule_id, schedule_id, diff_id))
                    # else it's not a duplicate


def print_diff_table(f, schedule):
    diff_ids = {}
    count = 0
    f.write("CREATE TABLE IF NOT EXISTS diff (diff_id INTEGER, diff BLOB)\n")
    for route, direction_map in schedule.items():
        for direction, service_map in direction_map.items():
            for service, sched in service_map.items():
                for stop in sched.stops:
                    stop_schedule_or_diff = sched.schedules[stop]
                    if type(stop_schedule_or_diff) == tuple:
                        prev_sched, diff = stop_schedule_or_diff
                        diff_key = tuple(diff)
                        if diff_key not in diff_ids:
                            diff_ids[diff_key] = count
                            box = Box()
                            box.add_ints(diff)
                            count += 1
                            f.write("INSERT INTO diff VALUES (%d, %s)\n" %
                                    count, box.get_blob_string())
    return diff_ids


def print_trip_table(f, schedule):
    f.write("CREATE TABLE IF NOT EXISTS trips (id INTEGER PRIMARY KEY, start_time INTEGER)\n")


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
        # test that f is writable
        f.write("\n")
        schedule, trips, calendar = parse(args.path)

        service_ids = print_service_table(f, calendar)
        direction_ids = print_direction_table(f, schedule)
        schedule_ids = print_schedule_table(f, schedule, service_ids, direction_ids)
        stop_schedule_ids = print_stop_schedule_table(f, schedule, schedule_ids)
        print_stop_schedule_row_table(f, schedule, stop_schedule_ids)
        diff_ids = print_diff_table(f, schedule)
        print_stop_schedule_duplicate_table(f, schedule, diff_ids)

if __name__ == "__main__":
    main()







