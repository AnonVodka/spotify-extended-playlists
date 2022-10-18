import spotipy
import json
from datetime import datetime
from typing import Dict
from src.spotify_playlist import SpotifyPlaylist
from src.auth import SpotifyOAuthHandler

class SpotifyUser(spotipy.Spotify):
    oauth: SpotifyOAuthHandler
    last_login: str
    playlists: dict[str, SpotifyPlaylist] = {}

    def __init__(self, oauth_handler: SpotifyOAuthHandler):
        self.oauth = oauth_handler
        super().__init__(self.oauth.get_token())

        self.__odict__ = self.__dict__
        self.__dict__.update(self.me())
        
    def check_login(self) -> bool:
        if self.oauth.is_token_expired(self.oauth.cache_handler.get_cached_token()):
            super().__init__(self.oauth.get_token())
            self.__dict__.update(self.me())
            return True

        return False

    def get_playlist(self, playlist_id: str) -> SpotifyPlaylist:
        return SpotifyPlaylist(playlist_id, self)

    def get_all_playlists(self) -> Dict[str, SpotifyPlaylist]:
        _playlists = self.user_playlists(self.id)

        while _playlists:
            for playlist in _playlists.get("items"):
                playlist = SpotifyPlaylist(playlist, self)
                self.playlists.update({
                    playlist.name: playlist
                })
            if _playlists['next']:
                _playlists = self.next(_playlists)
            else:
                _playlists = None

        return self.playlists

