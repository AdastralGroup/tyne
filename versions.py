from os import path
from gettext import gettext as _
import gui
from downloads import Kachemak

VERSION_LIST = None


def check_for_updates(game: Kachemak):
    """
    This function checks the local version against the list of remote versions and deems firstly, if an update is necessary, and secondarily, whether it's more efficient to update or reinstall.
    """

    # This probably was already communicated to the user in update_version_file(), but if version.txt doesn't exist, skip updating.
    if not path.exists(game.install_dir + "version.txt"):
        if gui.message_yes_no(_("No game installation detected at given sourcemods path. Do you want to install the game?")):
            return False
        else:
            gui.message_end(_("We have nothing to do. Goodbye!"), 0)

    try:
        game.get_installed_version()
    except ValueError:
        if gui.message_yes_no(_("We can't read the version of your installation. It could be corrupted. Do you want to reinstall the game?"), False):
            return False
        else:
            gui.message_end(_("We have nothing to do. Goodbye!"), 0)
    # End of checking, we definitely have a valid installation at this point
    # Now we have to see if there's a remote patch matching our local version

    # First, as a basic sanity check, do we know about this version at all?
    # We don't want to try to patch from 746 or some other nonexistent version.
    if not game.local_version_check():
        if gui.message_yes_no(_("The version of your installation is unknown. It could be corrupted. Do you want to reinstall the game?"), False):
            return False
        else:
            gui.message_end(_("We have nothing to do. Goodbye!"), 0)

    # Now we're checking the latest version, to see if we're already up-to-date.
    latest_version = game.get_version_list()
    if game.get_installed_version() == latest_version:
        if gui.message_yes_no(_("We think we've found an existing up-to-date installation of the game. Do you want to reinstall it?"), False):
            return False
        else:
            gui.message_end(_("We have nothing to do. Goodbye!"), 0)

    # Finally, we ensure our local version has a patch available before continuing.
    patches = game.get_version_list()["patches"]
    if game.get_installed_version() in patches:
        if gui.message_yes_no(_("An update is available for the game. Do you want to install it?"), None, True):
            if gui.message_yes_no(_("If running, please close your game client and/or game launcher. Confirm once they're closed."), None, True):
                return True
            else:
                gui.message_end(_("Exiting..."), 0)
        else:
            gui.message_end(_("We have nothing to do. Goodbye!"), 0)
    else:
        gui.message_end(_("An update is available, but no patch could be found for your game version. Try reinstalling?"), 0)
