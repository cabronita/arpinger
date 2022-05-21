#!/usr/bin/env python3

from argparse import ArgumentParser
from datetime import datetime, timedelta
import logging
import pymongo

parser = ArgumentParser()
parser.add_argument('target', help='target hostname')
parser.add_argument('-v', '--verbosity', action='count', default=0, help='increase output verbosity (-vv for debug)')
args = parser.parse_args()

target = args.target
verbosity = args.verbosity

logging_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
logging.basicConfig(level=logging_levels[verbosity],
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

client = pymongo.MongoClient("mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0")
database = 'arping'
collection = target
cursor = client[database][collection]


def main():
    records = cursor.find().sort('_id', pymongo.ASCENDING)
    online_times_list = []
    for i in records:
        online_times_list.append(datetime.strptime(i['_id'], '%Y-%m-%d %H:%M'))
    time = online_times_list[0]
    alternate_state = False
    while True:
        was_online = time in online_times_list
        if alternate_state == was_online:
            if was_online:
                print(f"{time} UP")
            else:
                print(f"{time} DOWN")
        if time == online_times_list[-1]:
            break
        else:
            time = time + timedelta(minutes=1)
            alternate_state = not was_online


if __name__ == "__main__":
    logging.info("Starting...")
    try:
        main()
    except KeyboardInterrupt as eki:
        logging.info("Stopping...")
