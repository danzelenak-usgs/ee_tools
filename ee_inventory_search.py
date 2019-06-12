"""
Search EE Inventory for Collection 1 datasets

Date: 2019-06-12
"""
from argparse import ArgumentParser
from multiprocessing import Pool  # use threads for I/O bound tasks

import getpass
import json
import os
import requests
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class EarthExplorer(object):
    """  Web-Service interface for EarthExplorer JSON Machine-to-Machine API  """

    def __init__(self, version='1.4.1'):
        self.baseurl = 'https://earthexplorer.usgs.gov/inventory/json/v/%s/' % version

    def _api(self, endpoint='login', body=None):
        body = {'jsonRequest': json.dumps(body)} if body else {}
        r = requests.post(self.baseurl + endpoint, data=body)
        r.raise_for_status()
        dat = r.json()
        if dat.get('error'):
            sys.stderr.write(': '.join([dat.get('errorCode'), dat.get('error')]))
            exit(1)
        return dat

    @classmethod
    def login(cls, username, password=None):
        if password is None:
            password = getpass.getpass('Password (%s): ' % username)
        payload = {'username': username, 'password': password}
        return cls()._api('login', payload).get('data')

    @classmethod
    def search(cls, **kwargs):
        return cls()._api('search', kwargs).get('data')

    @classmethod
    def download(cls, **kwargs):
        return cls()._api('download', kwargs).get('data')

    @staticmethod
    def additionalCriteriaValues(p=None, r=None):
        k = 'additionalCriteria'
        additional = {k: {"filterType": "and", "childFilters": []}}
        if p:
            additional[k]['childFilters'].append({"filterType": "value", "fieldId": 21989, "value": p})
        if r:
            additional[k]['childFilters'].append({"filterType": "value", "fieldId": 19879, "value": r})

        return additional

    @staticmethod
    def temporalCriteria(ad):
        dates = ad.split(',')
        sd, ed = dates if len(dates) == 2 else dates * 2
        return {"temporalFilter": {"dateField": "search_date", "startDate": sd, "endDate": ed}}


def search_collection1_archive(directory, wrs_path=None, wrs_row=None, username=None, password=None,
                               dataset='LANDSAT_TM_C1', N=50000, acq_date=None, months=[]):
    """
    Search for and download Landsat ARD products to local directory

        Args:
            directory: Relative path to local directory (will be created)
            wrs_path: path
            wrs_row: row
            username: ERS Username (with full M2M download access) [Optional]
            dataset: EarthExplorer Catalog datasetName [Default: ARD_TILE]
            N: Maximum number of search results to return
            acq_date: Search Date image acquired [Format: %Y-%m-%d]
            password:
    """
    api_key = EarthExplorer.login(username=username, password=password)

    search = dict(apiKey=api_key, datasetName=dataset, maxResults=N)

    if any([wrs_path, wrs_row]):
        search.update(EarthExplorer.additionalCriteriaValues(r=wrs_row, p=wrs_path))

    if acq_date:
        search.update(EarthExplorer.temporalCriteria(ad=acq_date))

    if months:
        search.update(months=months)

    results = EarthExplorer.search(**search)

    n_results = results['totalHits']

    product_ids = results['results']

    print("Path: %s %s" % (wrs_path, wrs_row))
    print("Number of results: %s" % n_results)
    print("Product IDs: ")

    for i in product_ids:
        print("%s\n" % i["displayId"])

    if len(product_ids) < 1:
        return

    if not os.path.exists(directory):
        os.makedirs(directory)

    fname = os.path.join(directory, '{}_p{}-r{}_scenes.txt'.format(acq_date.replace(',', ''),
                                                                   wrs_path,
                                                                   wrs_row))

    with open(fname, 'w') as f:
        for s in product_ids:
            scene = s['displayId']

            f.write(scene)

    print('Wrote results out to %s' % fname)

    return None


def build_command_line_arguments():
    """
    Read in the command line arguments
    :return:
    ArgumentParser.parse_args
    """
    description = 'Search and download ARD data (skip those already downloaded)'

    parser = ArgumentParser(description=description, add_help=False)

    parser.add_argument('--help', action='help', help='show this help message and exit')

    parser.add_argument('-d', '--directory', type=str, dest='directory', required=True,
                        help='Relative path to save scene list text file')

    parser.add_argument('-u', '--username', type=str, dest='username', default=None,
                        help='ERS Username (with full M2M download access)')

    parser.add_argument('--path', type=int, dest='wrs_path',
                        help='WRS2 PATH')

    parser.add_argument('--row', type=int, dest='wrs_row',
                        help='WRS2 ROW')

    parser.add_argument('--dataset', type=str, dest='dataset', default='LANDSAT_TM_C1',
                        choices=['LANDSAT_TM_C1', 'LANDSAT_ETM_C1', 'LANDSAT_MSS_C1', 'LANDSAT_8_C1'],
                        help='EE Catalog dataset name')

    parser.add_argument('--acq_dates', type=str, metavar= 'YYYY-MM-DD,YYYY-MM-DD', dest='acq_date', default=None,
                        help='Search Dates Acquired (FROM TO)')

    parser.add_argument('--months', type=list, metavar='INT', dest='months', default=[],
                        help='Months of acquisition to search for, default=[]')

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    search_collection1_archive(**vars(build_command_line_arguments()))
