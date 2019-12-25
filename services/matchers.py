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

    def get_suggestions(self, pattern):
        r = requests.get("%stags/suggest?q=%s" % (self.base_url, pattern),
                         headers={"Content-type": "application/json"})

        if r.status_code != 200:
            return -1
        return r.json()

    def get_unrecognized(self, tag, num):
        r = requests.get("%sreport/unrecognized?tags=%s" % (self.base_url, tag),
                         headers={"Content-type": "application/json"})

        if r.status_code != 200:
            return -1

        if len(r.json()) < num + 1:
            return None

        return r.json()[num]

    def add_matcher(self, tags, provider, func, pattern):
        r = requests.put("%smatchers/addmany" % self.base_url,
                         json.dumps([
                             {'provider': provider, "func": func, "pattern": pattern, "tags": tags}
                         ]),
                         headers={"Content-type": "application/json"})

        if r.status_code != 200:
            return -1
        return r.json()
