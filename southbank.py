import json
from jsonschema import validate

global SCHEMA
SCHEMA = json.load(open("schema.json","r"))
class Game:
    def __init__(self):
        self.title = ""
        self.data_dir = ""
        self.source_url = ""
        self.download_method = 0
class RemoteJson:
    def __init__(self):
        self.version = ""
        self.title = ""
        self.pubkey = ""
        self.authority_url = ""

    def importjson(self,json_as_string):
        newjson = json.loads(json_as_string)
        validate(newjson,schema=SCHEMA)
