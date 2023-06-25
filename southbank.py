import json
from jsonschema import validate
import setup
import httpx
from gettext import gettext as _
import gui
global SCHEMA
from pathlib import Path
import vars
from downloads import Kachemak
SCHEMA = json.load(open("schema.json","r"))





class RemoteJson:
    def __init__(self):
        self.version = ""
        self.pubkey = ""
        self.authority_url = ""
        self.games = []
        url = vars.LAUNCHER_SOURCE_URL + "/meta.json"
        newjson = json.loads(url)
        validate(newjson,schema=SCHEMA)
        self.version = newjson["ver"]
        self.authority_url = newjson["authority_url"]
        self.pubkey = newjson["authority_pub_key"]
        games = newjson["games"]
        for x in games:
            if x["versioning"] == 0:
                game = Kachemak(x["name"],x["data_dir"],self.authority_url + x["source"])
            self.games.append(game)

    def prettyprint(self):
        arr = []
        for num,game in zip(self.games,range(0,len(self.games))):
            try:
                z = game.get_installed_version()
                arr.append([num, game.name, "Yes", game.latest_ver, z])
            except:
                arr.append([num,game.name,"No",game.latest_ver,""])
