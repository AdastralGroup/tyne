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
INSTALLED = False

ARIA2C_BINARY = None
INSTALL_PATH = None
TF2C_PATH = None

SCRIPT_MODE = len(sys.argv) > 1

SOURCE_URL = 'https://tf2classic.org/tf2c/'
