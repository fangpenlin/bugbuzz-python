import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('requests').setLevel(logging.WARN)


def func(
    arg1,
    arg2,
    arg3,
):
    """1
    2
    3
    """
    print arg1, arg2, arg3
    for i in range(10):
        print 'foo'
    return 'hi'

func(1, 2, 3)

print 1
print 2
print 3
import requests
import bugbuzz; bugbuzz.set_trace()
requests.get('http://google.com')

friends = ['john', 'pat', 'gary', 'michael']
for i, name in enumerate(friends):
    print "iteration {iteration} is {name}".format(iteration=i, name=name)
