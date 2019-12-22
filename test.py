from services.goals import Goals
from services.matchers import Matchers

goals = Goals("http://192.168.0.21:9999/goals/")
matchers = Matchers("http://192.168.0.21:9999/matcher/")

print(goals.set_limit({'category': 'SUPERMARKET',
                        'limit': 5000,
                        'family': 'zagoruiko'}))
print(goals.get_limits('zagoruiko'))
print(goals.get_limits('zagoruiko', category='SUPERMARKET'))

print(goals.get_limit_report('zagoruiko'))
limits = goals.get_limit_report('zagoruiko')

maxlen = 0
for limit in limits:
    if len(limit['category']) > maxlen:
        maxlen = len(limit['category'])

for limit in limits:
    if len(limit['category']) < maxlen:
        for i in range(0, maxlen - len(limit['category'])):
            limit['category'] += ' '

limitstr = ''
for limit in limits:
    limitstr += "%s\t%s\t%s\t%s%%\n" % (limit['category'], limit['limit'], limit['amount'], limit['percent'])
print(limitstr)
print(matchers.get_categories())
