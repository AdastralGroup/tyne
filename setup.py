"""
This module is primarily related to helping
the rest of the application find what it needs.

This includes the path to the user's sourcemods
folder, the binary locations for things like Aria2
depending on their platform, etc.
"""
import sys
from os import environ, getcwd, path
from platform import system
from shutil import which
from rich import print
from gettext import gettext as _
import gui
import vars
if system() == 'Windows':
    import winreg


REGISTRY = 0
REGISTRY_KEY = 0

def sourcemods_path():
    """
    Find path to sourcemod folder.
    """
    if system() == 'Windows':
        try:
            global REGISTRY
            global REGISTRY_KEY
            if REGISTRY == 0:
                REGISTRY = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                REGISTRY_KEY = winreg.OpenKeyEx(REGISTRY, r'SOFTWARE\Valve\Steam', access=winreg.KEY_ALL_ACCESS)

            value = winreg.QueryValueEx(REGISTRY_KEY, 'SourceModInstallPath')
            return value[0]
        except Exception:
            return None
    else:
        try:
            sourcepath = None
            with open(path.expanduser(r'~/.steam/registry.vdf'), encoding="utf-8") as file:
                for _, line in enumerate(file):
                    if 'SourceModInstallPath' in line:
                        sourcepath = line[line.index('/home'):-1].replace(r'\\', '/')
                        break
                file.close()
            return sourcepath
        except Exception:
            return None

def setup_path_script():
    """
    Choose setup path, but without user interference.
    """
    if len(sys.argv) > 2:
        vars.INSTALL_PATH = sys.argv[2].rstrip('"')
    else:
        vars.INSTALL_PATH = sourcemods_path()
        if vars.INSTALL_PATH is not None:
            vars.INSTALL_PATH = vars.INSTALL_PATH.rstrip('"')
        else:
            vars.INSTALL_PATH = getcwd()

        gui.message(_("Installation location not specified, will assume: %s") % vars.INSTALL_PATH)

def setup_path(manual_path):
    """
    Choose setup path.
    """
    confirm = False
    install_path = sourcemods_path()
    if install_path is not None:
        vars.INSTALL_PATH = install_path.rstrip('\"')

    smodsfound = isinstance(vars.INSTALL_PATH, str)
    if smodsfound is True and manual_path is not True:
        gui.message(_("Sourcemods folder was automatically found at: %s") % vars.INSTALL_PATH)
        if gui.message_yes_no(_("Does that look correct?")):
            confirm = True
        else:
            setup_path(True)
            return
    else:
        gui.message(_("WARNING: Steam's sourcemods folder has not been found, or you chose not to use it."))
        if gui.message_yes_no(_("Would you like to extract in %s? You must move it to your sourcemods manually.") % getcwd()):
            vars.INSTALL_PATH = getcwd()
            confirm = True
        else:
            vars.INSTALL_PATH = gui.message_dir(_("Please, enter the location in which the game will be installed to.\n"))

    if not confirm:
        if not gui.message_yes_no(_("The game will be installed in %s\nDo you accept?") % vars.INSTALL_PATH):
            print(_("Reinitialising...\n"))
            setup_path(False)

