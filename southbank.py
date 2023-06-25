import json
from jsonschema import validate
import setup
import httpx
from gettext import gettext as _
import gui
global SCHEMA
from pathlib import Path
from downloads import Kachemak
SCHEMA = json.load(open("schema.json","r"))


class Game:
    downloads_data = None
    def __init__(self,name,data_dir,source_url,download_method):
        self.name = name
        self.data_dir = data_dir
        self.source_url = source_url
        self.download_method = download_method
        self.install_dir = setup.sourcemods_path() + self.data_dir

    def fetch_dl_data(self):
        if self.download_method == 0: # kachemak
            self.downloads_data = Kachemak(False,setup.sourcemods_path(),self.data_dir,self.source_url)

    def get_installed_version(self): # need to check it exists locally first.
        self.update_version_file()
        local_version_file = open(self.install_dir + '.adastral_ver', 'r')
        local_version = local_version_file.read().rstrip('\n')
        return local_version

    def is_installed(self): ## awful
        try:
            self.get_installed_version()
        except Exception:
            return False
        return True
    def update_version_file(self): # this needs to be updated to cover all games....
        """
        The previous launcher/updater leaves behind a rev.txt file with the old internal revision number.
        To avoid file bloat, we reuse this, but replace it with the game's semantic version number.
        To obtain the game's semantic version number, we do some horrible parsing of the game's version.txt
        file, which is what the game itself uses directly to show the version number on the main menu, etc.
        """
        try:
            old_version_file = open(self.install_dir + 'version.txt', 'r')
            old_version = old_version_file.readlines()[1]
            before, sep, after = old_version.partition('=')
            if len(after) > 0:
                old_version = after
            old_version = old_version.replace('.', '')
            new_version_file = open(self.install_dir + '.adastral_ver', 'w')
            # We unconditionally overwrite rev.txt since version.txt is the canonical file.
            new_version_file.write(old_version)
            new_version_file.close()
            old_version_file.close()
            return True
        except FileNotFoundError:
            if gui.message_yes_no(_("We can't read the version of your installation. It could be corrupted. Do you want to reinstall the game?"), False):
                return False
            else:
                gui.message_end(_("We have nothing to do. Goodbye!"), 0)

    def local_version_check(self):
        pass

    def set_install_dir(self, val):
        self.install_dir = val
        if self.downloads_data != None:
            self.downloads_data.INSTALL_PATH = Path(val).parents[0]
            self.downloads_data.DATA_DIR = Path(val).name



class RemoteJson:
    def __init__(self):
        self.version = ""
        self.pubkey = ""
        self.authority_url = ""
        self.games = []

    def importjson(self,json_as_string):
        newjson = json.loads(json_as_string)
        validate(newjson,schema=SCHEMA)
        self.version = newjson["ver"]
        self.authority_url = newjson["authority_url"]
        self.pubkey = newjson["authority_pub_key"]
        games = newjson["games"]
        for x in games:
            game = Game(x["name"],x["data_dir"],self.authority_url + x["source"],x["versioning"])
            self.games.append(game)

