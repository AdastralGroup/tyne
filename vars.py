"""
Tiny module that currently just establishes
the temp paths and some variables for other
modules to use.
"""
from platform import system
import sys
import tempfile

if system() == 'Windows':
    TEMP_PATH = tempfile.gettempdir()
else:
    TEMP_PATH = '/var/tmp/'

# For determining whether we're installing or updating/repairing the game


SOUTHBANK = ""
INSTALL_PATH = ""
SCRIPT_MODE = len(sys.argv) > 1
LAUNCHER_SOURCE_URL = 'https://adastral.net/southbank/'

BLACKLIST_URL = 'https://tf2classic.org/serverlist/blacklist.php'
BLACKLIST_PATH = '/tf2classic/cfg/server_blacklist.txt'

UPDATE_HASH_URL_WINDOWS = LAUNCHER_SOURCE_URL + 'tf2cd_sha512sum_windows'
UPDATE_HASH_URL_LINUX = LAUNCHER_SOURCE_URL + 'tf2cd_sha512sum_linux'

UPDATE_DOWNLOAD_URL = 'https://tf2classic.com/download'

# Only on Linux
TO_SYMLINK = [
    ["bin/server.so", "bin/server_srv.so"]
]
