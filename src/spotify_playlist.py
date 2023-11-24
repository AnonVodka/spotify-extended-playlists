import spotipy
import json
import src

import os

class SpotifyPlaylist:
    def __init__(self, playlist, user : spotipy.Spotify = None) -> None:

        if type(playlist) == str:
            self.__dict__ = user.playlist(playlist)
        elif type(playlist) == dict:
            self.__dict__ = playlist
        else:
            raise TypeError(f"[!] Type {type(playlist)} isn't support")

        self.user = user

    def info(self) -> str:
        return f"{self.name}(id: {self.id})"

    def _get_song_name(self, track):
        track_type = track["type"]
        if track_type == "episode":
            return track["name"]
        return f'{track["name"]} - {", ".join([x["name"] for x in track["artists"]])}'

    def get_all_songs(self) -> dict:

        if self.user == None:
            raise Exception("This function can't be used without giving a user object in the constructor!")

        self.songs = {}

        tracks = self.user.playlist_items(self.id, limit=100)
        total_songs = tracks["total"]

        if total_songs == 0:
            return self.songs

        while tracks:
            for track in tracks["items"]:

                if track["track"] == "None" or track["track"] == None:
                    continue

                self.songs.update({
                    track["track"]["id"]: self._get_song_name(track["track"])
                })

            if tracks["next"]:
                tracks = self.user.next(tracks)
            else:
                tracks = None

        return self.songs

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

    def toJson(self) -> str:
        ret = {}
        for k, v in self.__dict__.items():
            if type(v) is not src.spotify_user.SpotifyUser:
                ret.update({
                    k: v
                })
        return json.dumps(ret, indent=4)

    @staticmethod
    def fromJson(json_str: str):
        obj = json.loads(json_str)
        return SpotifyPlaylist(obj)
