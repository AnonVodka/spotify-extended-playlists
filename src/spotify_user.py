import spotipy
from typing import Dict
from src.spotify_playlist import SpotifyPlaylist
from src.auth import SpotifyOAuthHandler

class SpotifyUser(spotipy.Spotify):
    oauth: SpotifyOAuthHandler

    def __init__(self, oauth_handler: SpotifyOAuthHandler):
        self.oauth = oauth_handler
        super().__init__(self.oauth.get_token())

        self.__dict__.update(self.me())

    def get_token(self) -> str:
        return self.oauth.get_token()

    def get_playlist(self, playlist_id: str) -> SpotifyPlaylist:
        return SpotifyPlaylist(playlist_id, self)

    def get_all_playlists(self) -> Dict[str, SpotifyPlaylist]:
        self.playlists = {}
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

