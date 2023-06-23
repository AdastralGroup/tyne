import json
from jsonschema import validate
import httpx
from gettext import gettext as _
import gui
global SCHEMA
SCHEMA = json.load(open("schema.json","r"))


class KachemakData:
    def __init__(self,dl):
        self.dl_url = dl
        self.version_list = {}
        try:
            version_remote = httpx.get(self.dl_url + 'versions.json')
            self.version_list = json.loads(version_remote.text)
        except httpx.RequestError:
            gui.message_end(_("Could not get version list. If your internet connection is fine, the servers could be having technical issues."), 1)

class Game:
    downloads_data = {}
    def __init__(self):
        self.name = ""
        self.data_dir = ""
        self.source_url = ""
        self.download_method = 0
        self.local = False

    def fetch_dl_data(self):
        if self.download_method == 0: # kachemak
            self.downloads_data = KachemakData(self.source_url)



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
            game = Game()
            game.name = x["name"]
            game.data_dir = x["data_dir"]
            game.source_url = self.authority_url + x["source"]
            game.download_method = x["versioning"]
            game.download_opts = x["download_opts"]
            self.games.append(game)

