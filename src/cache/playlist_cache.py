from os.path import exists
from os import makedirs, remove
from src.spotify_playlist import SpotifyPlaylist

class PlaylistCache:

    def __init__(self, cache_path="cache/playlist-cache"):
        self.cache_path = cache_path
        if not exists(self.cache_path):
            makedirs(self.cache_path)

    def _fix_name(self, name: str) -> str:
        return name.replace("/", "-")

    def _path(self, id: str) -> str:
        return f"{self.cache_path}/{id}.json"

    def _write_to_file(self, playlist: SpotifyPlaylist) -> None:
        with open(self._path(playlist.id), 'w') as f:
            f.write(playlist.toJson())

    def _read_from_file(self, id: str) -> SpotifyPlaylist:

        if self.was_cached(id):
            with open(self._path(id)) as f:
                return (True, SpotifyPlaylist.fromJson(f.read()))

        return (False, None)

    def was_cached(self, id: str) -> bool:
        """Returns wether or not the give playlist id was already cached before"""
        return exists(self._path(id))

    def add(self, playlist: SpotifyPlaylist) -> bool:
        """Adds the given playlist to the playlist cache. 
        Returns wether or not the playlist was added/updated"""
        id = playlist.id
        snapshot_id = playlist.snapshot_id

        if self.compare(id, snapshot_id):
            # playlist matches the cached playlist
            # no need to do anything else
            return False

        self._write_to_file(playlist)

        return True

    def remove(self, id: str) -> None:
        """Removes the given playlist id from the cache"""
        if self.was_cached(id):
            remove(self._path(id))

    def get(self, id: str) -> SpotifyPlaylist:
        """Gets the data for the given playlist id from the cache, if a cache file exists and returns it"""
        (success, data) = self._read_from_file(id)

        if not success:
            return None

        return data

    def compare(self, id: str, snapshot_id: str) -> bool:
        """Returns wether or not the given playlist snapshot id 
        for the given playlist id matches the cached snapshot id"""

        (success, data) = self._read_from_file(id)

        return False if not success else data.snapshot_id == snapshot_id
