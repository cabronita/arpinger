#!/usr/bin/env python3

from argparse import ArgumentParser
from datetime import datetime
from socket import gethostbyname
import subprocess
from time import sleep
import logging
import pymongo

parser = ArgumentParser()
parser.add_argument('target', help='target hostname')
parser.add_argument('-i', '--interface', default='eth0', metavar='DEV', help='arping interface (default = eth0)')
parser.add_argument('-v', '--verbosity', action='count', default=0, help='increase output verbosity (-vv for debug)')
args = parser.parse_args()

target = args.target
target_ip = gethostbyname(target)
interface = args.interface
verbosity = args.verbosity

logging_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
logging.basicConfig(level=logging_levels[verbosity],
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

client = pymongo.MongoClient("mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0")
database = 'arping'
collection = target
cursor = client[database][collection]


def arping():
    logging.debug(f"Sending arping to {target_ip}")
    command = f"/usr/sbin/arping -q -f -I {interface} -w 5 {target_ip}"
    return subprocess.run(command.split()).returncode


def now():
    return datetime.now().replace(second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')


def main():
    confirmed_online_time = None
    while True:
        time = now()
        if time != confirmed_online_time:
            logging.debug(f"Not confirmed for {time} yet")
            document = {"_id": time}
            if not cursor.find_one(document):
                logging.debug('No record found in database')
                output = arping()
                if output == 0:
                    logging.info('Up')
                    cursor.replace_one(document, document, upsert=True)
                    confirmed_online_time = time
                else:
                    logging.info('Down')
            else:
                logging.info('Already up')
                confirmed_online_time = time
        sleep(1)


if __name__ == "__main__":
    logging.info("Starting...")
    try:
        main()
    except KeyboardInterrupt as eki:
        logging.info("Stopping...")
