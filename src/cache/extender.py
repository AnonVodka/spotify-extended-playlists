import json
from os.path import exists
from os import makedirs, remove
from typing import Dict
from src.spotify_playlist import SpotifyPlaylist

class Extender:

    def __init__(self, path="cache/extended-playlists"):
        self.path = path
        if not exists(self.path):
            makedirs(self.path)

    def _fix_name(self, name: str) -> str:
        return name.replace("/", "-")

    def _path(self, id: str) -> str:
        return f"{self.path}/{id}.json"

    def _read_from_file(self, id: str) -> SpotifyPlaylist:

        if self.was_extended(id):
            with open(self._path(id)) as f:
                return (True, json.loads(f.read()))

        return (False, None)

    def was_extended(self, id: str) -> bool:
        """Returns wether or not the give playlist id was already extended before"""
        return exists(self._path(id))

    def add(self, playlist: SpotifyPlaylist, inherited_playlists, script_added_songs, user_added_songs) -> bool:
        """Adds the given playlist to the list of extended playlists. 
        Returns wether or not the playlist was added/updated"""

        if self.compare(playlist.id, playlist.snapshot_id):
            return False

        with open(self._path(playlist.id), 'w') as f:
            f.write(json.dumps({
                "name": playlist.name,
                "snapshot_id": playlist.snapshot_id,
                "total_playlists_inherited": len(inherited_playlists),
                "total_songs_inherited": len(script_added_songs),
                "inherited_playlists": inherited_playlists,
                "user_added_songs": user_added_songs
            }))

        return True

    def remove(self, id: str) -> None:
        """Removes the given playlist id from the cache"""
        if self.was_extended(id):
            remove(self._path(id))

    def get(self, id: str) -> Dict:
        """Gets the data for the given playlist id from the cache, if a cache file exists, and returns it"""
        (success, data) = self._read_from_file(id)

        if not success:
            return None

        return data

    def compare(self, id: str, snapshot_id: str) -> bool:
        """Returns wether or not the given playlist snapshot id 
        for the given playlist id matches the cached snapshot id"""

        (success, data) = self._read_from_file(id)

        return False if not success else data["snapshot_id"] == snapshot_id
