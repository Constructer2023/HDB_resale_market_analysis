from __future__ import annotations
import requests

BASE = "https://www.onemap.gov.sg"

class OneMapClient:
    def __init__(self, email: str, password: str, token: str | None = None):
        self.email = email
        self.password = password
        self.token: str | None = token
        self._token_ts = -1

    def get_token(self, force: bool = False):
        # token lasts 3 days
        # refresh if older than 3 days or forced
        if self.token and not force:
            return self.token
        url = f'{BASE}/api/auth/post/getToken'
        payload = {'email': self.email, 'password': self.password}
        response = requests.request('POST', url, json = payload, timeout = 30)
        response.raise_for_status()
        data = response.json()
        self.token = data['access_token']
        self._token_ts = data['expiry_timestamp']
        return self.token

    def _headers(self):
        return {'Authorization': self.get_token()}

    def search(self, search_val: str, return_geom: bool = True, get_addr_details: bool = True):
        """
        geocode an address string.
        """
        url = f'{BASE}/api/common/elastic/search'
        params = {
            'searchVal': search_val,
            'returnGeom': 'Y' if return_geom else 'N',
            'getAddrDetails': 'Y' if get_addr_details else 'N',
            'pageNum': 1
        }
        url = f'{url}?searchVal={params['searchVal']}&returnGeom={params['returnGeom']}&getAddrDetails={params['getAddrDetails']}&pageNum={params['pageNum']}'
        response = requests.get(url, headers = self._headers(), timeout = 30)
        response.raise_for_status()
        return response.json()

    def get_all_planning_areas(self, year: int | None = 2019):
        """
        return list of dicts containing planning areas with names and geojson.
        """
        url = f'{BASE}/api/public/popapi/getAllPlanningarea'
        params = {}
        if year is not None:
            if year in (1998, 2008, 2014, 2019):
                params['year'] = year
        url = f'{url}?year={year}'
        response = requests.request('GET', url, headers = self._headers(), timeout = 60)
        response.raise_for_status()
        data = response.json() # response shape shall be {'SearchResults': [...]}
        return data['SearchResults']

    def get_names_of_planning_areas(self, year: int | None = 2019):
        """
        return list of dicts containing ids and names of planning areas.
        """
        url = f'{BASE}/api/public/popapi/getPlanningareaNames'
        params = {}
        if year is not None:
            if year in (1998, 2008, 2014, 2019):
                params['year'] = year
        url = f'{url}?year={year}'
        response = requests.request('GET', url, headers = self._headers(), timeout = 60)
        response.raise_for_status()
        data = response.json()
        return data.get('SearchResults')

    def get_nearest_mrt(self, lat: float, lon: float, radius_m: int = 2000):
        """
        OneMap nearby MRT/LRT stations.
        """
        url = f'{BASE}/api/public/nearbysvc/getNearestMrtStops'
        params = {'latitude': lat, 'longitude': lon, 'radius_in_meters': radius_m}
        url = f'{url}?latitude={params['latitude']}&longitude={params['longitude']}&radius_in_meters={params['radius_in_meters']}'
        response = requests.get(url, headers = self._headers(), timeout = 30)
        response.raise_for_status()
        data = response.json()
        return data
