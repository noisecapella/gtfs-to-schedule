gtfs-to-schedule
================

A simple program to turn GTFS data into a general schedule.

Requirements
------------

* GTFS data for your particular stop needs to be downloaded and unzipped into a directory
* `print_updates.py` is currently hardcoded to the MBTA's GTFS-realtime feed, you might want to change this for other transit agencies.

Pieces
------
* `make_schedule.py` - This creates simple schedules for each route in the system. This should be changed to resemble paper schedules where certain details are omitted. Right now it's basically a less useful version of `make_database.py`.
* `make_database.py` - This creates a database which contains enough information about every GTFS trip in order to be useful for resolving GTFS-realtime results. This actually produces SQL statements, you can create a SQLite database like this: `sqlite3 new.db < make_database_output.sql`
* `print_updates.py` - This takes the database from `make_database.py` and a stop number and prints all updates for this stop, for each route and including delay information from GTFS-realtime.

Database Schema
---------------

For detailed information please inspect the database and the source code. Here's the basic overview.

`trip_ids` and `stop_ids` contain strings which are used to identify the trip or stop in the GTFS data. They map these strings to ID numbers which are used internally instead of the strings to save space. They may also contain extra trip or stop related data.

The `stop_times` table roughly corresponds to the huge `stop_times.txt` GTFS file. It joins with the `arrivals` table to provide all arrival times for every trip for every stop. The database takes advantage of the redundancy of information so that multiple trips will map to the same arrival timetable, just with different starting times.