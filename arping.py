#!/usr/bin/env python3

from argparse import ArgumentParser
from datetime import datetime
import subprocess
from time import sleep
import logging
import pymongo

parser = ArgumentParser()
parser.add_argument('target', help='target IP')
parser.add_argument('-v', '--verbosity', action='count', default=0, help='increase output verbosity (-vv for debug)')
args = parser.parse_args()

ip = args.target
verbosity = args.verbosity

logging_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
logging.basicConfig(level=logging_levels[verbosity],
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

client = pymongo.MongoClient("mongodb://mongo1:27017,mongo2:27017/?replicaSet=rs0")
database = 'arping'
collection = 'online'
cursor = client[database][collection]


def get_interface_dev():
    get_route = f"ip -oneline route get {ip}"
    return subprocess.run(get_route.split(), stdout=subprocess.PIPE).stdout.split()[2].decode()


def get_state(timestamp):
    logging.debug('Arping...')
    command = f"/usr/sbin/arping -q -f -I {dev} -w 5 {ip}"
    return subprocess.run(command.split()).returncode


def now():
    return datetime.now().replace(second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')


def main():
    confirmed_online_time = None
    while True:
        time = now()
        if time != confirmed_online_time:
            logging.debug(f"Not confirmed for {time} yet")
            document = {"_id": {ip: time}}
            if not cursor.find_one(document):
                logging.debug('No record found in database')
                check_output = get_state(time)
                if check_output == 0:
                    logging.debug('Up')
                    cursor.replace_one(document, document, upsert=True)
                    confirmed_online_time = time
                else:
                    logging.info('Down')
            else:
                logging.debug('Matching record found in database')
                confirmed_online_time = time
        sleep(1)


if __name__ == "__main__":
    logging.info("Starting...")
    dev = get_interface_dev()
    try:
        main()
    except KeyboardInterrupt as eki:
        logging.info("Stopping...")
