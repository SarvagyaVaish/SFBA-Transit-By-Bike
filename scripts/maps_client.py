import os
import urllib
import urllib2
import json
from api_keys import GOOGLE_MAPS_KEY

NUMBER_OF_REQUESTS = 0
NUMBER_OF_CACHES = 0


def maps_client_network_stats():
    Memoize.print_stats()


class Memoize:
    def __init__(self, f):
        self.f = f
        self.memo = self.load_memo()

    def __call__(self, start_str, end_str):
        start_lon, start_lat = start_str.split(',')
        end_lon, end_lat = end_str.split(',')

        vals = [start_lon, start_lat, end_lon, end_lat]
        key_str = ""
        for v in vals:
            key_str += str(int(float(v)*1000))

        if key_str not in self.memo:
            global NUMBER_OF_REQUESTS
            NUMBER_OF_REQUESTS += 1
            self.memo[key_str] = self.f(start_str, end_str)
            self.save_memo(self.memo)
        else:
            global NUMBER_OF_CACHES
            NUMBER_OF_CACHES += 1

        return self.memo[key_str]

    @classmethod
    def save_memo(self, memo):
        with open(os.path.join(os.path.dirname(__file__), "biking_times_memo.txt"), 'w') as f:
            f.write(json.dumps(memo))

    @classmethod
    def load_memo(self):
        try:
            with open(os.path.join(os.path.dirname(__file__), "biking_times_memo.txt"), 'r') as f:
                memo = json.load(f)
        except:
            memo = {}

        return memo

    @classmethod
    def print_stats(cls):
        global NUMBER_OF_CACHES
        global NUMBER_OF_REQUESTS
        print "Number of requests", NUMBER_OF_REQUESTS
        print "Number of cache hits", NUMBER_OF_CACHES
        print "Number in local file", len(Memoize.load_memo().keys())


@Memoize
def get_biking_time(start_point, end_point):
    assert len(start_point.split(',')) == 2
    assert len(end_point.split(',')) == 2

    url = 'https://maps.googleapis.com/maps/api/directions/json'
    params = {
        'origin': start_point,
        'destination': end_point,
        'mode': 'bicycling',
        'key': GOOGLE_MAPS_KEY,
    }

    url_values = urllib.urlencode(params)
    full_url = url + '?' + url_values
    response = urllib2.urlopen(full_url)

    response_text = response.read()
    json_data = json.loads(response_text)

    duration = None
    if json_data['status'] == "OK":
        if json_data.has_key('routes') and \
                json_data['routes'][0].has_key('legs') and \
                json_data['routes'][0]['legs'][0].has_key('duration') and \
                json_data['routes'][0]['legs'][0]['duration'].has_key('value'):
            assert len(json_data['routes']) == 1  # guaranteed if alternatives = 0
            assert len(json_data['routes'][0]['legs']) == 1  # guaranteed when no waypoints are specified
            duration = json_data['routes'][0]['legs'][0]['duration']['value'] / 60
    else:
        print "ERROR: response status not OK"
        print repr(full_url)
        print json_data
        print ""

    return duration


# Test
# print get_biking_time("37.425822,-122.100192", "37.407323,-122.107069")
