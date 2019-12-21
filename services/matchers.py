import requests, json


class Matchers(object):
    def __init__(self, base_url):
        self.base_url = base_url

    def get_categories(self):
        r = requests.get("%stags/categories" % self.base_url,
                         headers={"Content-type": "application/json"})

        if r.status_code != 200:
            return -1
        return r.json()
