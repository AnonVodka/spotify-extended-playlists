#!/usr/bin/env python3
import random
import re
from os import makedirs, remove
from os.path import exists
import json

from time import sleep
from src.config import Config
from src.auth import SpotifyOAuthHandler
from src.utils import utils
from src.spotify_user import SpotifyUser
from src.spotify_playlist import SpotifyPlaylist

cfg = Config()



def main():

    if not exists("extended-playlists"):
        makedirs("extended-playlists")

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

                playlist_json_file_path = f"extended-playlists/{user_playlist_id}.json"

                if exists(playlist_json_file_path) and len(user_playlist_songs) == 0:
                    print("[#] Playlist is empty, removing data file")
                    remove(playlist_json_file_path)

                # inherited songs we need to add
                inherited_songs_to_add = []
                # a dictionary containing all inherited playlist ids and playlist songs
                inherited_playlists = {}
                # songs that got removed from an inherited playlist
                inherited_songs_to_remove = []

                for url in urls:
                    # extract id from playlist uri (spotify:playlist:<id> / open.spotify.com/playlist/<id>)
                    inherited_playlist_id = re.split("[:/]", url)[1]
                    if inherited_playlist_id == None:
                        print("[!] Couldn't extract playlist id from \"{url}\"!")
                        continue

                    inherited_playlist = SpotifyPlaylist(user.playlist(inherited_playlist_id), user)

                    inherited_playlist_songs = inherited_playlist.get_all_songs()

                    inherited_playlists.update({
                        inherited_playlist_id: list(inherited_playlist_songs.keys())
                    })

                    songs_cache.update(inherited_playlist_songs)

                    if exists(playlist_json_file_path):
                        data = json.loads(open(playlist_json_file_path).read())

                        inherited_playlists_data = data["inherited_playlists"]

                        # loop through all playlists we added previously
                        for _playlist_id, _playlist_songs in inherited_playlists_data.items():
                            # loop through all previously added songs of that playlist
                            for _song in _playlist_songs:
                                # if playlist is still being inheritated from and the song isnt in that said playlist
                                # and is also not in the songs the user has added themselves
                                if (_playlist_id in inherited_playlists.keys() 
                                    and _song not in inherited_playlists.get(_playlist_id)):
                                    # that means it got removed from the playlist and we need to queue it for removal
                                    inherited_songs_to_remove.append(_song)

                    # loop through the songs we need to add
                    for _song in inherited_playlist_songs.keys():
                        # check if the song isnt already in the playlist or is already queued to be added
                        if _song not in user_playlist_songs and _song not in inherited_songs_to_add:
                            # and add the songs
                            inherited_songs_to_add.append(_song)


                if len(inherited_songs_to_add) > 0:
                    if cfg.SHUFFLE_SONGS:
                        print("[#] Shuffling songs..")
                        for i in range(5):
                            random.shuffle(inherited_songs_to_add)

                    # remove any duplicates from the songs to add, so that we dont add the same song multiple times
                    inherited_songs_to_add, dups = utils.remove_duplicates_from_list(inherited_songs_to_add, True)  
                    dup_len = len(dups)
                    if dup_len > 0:
                        songs_to_add_len = len(inherited_songs_to_add)
                        print(f"[#] Removed {dup_len} duplicates from the song list, {songs_to_add_len} out of {songs_to_add_len + dup_len} songs left to process")

                if exists(playlist_json_file_path):
                    # this playlist was already extended once
                    # so get user added songs and script added songs 

                    print(f"[#] Playlist was already extended before, comparing data to file")

                    data = json.loads(open(playlist_json_file_path).read())

                    user_added_songs_data = data["user_added_songs"]
                    inherited_playlists_data = data["inherited_playlists"]

                    # songs previously added by the script
                    script_added_songs_data = []

                    # loop through all playlists we added previously
                    for _playlist_id, _playlist_songs in inherited_playlists_data.items():
                        # add the songs to our script_added_songs list, so we know what songs we've added
                        script_added_songs_data += list(_playlist_songs)

                        if cfg.AUTO_REMOVED_INHERITED_SONGS:
                            # if the playlist id of our previous inherited playlist isnt in our to inherit playlists
                            if _playlist_id not in inherited_playlists.keys():
                                # loop through the songs from that playlist
                                for _song in _playlist_songs:
                                    # check if the songs arent in any other playlist or the user didnt add the song manually
                                    if _song not in inherited_songs_to_add and _song not in user_added_songs_data:
                                        # and add them to the songs we need to remove
                                        inherited_songs_to_remove.append(_song)

                    # get all songs from user_added_songs and script_added_songs that arent in user_playlist_songs
                    # those are the songs that the user removed
                    user_removed_songs = utils.get_diff_between_lists(user_playlist_songs, user_added_songs_data, script_added_songs_data)[0]
                    if len(user_removed_songs) > 0:
                        print(f"[#] The user removed {len(user_removed_songs)} songs from their playlist: " + ", ".join([songs_cache.get(x, "UNKNOWN") for x in user_removed_songs]) )
                        user_added_songs_data = [x for x in user_added_songs_data if x not in user_removed_songs]

                    # get all songs that are arent in inherited_songs_to_add nor script_added_songs_data
                    # those are the songs the user has added manually
                    # and update user_added_songs
                    diff = utils.get_diff_between_lists(user_playlist_songs, inherited_songs_to_add, script_added_songs_data)[1]
                    new_user_added_songs = utils.get_diff_between_lists(user_added_songs_data, diff)[0]
                    if len(new_user_added_songs) > 0:
                        print(f"[#] The user added {len(new_user_added_songs)} songs to their playlist: " 
                        + ", ".join([songs_cache.get(x, "UNKNOWN") for x in new_user_added_songs]))
                        user_added_songs_data += new_user_added_songs

                    if len(inherited_songs_to_remove) == 0 and len(inherited_songs_to_add) == 0:
                        print("[#] No songs to be added or removed")

                    else:
                        if len(inherited_songs_to_remove) > 0:
                            print(f"[#] {len(inherited_songs_to_remove)} songs need to be removed from the playlist: " 
                                    + ", ".join([songs_cache.get(x, "UNKNOWN") for x in inherited_songs_to_remove]))
                            playlist.remove_songs(inherited_songs_to_remove)

                        if len(inherited_songs_to_add) > 0:
                            print(f"[#] {len(inherited_songs_to_add)} songs need to be added to the playlist: " 
                                    + ", ".join([songs_cache.get(x, "UNKNOWN") for x in inherited_songs_to_add]))
                            playlist.add_songs(inherited_songs_to_add)
                else:
                    user_added_songs_data = user_playlist_songs
                    # get all songs from songs_to_add that arent in user_added_songs_data
                    # those are the songs the script added
                    script_added_songs_data = utils.get_diff_between_lists(user_added_songs_data, inherited_songs_to_add)[0]

                    if len(script_added_songs_data) == 0:
                        print("[!] No songs to be added as the user has them all in their playlist already")
                    else:
                        print(f"[#] {len(script_added_songs_data)} songs need to be added to the playlist: " 
                            + ", ".join([songs_cache.get(x, "UNKNOWN") for x in script_added_songs_data]))
                        playlist.add_songs(script_added_songs_data)
                    
                open(playlist_json_file_path, "w").write(json.dumps({
                    "name": playlist_name,
                    "total_playlists_inherited": len(inherited_playlists),
                    "total_songs_inherited": len(script_added_songs_data),
                    "inherited_playlists": inherited_playlists,
                    "user_added_songs": user_added_songs_data
                }))

        print(f"[#] Fetching again in {cfg.DELAY} minutes ({cfg.DELAY * 60} seconds)")
        sleep(cfg.DELAY * 60)


if __name__ == "__main__":
    main()