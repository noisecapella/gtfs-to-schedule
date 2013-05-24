__author__ = 'schneg'
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

