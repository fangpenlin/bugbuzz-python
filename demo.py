import requests

import bugbuzz
bugbuzz.set_trace()

for url in ['http://google.com', 'http://facebook.com', 'http://twitter.com']:
    requests.get(url)
