import spotipy

class SpotifyPlaylist():
    def __init__(self, playlist, user : spotipy.Spotify = None) -> None:

        if type(playlist) == str:
            self.__dict__ = user.playlist(playlist)
        elif type(playlist) == dict:
            self.__dict__ = playlist
        else:
            raise TypeError(f"[!] Type {type(playlist)} isn't support")

        self.user = user

    def _get_song_name(self, track):
        return f'{track["name"]} - {", ".join([x["name"] for x in track["artists"]])}'

    def get_all_songs(self) -> dict:

        if self.user == None:
            raise Exception("This function can't be used without giving a user object in the constructor!")

        songs = {}

        tracks = self.user.playlist_items(self.id, limit=100)
        total_songs = tracks["total"]
        def _add_tracks(_tracks):
            for x in _tracks["items"]:
                track = x["track"]
                songs.update({
                    track["id"]: self._get_song_name(track)
                })

        if total_songs == 0:
            return songs

        if total_songs > 100:
            for i in range(0, total_songs, 100):
                tracks = self.user.playlist_items(self.id, limit=100, offset=i)
                _add_tracks(tracks)
        else:
            _add_tracks(tracks)

        return songs

    def add_songs(self, songs: list) -> None:
        if self.user == None:
            raise Exception("This function can't be used without giving a user object in the constructor!")

        if len(songs) == 0: 
            return

        if len(songs) > 100:
            for i in range(0, len(songs), 100):
                self.user.playlist_add_items(self.id, songs[i:100+i])
        else:
            self.user.playlist_add_items(self.id, songs)

    def remove_songs(self, songs: list) -> None:

        if self.user == None:
            raise Exception("This function can't be used without giving a user object in the constructor!")

        if len(songs) == 0: 
            return

        if len(songs) > 100:
            for i in range(0, len(songs), 100):
                self.user.playlist_remove_all_occurrences_of_items(self.id, songs[i:100+i])
        else:
            self.user.playlist_remove_all_occurrences_of_items(self.id, songs)