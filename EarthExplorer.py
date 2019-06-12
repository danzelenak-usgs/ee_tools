
import sys
import json
import requests
import getpass

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
