import csv
import os

import requests


def pull_results(url, remote=False):

    if remote is True:
        if os.path.exists('results.csv'):
            os.unlink('results.csv')

    if not os.path.exists('results.csv'):
        print('Retrieving results from: %s' % url)
        response = requests.get(url)
        with open('results.csv', 'w') as outf:
            outf.write(response.text.replace('\r', ''))

    with open('results.csv', 'r') as inf:
        reader = csv.reader(inf)
        next(reader)

        return [x for x in reader]
