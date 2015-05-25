# Bugbuzz - easy to use online debugger

![Bugbuzz demo](/screencast.gif?raw=true )

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

```
import bugbuzz; bugbuzz.set_trace()
```

# Security concern

As bugbuzz providing debugging in a software-as-service manner, all source code and local variables needed will be uploaded to the server. However, when a debuggin session created, a random secret access key will be generated, and used for encryping all source code and local variables. The access key will be passed to dashboard as part of hash tag like this

```
http://dashboard.bugbuzz.io/#/sessions/SECsLArhHBVHF5mrtvXHVp3T?access_key=<ACCESS KEY>
```

With the access key, the Ember.js dashboard app can then decrypt the source code and local variables downloaded from the server. As the access key passed as part of hash in the URL, the server cannot see it, without the access key, your source code and local variables are not visible by the server.

# Run demo

To run our demo

```
git clone git@github.com:victorlin/bugbuzz-python.git
```

install the project

```
virtualenv --no-site-packages .env
source .env/bin/activate
pip install -e .
```

and dependency used in the `demo.py`

```
pip install requests
```

then

```
python demo.py
```

It will open a new tab in your browser for debugging.

# Notice

 This is just a prototype, use it at your own risk
