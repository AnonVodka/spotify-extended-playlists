#!/usr/bin/env python3
import random
import re
import os
import json

from time import sleep
from src.config import Config
from src.auth import SpotifyOAuthHandler
from src.utils import utils
from src.spotify_user import SpotifyUser
from src.spotify_playlist import SpotifyPlaylist

cfg = Config()



def main():

    if not os.path.exists("extended-playlists"):
        os.makedirs("extended-playlists")

    oauth_handler = SpotifyOAuthHandler(
        cfg.SPOTIFY_CLIENT_ID, 
        cfg.SPOTIFY_CLIENT_SECRET, 
        "playlist-modify-public playlist-modify-private",
        cfg.IP,
        cfg.PORT
    )

    while True:

        user = SpotifyUser(oauth_handler)

        if user.id != None:
            print(f"[#] Successfully logged into {user.display_name}({user.id})")
        else:
            raise Exception("[!] Something went wrong when trying to login to your account, please check you config and try again")

        playlists = user.get_all_playlists()

        for playlist_name, playlist in playlists.items():
            desc = playlist.description

            if len(desc) == 0:
                # skip playlists that dont have a description
                continue

            if "extends:" not in desc:
                # this playlist has a description
                # but doesnt extend any other playlists
                # so skip
                continue

            user_playlist_id = playlist.id

            playlist_songs = playlist.get_all_songs()

            songs_cache = playlist_songs

            user_playlist_songs = list(playlist_songs.keys())

            to_inherit = desc[desc.index("extends:"):]

            # get spotify playlist id from uri
            urls = re.findall("(playlist[/:][0-9A-Za-z_-]{22})", to_inherit)

            if len(urls) > 0:
                print(f"[#] Playlist \"{playlist_name}(id: {user_playlist_id})\" extends {len(urls)} playlists")

                if os.path.exists(f"extended-playlists/{user_playlist_id}.json") and len(user_playlist_songs) == 0:
                    print("[#] Playlist is empty, removing data file")
                    os.remove(f"extended-playlists/{user_playlist_id}.json")

                songs_to_add = []
                inherited_playlist_ids = []

                for url in urls:
                    # extract id from playlist uri (spotify:playlist:<id> / open.spotify.com/playlist/<id>)
                    inherited_playlist_id = re.split("[:/]", url)[1]
                    if inherited_playlist_id == None:
                        print("[!] Couldn't extract playlist id from \"{url}\"!")
                        continue

                    inherited_playlist = SpotifyPlaylist(user.playlist(inherited_playlist_id), user)

                    inherited_playlist_ids += inherited_playlist_id

                    inherited_songs = inherited_playlist.get_all_songs()

                    songs_cache.update(inherited_songs)

                    songs_to_add += inherited_songs.keys()

                if cfg.SHUFFLE_SONGS:
                    print("[#] Shuffling songs..")
                    for i in range(5):
                        random.shuffle(songs_to_add)

                songs_to_add, dups = utils.remove_duplicates_from_list(songs_to_add, True)  

                dup_len = len(dups)
                if dup_len:
                    songs_to_add_len = len(songs_to_add)
                    print(f"[#] Removed {dup_len} duplicates from the song list, {songs_to_add_len} out of {songs_to_add_len + dup_len} songs left to add")

                if os.path.exists(f"extended-playlists/{user_playlist_id}.json"):
                    # this playlist was already extended once
                    # so get user added songs and script added songs 
                    # and do some comparison to see if the inherited playlist changed
                    # or if the user added/removed songs

                    print(f"[#] Playlist \"{playlist_name}(id: {user_playlist_id})\" was already extended before, comparing data to file")

                    info = json.loads(open(f"extended-playlists/{user_playlist_id}.json").read())

                    user_added_songs = info["user_added_songs"]
                    script_added_songs = info["script_added_songs"]   

                    # check if the user removed any songs
                    removed_songs = utils.get_diff_between_lists(user_playlist_songs, user_added_songs, script_added_songs)[0]

                    if len(removed_songs) > 0:
                        print("[#] The user removed the following songs from their playlist: " + ", ".join([songs_cache.get(x, "UNKNOWN") for x in removed_songs]) )
                        user_added_songs = [x for x in user_added_songs if x not in removed_songs]

                    # get all songs that are arent in inherited_songs nor script_added_songs
                    # those are the songs the user has added manually
                    # and update user_added_songs
                    diff = utils.get_diff_between_lists(user_playlist_songs, songs_to_add, script_added_songs)[1]
                    new_user_added_songs = utils.get_diff_between_lists(user_added_songs, diff)[0]

                    if len(new_user_added_songs) > 0:
                        print("[!] The user added the following songs to their playlist: " + ", ".join([songs_cache.get(x, "UNKNOWN") for x in new_user_added_songs]))
                        user_added_songs += new_user_added_songs

                    # check if there are any differences between already inherited songs and the to inherite songs
                    # make sure that we are skipping user added songs
                    (not_in_a, not_in_b) = utils.get_diff_between_lists(songs_to_add, script_added_songs, user_added_songs)

                    if len(not_in_a) == 0 and len(not_in_b) == 0:
                        print("[#] No songs to be added or removed")

                    else:
                        if len(not_in_a) > 0:
                            # songs got removed from the inherited playlist
                            # remove excessive songs from user playlist
                            print("[-] The following songs need to be removed: " + ', '.join([songs_cache.get(x, "UNKNOWN") for x in not_in_a]))   

                            script_added_songs = [x for x in script_added_songs if x not in not_in_a]

                            playlist.remove_songs(not_in_a)

                        if len(not_in_b) > 0:
                            # songs got added to the inherited playlist
                            # add missing songs to the playlist
                            # get the difference between the existing songs and the songs we need to add
                            # so that we dont add songs that are already in the playlist coz the user added them lol
                            new_not_in_b = utils.get_diff_between_lists(user_playlist_songs, not_in_b)[0]

                            if len(new_not_in_b) == 0:
                                print("[#] No songs to be added after removing already existing songs")
                                script_added_songs += not_in_b
                            else:
                                print("[+] The following songs need to be added: " + ', '.join([songs_cache.get(x, "UNKNOWN") for x in new_not_in_b]))  

                                playlist.add_songs(new_not_in_b)

                            script_added_songs += new_not_in_b  

                else:
                    user_added_songs = user_playlist_songs
                    script_added_songs = utils.get_diff_between_lists(user_added_songs, songs_to_add)[0]

                    if len(script_added_songs) == 0:
                        print("[!] No songs to be added as the user already has them all in their playlist")
                    else:
                        print("[#] The following songs need to be added: " + ", ".join([songs_cache.get(x, "UNKNOWN") for x in script_added_songs]))
                        playlist.add_songs(script_added_songs)
                    
                open(f"extended-playlists/{user_playlist_id}.json", "w").write(json.dumps({
                    "inherited_playlists": inherited_playlist_ids,
                    "name": playlist_name,
                    "script_added_songs": script_added_songs,
                    "user_added_songs": user_added_songs
                }))



        print(f"[#] Fetching again in {cfg.DELAY} minutes ({cfg.DELAY * 60} seconds)")
        sleep(cfg.DELAY * 60)


if __name__ == "__main__":
    main()