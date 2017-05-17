# Bugbuzz - easy to use online debugger

[![Build Status](https://travis-ci.org/victorlin/bugbuzz-python.svg?branch=master)](https://travis-ci.org/victorlin/bugbuzz-python)

![Bugbuzz demo](/screencast.gif?raw=true )

# Relative projects

[Ember.js Dashboard project](https://github.com/victorlin/bugbuzz-dashboard)
[Backend API project](https://github.com/victorlin/bugbuzz-api)

# Dashboard shortcuts

Vim style shortcuts

 - C Continue
 - H Return
 - J Next
 - L Step

# Usage

```
pip install bugbuzz
```

then insert following lines in your code to debug

```python
import bugbuzz; bugbuzz.set_trace()
```

# Security concerns

As bugbuzz providing debugging in a software-as-service manner, all source code and local variables needed will be uploaded to the server. When a debugging session created, a random secret access key will be generated, and used for encryping all source code and local variables. The access key will be passed to dashboard as a part of hash tag like this

```
http://dashboard.bugbuzz.io/#/sessions/SECsLArhHBVHF5mrtvXHVp3T?access_key=<ACCESS KEY>
```

With the access key, the Ember.js dashboard app can then decrypt the source code and local variables downloaded from the server. As the access key is passed as part of hash in the URL, the server cannot see it, without the access key, your source code and local variables are not visible by the server.

For more details about security topic, you can also read my article [Anonymous computing: Peer-to-peer encryption with Ember.js](http://victorlin.me/posts/2015/05/26/anonymous-computing-peer-to-peer-encryption-with-ember-js).

# Run demo

To run our demo

```bash
git clone --recursive git@github.com:victorlin/bugbuzz-python.git
```

install the project

```bash
virtualenv --no-site-packages .env
source .env/bin/activate
pip install -e .
```

and dependency used in the `demo.py`

```bash
pip install requests
```

then

```bash
python demo.py
```

It will open a new tab in your browser for debugging.

# Notice

 This is just a prototype, use it at your own risk
