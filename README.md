# Bugbuzz - easy to use online debugger

![Bugbuzz demo](/screencast.gif?raw=true )

# Dashboard shortcuts

Vim style shortcuts

 - C Continue
 - H Return
 - J Next
 - L Step


# Usage:

This is still a prototype stage service, you clone it

```
git clone git@github.com:victorlin/bugbuzz-python.git
```

run

```
virtualenv --no-site-packages .env
source .env/bin/activate
pip install -e .
```

then

```
python demo.py
```

It will open a new tab in your browser for debugging.

Notice:

 - This is just a prototype, use it at your own risk
 - The source code you are debugging (encountered breakpoints or pause) will be uploaded to the server
 - Safari is not working for an issue, use Chrome instead
