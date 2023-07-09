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
            date = datetime.strptime(record['_id'], '%Y-%m-%d %H:%M')
            logging.debug(f'Appending {date}')
            online_times.append(date)

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
            color = 'red' if state_changes[0]['online'] else 'green'
            html_body.append(f'<div class="{color}"><h1>N/A</h1></div>')
        else:
            color = 'red' if state_changes[-1]['online'] else 'green'
            ts_str = state_changes[-1]['ts'].strftime('%a %H:%M')
            html_body.append(f'<div class="{color}"><h1>{ts_str}</h1></div>')

    cursor = client[database]['report']
    c = cursor.find_one()
    previous_state = c['html_body'] if c else None

    if previous_state != html_body:
        logging.info(f'Writing {output}')
        cursor.update_one({'_id': 'html_body'}, {'$set': {'html_body': html_body}}, upsert=True)
        html_doc = [
            '<!DOCTYPE html><html><meta http-equiv="refresh" content="30"><style>',
            'h1 {color: white; font-size: 150px; padding: 100px; text-align: center}',
            '.red {background-color: red;}',
            '.green {background-color: green;}',
            '</style><body style="background-color:black;">',
        ]
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
