#!/usr/bin/env python3

from argparse import ArgumentParser
from datetime import datetime, timedelta
import logging
import pymongo

parser = ArgumentParser()
parser.add_argument('targets', metavar='TARGET', nargs='+', help='target hostname')
parser.add_argument('--output', '-o', metavar='file', default='index.html', help='html output file')
parser.add_argument('-v', '--verbosity', action='count', default=0, help='increase output verbosity (-vv for debug)')
args = parser.parse_args()

output = args.output
targets = args.targets
verbosity = args.verbosity

logging_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
logging.basicConfig(level=logging_levels[verbosity],
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

client = pymongo.MongoClient("mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0")
database = 'arping'


def main():
    minute_ago = datetime.now().replace(second=0, microsecond=0) - timedelta(minutes=1)
    six_days_ago = minute_ago.replace(hour=0, minute=0) - timedelta(days=6)
    six_days_ago_db_record_format = str(six_days_ago.strftime('%Y-%m-%d %H:%M'))
    html_body = []

    for target in targets:
        cursor = client[database][target]
        records = cursor.find({'_id': {'$gte': six_days_ago_db_record_format}}).sort('_id', pymongo.ASCENDING)
        online_times = []
        for record in records:
            online_times.append(datetime.strptime(record['_id'], '%Y-%m-%d %H:%M'))

        state_changes = []
        ts = six_days_ago
        previous_online = True if ts in online_times else False
        state_changes.append({'ts': ts, 'online': previous_online})
        while ts < minute_ago:
            ts += timedelta(minutes=1)
            online = True if ts in online_times else False
            if online != previous_online:
                state_changes.append({'ts': ts, 'online': online})
                logging.info(f'{target} appending {ts} {online}')
            previous_online = online

        if len(state_changes) == 1:
            color = 'lime' if state_changes[0]['online'] else 'lightgrey'
            html_body.append(f'<h1 style="background-color:{color};">N/A</h1>')
        else:
            color = 'lime' if state_changes[-1]['online'] else 'lightgrey'
            ts_str = state_changes[-1]['ts'].strftime('%a %H:%M')
            html_body.append(f'<h1 style="background-color:{color};">{ts_str}</h1>')

    html_doc = []
    html_doc.append('<!DOCTYPE html><html><style>h1 {text-align: center; font-size:500%;}</style>')
    html_doc.append('<meta http-equiv="refresh" content="60"><body>')
    for line in html_body:
        html_doc.append(line)
    html_doc.append('</body></html>')
    with open(output, 'w') as f:
        f.writelines(html_doc)


if __name__ == "__main__":
    logging.info("Starting...")
    try:
        main()
    except KeyboardInterrupt as eki:
        logging.info("Stopping...")
