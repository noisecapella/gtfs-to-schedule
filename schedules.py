#!/usr/bin/env python3

__author__ = 'schneg'
from collections import OrderedDict
class Schedule:
    def __init__(self):
        # a mapping of stop -> StopSchedule
        self.schedules = {}
        # a list of all stops which were added for this schedule
        self.stops = OrderedDict()
        # mapping of stop -> (first stop, first schedule in compressed group)
        self.schedule_groups = {}

    def add_time(self, arrival_time, stop):
        if stop not in self.stops:
            self.stops[stop] = True
            self.schedules[stop] = StopSchedule(stop)

        self.schedules[stop].add_time(arrival_time)

    def compress(self):
        # if schedule is exactly some number of minutes different from previous
        # replace with number

        prev_sched = None
        for stop, _ in self.stops.items():
            current_sched = self.schedules[stop]
            current_sched.compress()
            for schedule_group_stop, prev_sched in self.schedule_groups.items():
                diff = prev_sched.diff(current_sched)
                if diff is not None:
                    self.schedules[stop] = (prev_sched, diff)
                    break
            else:
                self.schedule_groups[stop] = current_sched

    def diff_as_string(self, x):
        if len(x) == 0:
            raise Exception("empty list")
        elif len(x) == 1:
            if x[0] % 60 == 0:
                return "%s minutes" % str(x[0]/60)
            else:
                return "%s seconds" % str(x[0])
        else:
            if len(list(filter(lambda z: z % 60 == 0, x))) == len(x):
                return str([each/60 for each in x])
            else:
                return str(x)

    def __str__(self):
        ret = ""

        for stop, _ in self.stops.items():
            current_sched = self.schedules[stop]
            if type(current_sched) == tuple:
                prev_sched, diff = current_sched
                ret += "     whole schedules for '%s' is exactly %s from '%s'\n" % \
                       (stop, self.diff_as_string(diff), prev_sched.stop)
            else:
                ret += ("    Stop: %s\n" % stop) + str(current_sched)

        return ret


class StopSchedule:
    """A compressed schedule for a stop"""
    def __init__(self, stop):
        self.pieces = []
        self.trip = None
        self.stop = stop

    def diff(self, next_sched):
        if len(next_sched.pieces) != len(self.pieces):
            return None

        current_diff = None
        for i, piece in enumerate(self.pieces):
            start_time, inc, count = piece

            next_start_time, next_inc, next_count = next_sched.pieces[i]

            if next_inc == inc and next_count == count:
                diff = next_start_time - start_time
                if current_diff is None:
                    current_diff = [diff]
                else:
                    current_diff.append(diff)
            else:
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
            ret += "        start at %s, repeat every %d minutes %d times\n" %\
                   (time_to_string(start_time), inc/60, count)

        return ret

def time_to_string(time):
    """Seconds from beginning of day to string"""

    hour = time / (60*60)
    time -= hour*60*60

    minute = time/60
    time -= minute*60

    second = time

    return "%02d:%02d:%02d" % (hour, minute, second)
