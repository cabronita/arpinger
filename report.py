#!/usr/bin/env python3

from argparse import ArgumentParser
from datetime import datetime, timedelta
import logging
import pymongo

parser = ArgumentParser()
parser.add_argument('targets', metavar='TARGET', nargs='+', help='target hostname')
parser.add_argument('-v', '--verbosity', action='count', default=0, help='increase output verbosity (-vv for debug)')
args = parser.parse_args()

targets = args.targets
verbosity = args.verbosity

logging_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
logging.basicConfig(level=logging_levels[verbosity],
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

client = pymongo.MongoClient("mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0")
database = 'arping'


def get_recent_online_times(cursor, earliest_timestamp):
    online_times = []
    records = cursor.find().sort('_id', pymongo.ASCENDING)
    for record in records:
        dt_time = datetime.strptime(record['_id'], '%Y-%m-%d %H:%M')
        if dt_time >= earliest_timestamp:
            online_times.append(dt_time)
    return online_times


def get_status_change_times(target):
    cursor = client[database][target]
    now = datetime.now().replace(second=0, microsecond=0)
    earliest_timestamp = now - timedelta(days=3)
    online_times_list = get_recent_online_times(cursor, earliest_timestamp)
    if not online_times_list:
        return

    state_changes = list()
    ts = earliest_timestamp
    previous_online = None
    while ts < now:
        if ts in online_times_list:
            online = True
        else:
            online = False
        if online != previous_online:
            state_changes.append({'ts': ts, 'online': online})
        previous_online = online
        ts += timedelta(minutes=1)
    return state_changes


def main():
    for target in targets:
        print(target)
        states = get_status_change_times(target)
        if states:
            for item in states:
                state = 'UP' if item['online'] else 'DOWN'
                print('-', item['ts'].strftime('%a %H:%M'), state)
        else:
            print('- No records')
        if not states:
            color = 'grey'
            ts = ''
        else:
            (ts, current_state) = states[-1].values()
            color = 'GREEN' if item['online'] else 'grey'
        logging.info(f"{color} {ts}")


if __name__ == "__main__":
    logging.info("Starting...")
    try:
        main()
    except KeyboardInterrupt as eki:
        logging.info("Stopping...")
