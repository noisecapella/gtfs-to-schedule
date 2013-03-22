from make_schedule import parse
import argparse
import os

def print_service_table(schedule):
    print "CREATE TABLE IF NOT EXISTS service (id INTEGER PRIMARY KEY, days_of_week INTEGER, start_date INTEGER, end_date INTEGER)"



def print_schedule_table(schedule):
    print "CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY, direction_id INTEGER, service_id INTEGER)"

def print_direction_table(schedule):
    print "CREATE TABLE IF NOT EXISTS gtfs_directions (id INTEGER PRIMARY KEY, title STRING)"


def print_stop_schedule_table(schedule):
    print "CREATE TABLE IF NOT EXISTS stop_schedule (id INTEGER PRIMARY KEY, schedule_id INTEGER, stop_id STRING)"



def print_stop_schedule_row_table(schedule):
    print "CREATE TABLE IF NOT EXISTS stop_schedule_row (stop_schedule_id INTEGER, start_time INTEGER, repeats INTEGER, diff INTEGER)"



def print_stop_schedule_duplicate_table(schedule):
    print "CREATE TABLE IF NOT EXISTS stop_schedule_duplicate (stop_schedule_id INTEGER, stop_id STRING, diff INTEGER)"



def print_diff_table(schedule):
    print "CREATE TABLE IF NOT EXISTS diff (diff_id INTEGER, n1 INTEGER, n2 INTEGER, ...)"



    

def main():
    parser = argparse.ArgumentParser(description='Parses GTFS data into general schedule')
    parser.add_argument('path', help='Path of directory containing GTFS data')

    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print("%s is not a valid directory" % args.path)
        exit(-1)

    schedule = parse(args.path)
    
    print_service_table(schedule)
    print_direction_table(schedule)
    print_schedule_table(schedule)
    print_stop_schedule_table(schedule)
    print_stop_schedule_row_table(schedule)
    print_stop_schedule_duplicate_table(schedule)
    print_diff_table(schedule)

if __name__ == "__main__":
    main()







