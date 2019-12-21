import requests, json


class Goals(object):
    def __init__(self, base_url):
        self.base_url = base_url

    def get_limits(self, family, category=''):
        r = requests.get("%slimits/%s/%s" % (self.base_url, family, category),
                         headers={"Content-type": "application/json"})

        if r.status_code != 200:
            return -1
        return r.json()

    def set_limit(self, limit):
        r = requests.put('%slimits' % self.base_url,
                         json.dumps(limit),
                         headers={"Content-type": "application/json"})

        if r.status_code != 200:
            return -1
        return r.json()

    def get_limit_report(self, family):
        r = requests.get("%sreport/limits/%s" % (self.base_url, family),
                         headers={"Content-type": "application/json"})

        if r.status_code != 200:
            return -1
        return r.json()
