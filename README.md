# SlapPy
SlapPy is the Python support and generation code for [Slapp](https://github.com/kjhf/SplatTag) and [Dola](https://github.com/kjhf/DolaBot).
Code on [Github](https://github.com/kjhf/SlapPy).

## Requirements
- Python 3.9+
* Create a `.env` in the repository root with the following values:

```py
# Required values:
# Source address for Battlefy backend
CLOUD_BACKEND="https://xxxxx.cloudfront.net"
# Path to SplatTagConsole for Slapp things
SLAPP_CONSOLE_PATH=".../SplatTagConsole.dll"
# Path to the Slapp App Data folder
SLAPP_DATA_FOLDER=".../SplatTag"

# Optional values depending on requirements:
# Database variables if using the database, which are:
DATABASE_HOST="localhost:5000"
DATABASE_NAME="database"
DATABASE_USER="user"
DATABASE_PASSWORD="user"
# A Discord bot token if using the backtrace:
BOT_TOKEN="xxxxxx.xxxxxx.xxxxxx"
# Challonge credentials if using Challonge downloaders
CHALLONGE_API_KEY="xxxx"
CHALLONGE_USERNAME="YourUsername"
# Smash GG credentials if using Smash GG downloaders 
SMASH_GG_API_KEY="xxxx"
```

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
