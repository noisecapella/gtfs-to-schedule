#!/usr/bin/env python

import argparse
import sqlite3
import gtfs_realtime_pb2
from collections import defaultdict
from operator import itemgetter
from datetime import datetime
from schedules import time_to_string

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.web.client import getPage

@inlineCallbacks
def print_updates(args):
    data = yield getPage("http://developer.mbta.com/lib/gtrtfs/Passages.pb")
    update = gtfs_realtime_pb2.FeedMessage()
    update.ParseFromString(data)

    trip_id_to_delays = defaultdict(list)
    trip_ids = set()
    for entity in update.entity:
        trip_id = entity.trip_update.trip.trip_id
        trip_ids.add(trip_id)
        for stop_time_update in entity.trip_update.stop_time_update:
            # TODO: error-check for lack of arrival.delay
            tup = stop_time_update.stop_sequence, stop_time_update.arrival.delay
            trip_id_to_delays[trip_id].append(tup)
        if trip_id in trip_id_to_delays:
            trip_id_to_delays[trip_id] = sorted(trip_id_to_delays[trip_id], key=itemgetter(0))



    con = sqlite3.connect(args.db)
    cur = con.cursor()
    # injection risk here! SQLite can't handle this many parameters, though
    trip_ids_str = ", ".join(("'%s'" % x) for x in trip_ids)

    query = ('SELECT stop_times.offset, arrivals.arrival_seconds, '
             'stop_ids.stop_id, trip_ids.route_id, trip_ids.trip_id, arrivals.sequence_id '
             'FROM trip_ids '
             'JOIN stop_times ON stop_times.trip_id = trip_ids.id AND trip_ids.trip_id IN (%s) '
             'JOIN arrivals ON arrivals.id = stop_times.arrival_id '
             'JOIN stop_ids ON arrivals.stop_id = stop_ids.id ') % trip_ids_str
    results = cur.execute(query)

    stop_results = defaultdict(list)

    for offset, arrival_seconds, stop_id, route_id, trip_id, sequence_id in results:
        current_delay = 0
        if trip_id in trip_id_to_delays:
            for stop_sequence, delay in trip_id_to_delays[trip_id]:
                if stop_sequence > sequence_id:
                    break
                current_delay = delay


        tup = (offset + arrival_seconds, route_id, current_delay, trip_id)
        stop_results[str(stop_id)].append(tup)


    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    now_seconds = (now - midnight).seconds

    if args.stop_id in stop_results:
        lst = stop_results[args.stop_id]
        new_lst = [(seconds, route_id, delay, trip_id) for (seconds, route_id, delay, trip_id) in lst
                   if (seconds + delay) > now_seconds]

        new_lst = sorted(new_lst, key=lambda x: x[0] + x[2])

        if len(new_lst) == 0:
            print("No arrivals for %s" % args.stop_id)
        else:
            for seconds, route_id, delay, trip_id in new_lst:
                print("Next arrival for %s on route %s is at %s with delay %d on trip %s" % (args.stop_id,
                                                                                  route_id,
                                                                                  time_to_string(seconds),
                                                                                  delay,
                                                                                  trip_id))
    else:
        print("%s is not in any of the trips specified by the SQL query" % args.stop_id)

@inlineCallbacks
def main(args):
    try:
        yield print_updates(args)
    finally:
        reactor.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print next update for a stop')
    parser.add_argument("db", help="Path to sqlite3 database generated by make_database.py")
    parser.add_argument("stop_id", help="stop id to get results for")
    args = parser.parse_args()
    reactor.callLater(0, lambda: main(args))
    reactor.run()