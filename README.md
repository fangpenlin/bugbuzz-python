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

 - This is just a prototype, use it at your own risk
 - The source code and local variables you are debugging (encountered breakpoints or pause) will be uploaded to the server, but they will be **encrypted**, then decrypted on the dashboard, nobody can know the content without the access key.
