import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('requests').setLevel(logging.WARN)

import bugbuzz; bugbuzz.set_trace()

friends = ['john', 'pat', 'gary', 'michael']
for i, name in enumerate(friends):
    print "iteration {iteration} is {name}".format(iteration=i, name=name)
