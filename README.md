# SlapPy
SlapPy is the Python support and generation code for [Slapp](https://github.com/kjhf/SplatTag) and [Dola](https://github.com/kjhf/DolaBot).
Code on [Github](https://github.com/kjhf/SlapPy).

## Requirements
- Python 3.9+
- A root `tokens` module, which should contain:
    - Database variables if using the database, which are:
        - HOST = Database host address e.g. localhost:5000
        - DATABASE = Database name
        - USER = Database username
        - PASSWORD = Database user password
    - A Discord bot token if using the backtrace:
        - BOT_TOKEN = 'xxxxxx.xxxxxx.xxxxxx'
    - Source address for Battlefy backend
        - CLOUD_BACKEND = 'https://xxxxx.cloudfront.net'
    - Challonge credentials if using Challonge downloaders
        - CHALLONGE_API_KEY = 'xxxx'
        - CHALLONGE_USERNAME = Your username
    - Smash GG credentials if using SmashGG downloaders 
        - SMASH_GG_API_KEY = 'xxxx'
    - Slapp data folder for default loading from a path
        - SLAPP_APP_DATA = 'xxxx\\SplatTag'

## Distribution
The following commands should be entered into the venv console:

Windows:

    rmdir /S build
    rmdir /S dist
    py -m pip install --upgrade build
    py -m build
    py -m pip install --upgrade twine
    py -m twine upload dist/*

Linux:

    rm -r build
    rm -r dist
    python3 -m pip install --upgrade build
    python3 -m build
    python3 -m pip install --upgrade twine
    python3 -m twine upload dist/*
