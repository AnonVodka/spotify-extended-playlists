import json
from typing import Dict
from os import makedirs
from os.path import exists


class SongsCache:

    cache: Dict[str, str] = {}

    def __init__(self, cache_path="cache/songs-cache"):
        self.cache_path = cache_path

        if not exists(self.cache_path):
            makedirs(self.cache_path)

        if exists(f"{self.cache_path}/songs.json"):
            with open(f"{self.cache_path}/songs.json") as f:
                self.cache = json.loads(f.read())

    def update_cache(self):
        with open(f"{self.cache_path}/songs.json", "w") as f:
            f.write(json.dumps(self.cache, indent=4))

    def add_song(self, id: str, name: str, updateFile: bool = True):
        """Adds a song to the cache file"""

        if id not in self.cache.keys():
            self.cache.update({
                id: name
            })

        if updateFile:
            self.update_cache()


    def add_songs(self, songs: Dict[str, str]):
        for id, name in songs.items():
            self.add_song(id, name, False)
        
        self.update_cache()

    def get(self, id: str) -> str:
        return self.cache.get(id, "unknown")
