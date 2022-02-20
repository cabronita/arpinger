#!/usr/bin/env python3

from argparse import ArgumentParser
from datetime import datetime, timedelta
from subprocess import run
from time import sleep
import logging
import pymongo

parser = ArgumentParser()
parser.add_argument('target', help='target IP')
parser.add_argument('-o', '--output', default='output.html', help='html output filename')
parser.add_argument('-v', '--verbosity', action='count', default=0, help='increase output verbosity (-vv for debug)')
args = parser.parse_args()

ip = args.target
report_file = args.output
verbosity = args.verbosity

logging_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
logging.basicConfig(level=logging_levels[verbosity],
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

client = pymongo.MongoClient("mongodb://mongo1:27017,mongo2:27017/?replicaSet=rs0")
col = client['arping']['states']


def get_interface_dev():
    get_route = f"/usr/sbin/ip -oneline route get {ip}"
    return run(get_route.split(), capture_output=True, text=True).stdout.split()[2]


def flapping(previous_state, state):
    downtime_minutes_to_ignore = 2
    if state['online']:
        if previous_state['timestamp'] >= state['timestamp'] - timedelta(minutes=downtime_minutes_to_ignore):
            return True


def saved(state):
    logging.debug(f"Received: {state['timestamp']} {state['online']}")
    if col.count_documents({'ip': ip}):
        previous_state = col.find({'ip': ip}).sort('timestamp', pymongo.DESCENDING).limit(1)[0]
        if state['online'] != previous_state['online']:
            if flapping(previous_state, state):
                col.delete_one({'ip': ip, 'timestamp': previous_state['timestamp']})
                logging.info(f"Flapping detected. Deleted {previous_state['timestamp']}")
                return True
            col.find_one_and_replace({'ip': ip, 'timestamp': state['timestamp']}, state, upsert=True)
            return True
    else:
        col.insert_one(state)
        logging.debug("Inserted first state")
        return True


def get_state(timestamp):
    command = f"/usr/sbin/arping -q -f -I {dev} -w 2 {ip}"
    online = True if run(command.split()).returncode == 0 else False
    return {'ip': ip, 'timestamp': timestamp, 'online': online}


def generate_report():
    html_content = []
    states_count = col.count_documents({'ip': ip})
    if states_count:
        states = col.find({'ip': ip}).sort('timestamp', pymongo.DESCENDING).limit(15)
        background = 'palegreen' if states[0]['online'] == True else 'pink'
        html_content.append(
            f"<html><meta http-equiv='refresh' content='15' ><body style='background-color:{background};'>")
        for item in states:
            t_timestamp = datetime.strftime(item['timestamp'], '%a %H:%M')
            t_state = 'UP' if item['online'] else 'DOWN'
            html_content.append(f"{t_timestamp} {t_state}<br>\n")
        html_content.append("<pre style='font-size:800%;font-weight:bold;line-height:50%'>\n")
    with open(report_file, 'w') as f:
        f.writelines(html_content)


def main():
    generate_report()
    global dev
    dev = get_interface_dev()
    state = {'timestamp': None}
    while True:
        timestamp = datetime.now().replace(second=0, microsecond=0)
        if state['timestamp'] != timestamp:
            if 'online' in state.keys():
                if saved(state):
                    generate_report()
            state = get_state(timestamp)
        else:
            if not state['online']:
                state = get_state(timestamp)
        sleep(1)


if __name__ == "__main__":
    logging.info("Starting...")
    try:
        main()
    except KeyboardInterrupt as eki:
        logging.info("Stopping...")
