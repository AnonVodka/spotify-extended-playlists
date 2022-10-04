#!/usr/bin/env python3
import argparse, random, re

from datetime import datetime
from time import sleep
from src.config import Config
from src.auth import SpotifyOAuthHandler
from src.spotify_user import SpotifyUser

cfg = Config()

parser = argparse.ArgumentParser(
    description="Shuffles the given spotify playlist"
)
parser.add_argument("shuffle_amount", metavar="shuffle amount", type=int, help="Shuffle the playlist n times")
parser.add_argument("playlist", metavar="playlist id/link", type=str, nargs="+", help="The id/link of the playlist, seperate multiple links via space")

def main():

    args = parser.parse_args()

    matches = re.findall("[0-9A-Za-z_-]{22}", " ".join(args.playlist))

    if len(matches) == 0:
        print("[!] Invalid playlist link/id provided, please check your arguments")
        return

    oauth_handler = SpotifyOAuthHandler(
        cfg.SPOTIFY_CLIENT_ID, 
        cfg.SPOTIFY_CLIENT_SECRET, 
        "playlist-modify-public playlist-modify-private",
        cfg.IP,
        cfg.PORT
    )

    user = SpotifyUser(oauth_handler)

    if user.id != None:
        print(f"[#] Successfully logged into {user.display_name}({user.id})")
    else:
        raise Exception("[!] Something went wrong when trying to login to your account, please check you config and try again")

    for i, url in enumerate(matches):
        playlist = user.get_playlist(url)
        playlist_songs = list(playlist.get_all_songs().keys())
        playlist_desc = playlist.description


        print(f"[#] Shuffling {playlist.name}...")
        for _ in range(args.shuffle_amount):
            random.shuffle(playlist_songs)            

        playlist.remove_songs(playlist_songs)
        playlist.add_songs(playlist_songs)

        now = datetime.today()

        desc_len = len(playlist_desc)
        time_desc = f"Last shuffled on {now.strftime('%d.%m.%Y')} at {now.strftime('%H:%M:%S')}"
        if desc_len > 0:
            actual_desc = re.split("(Last shuffled on )+(\d+.)+at (\d+):(\d+):(\d+)", playlist_desc)[0]
            if len(actual_desc) == 0:
                user.user_playlist_change_details(user.id, playlist.id, description=time_desc)
            else: 
                if len(f"{actual_desc} {time_desc}") <= 300:
                    user.user_playlist_change_details(user.id, playlist.id, description=f"{actual_desc} {time_desc}")
        else:
            user.user_playlist_change_details(user.id, playlist.id, description=time_desc)
        
        if len(matches) > 1 and i != len(matches)-1:
            print("[#] Waiting 5 seconds to not overload the api..")
            sleep(5)

    print("[#] Successfully shuffled all playlists")
             

if __name__ == "__main__":
    main()