#!/usr/bin/env python3
from ctypes import util
import random
import re
import sys
import json

from os import mkdir, remove
from os.path import exists
from time import sleep
from src.cache.playlist_cache import PlaylistCache
from src.cache.song_cache import SongsCache
from src.cache.extender import Extender
from src.config import Config
from src.logging import Logging
from src.auth import SpotifyOAuthHandler
from src.utils import utils
from src.spotify_user import SpotifyUser
from src.spotify_playlist import SpotifyPlaylist

cfg = Config()

cache = PlaylistCache()
songs_cache = SongsCache()
extender = Extender()

logging = Logging(cfg)

def exception_handler(type, msg, traceback):
    if issubclass(type, KeyboardInterrupt):
        sys.__excepthook__(type, msg, traceback)
        return

    logging.exception(type, msg, traceback)

sys.excepthook = exception_handler

def main():

    if not exists("extended-playlists"):
        mkdir("extended-playlists")

    oauth_handler = SpotifyOAuthHandler(
        cfg.SPOTIFY_CLIENT_ID, 
        cfg.SPOTIFY_CLIENT_SECRET, 
        "playlist-modify-public playlist-modify-private",
        cfg.IP,
        cfg.PORT
    )

    user = SpotifyUser(oauth_handler)

    if user.id != None:
        logging.log(f"[#] Successfully logged into {user.display_name}({user.id})")

    while True:

        if user.check_login():
            logging.log("[#] Refreshed login token")

        if user.id == None:
            raise Exception("[!] Something went wrong when trying to login to your account, please check you config and try again")

        playlists = user.get_all_playlists()

        for user_playlist in playlists.values():
            desc = user_playlist.description
            if len(desc) == 0 or "extends:" not in desc:
                continue
            uris = re.findall("(playlist[/:][0-9A-Za-z_-]{22})", desc)
            if len(uris) == 0: 
                continue
            ids = re.findall("[0-9A-Za-z_-]{22}", " ".join(uris))
            if len(ids) == 0:
                continue

            user_playlist_id = user_playlist.id
            user_playlist_snapshot_id = user_playlist.snapshot_id
            user_playlist_songs = []

            logging.log(f"[#] Playlist \"{user_playlist.info()}\" extends {len(ids)} playlists")

            # a dictionary containing all inherited playlist ids, songs and snapshot_id
            inherited_playlists = {}
            # songs that got removed from an inherited playlist
            inherited_songs_to_remove = []
            # inherited songs we need to add
            inherited_songs_to_add = []

            if cache.compare(user_playlist_id, user_playlist_snapshot_id):
                logging.log(f"[#] \t - playlist matches cache, getting data from cache")
                # the playlists match
                # so get the data from file
                user_playlist_songs = list(cache.get(user_playlist_id).songs.keys())
            else:
                logging.log(f"[!] \t - playlist doesnt match the cache or was never cached, getting playlist data from api")
                # the playlists do not match, so get the data from the api
                user_playlist_songs = list(user_playlist.get_all_songs().keys())

                if len(user_playlist_songs) == 0 and cache.was_cached(user_playlist_id):
                    logging.log("[#] Playlist is empty, removing data file")
                    extender.remove(user_playlist_id)

            # loop through all playlists that we need to inherit from
            for inherited_playlist_id in ids:
                # create playlist object 
                inherited_playlist = SpotifyPlaylist(inherited_playlist_id, user)
                
                inherited_playlist_snapshot_id = inherited_playlist.snapshot_id

                inherited_playlist_songs = {}

                if cache.was_cached(inherited_playlist_id):
                    if cache.compare(inherited_playlist_id, inherited_playlist_snapshot_id):
                        # playlist was cached before and matches the cached data
                        logging.log(f"[#] Inherited playlist \"{inherited_playlist.info()}\" hasn't changed since we last fetched its songs, getting data from file")
                        inherited_playlist_songs = cache.get(inherited_playlist_id).songs
                    else: 
                        logging.log(f"[!] Inherited playlist \"{inherited_playlist.info()}\" changed, getting data from api")
                        # playlist doesnt match the cached data
                        inherited_playlist_songs = inherited_playlist.get_all_songs() 

                        # update cache
                        cache.add(inherited_playlist)       
                else:
                    logging.log(f"[!] Inherited playlist \"{inherited_playlist.info()}\" was never fetched from, getting data from api")
                    # playlist wasnt cached before
                    inherited_playlist_songs = inherited_playlist.get_all_songs()

                    # cache the playlist we inherited songs from
                    cache.add(inherited_playlist)


                inherited_playlists.update({
                    inherited_playlist_id: {
                        "songs": list(inherited_playlist_songs.keys())
                    }
                })

                songs_cache.add_songs(inherited_playlist_songs)

                # loop through the songs
                for _song in inherited_playlist_songs.keys():
                    # check if the song isnt already in the playlist or is already queued to be added
                    if _song not in user_playlist_songs and _song not in inherited_songs_to_add:
                        # and add the songs
                        inherited_songs_to_add.append(_song)

                if extender.was_extended(user_playlist_id):
                    data = extender.get(user_playlist_id)
                    _inherited_playlists_data = data.get("inherited_playlists")
                    for _id_, _data in _inherited_playlists_data.items():
                        for _song in _data["songs"]:
                            # if playlist is still being inheritated from and the song isnt in that said playlist
                            # and is also not in the songs the user has added themselves
                            if (_id_ in inherited_playlists.keys() 
                                and _song not in inherited_playlists.get(_id_).get("songs")):
                                # that means it got removed from the playlist and we need to queue it for removal
                                inherited_songs_to_remove.append(_song)


            songs_to_add_len = len(inherited_songs_to_add)
            if songs_to_add_len > 0:
                if cfg.SHUFFLE_SONGS:
                    logging.log("[#] Shuffling songs..")
                    for i in range(5):
                        random.shuffle(inherited_songs_to_add)

                # remove any duplicates from the songs to add, so that we dont add the same song multiple times
                inherited_songs_to_add, dups = utils.remove_duplicates_from_list(inherited_songs_to_add, True)  
                dup_len = len(dups)
                if dup_len > 0:
                    logging.log(f"[#] Removed {dup_len} duplicates from the song list, {songs_to_add_len} out of {songs_to_add_len} songs left to process")


            if extender.was_extended(user_playlist_id):
                changed = False
                # playlist was extended before
                logging.log(f"[#] Playlist was extended before, comparing data to cache")

                # get the data from the cache
                data = extender.get(user_playlist_id)

                # check if the user playlist matches the cache data from the extender
                if extender.compare(user_playlist_id, user_playlist_snapshot_id):
                    # if they match, the user hasnt changed the playlist at all
                    logging.log("[#] Snapshot ids match!")
                else:
                    # if they dont match, it means that the user changed something in the playlist
                    # that can be the description, added/removed songs or changed the name so
                    # we need to queue an update for the extender, so that we have the newest snapshot id 
                    changed = True

                # songs previously added by the script
                script_added_songs_data = []
                user_added_songs_data = data.get("user_added_songs")

                # loop through all playlists we added previously
                for _playlist_id, _playlist_data in data.get("inherited_playlists").items():
                    # add the songs to our script_added_songs list, so we know what songs we've added
                    _playlist_songs = _playlist_data["songs"]
                    script_added_songs_data += list(_playlist_songs)

                    # auto remove inherited songs
                    if cfg.AUTO_REMOVED_INHERITED_SONGS:
                        if _playlist_id not in inherited_playlists:
                            # the playlist isnt inherited from anymore
                            # so remove all inherited songs
                            for _song in _playlist_songs:
                                # only queue the song for removal if another playlist isnt adding the same song
                                if _song not in inherited_songs_to_add and _song not in user_added_songs_data:
                                    inherited_songs_to_remove.append(_song)

                # get all songs from user_added_songs and script_added_songs that arent in user_playlist_songs
                # those are the songs that the user removed
                user_removed_songs = utils.get_diff_between_lists(user_playlist_songs, user_added_songs_data, script_added_songs_data)[0]
                if len(user_removed_songs) > 0:
                    logging.log(f"[#] The user removed {len(user_removed_songs)} songs from their playlist:")
                    logging.log(", ".join([songs_cache.get(x) for x in user_removed_songs]), False)
                    user_added_songs_data = [x for x in user_added_songs_data if x not in user_removed_songs]


                
                # get all songs that are arent in inherited_songs_to_add nor script_added_songs_data
                # those are the songs the user has added manually
                # and update user_added_songs
                diff = utils.get_diff_between_lists(user_playlist_songs, inherited_songs_to_add, script_added_songs_data)[1]
                new_user_added_songs = utils.get_diff_between_lists(user_added_songs_data, diff)[0]
                if len(new_user_added_songs) > 0:
                    logging.log(f"[#] The user added {len(new_user_added_songs)} songs to their playlist:")
                    logging.log(", ".join([songs_cache.get(x) for x in new_user_added_songs]), False)
                    user_added_songs_data += new_user_added_songs

                if len(inherited_songs_to_remove) == 0 and len(inherited_songs_to_add) == 0:
                    logging.log("[#] No songs to be added or removed")

                else:
                    if len(inherited_songs_to_remove) > 0:
                        logging.log(f"[#] {len(inherited_songs_to_remove)} songs need to be removed from the playlist:")
                        logging.log(", ".join([songs_cache.get(x) for x in inherited_songs_to_remove]), False)
                        user_playlist.remove_songs(inherited_songs_to_remove)

                    if len(inherited_songs_to_add) > 0:
                        logging.log(f"[#] {len(inherited_songs_to_add)} songs need to be added to the playlist:")
                        logging.log(", ".join([songs_cache.get(x) for x in inherited_songs_to_add]), False)
                        user_playlist.add_songs(inherited_songs_to_add)
                
                # change this to use the actualy songs that the script added and not all songs
                # eq. remove duplicates and songs that were added by the user

                # fetch new playlist data from api so we have an up2date snapshot id
                if changed:
                    user_playlist = SpotifyPlaylist(user_playlist_id, user_playlist.user)
                    user_playlist.get_all_songs()

                extender.add(user_playlist, inherited_playlists, script_added_songs_data, user_added_songs_data)
            else:
                # playlist wasnt extended before
                # this is the first time we touch the playlist
                # get the current playlist songs, those are the songs the user added themselves 
                # and save them to the cache

                logging.log(f"[#] Playlist was never extended before, creating new cache entry")

                # we removed the duplicates now remove all songs that are already in the playlist
                inherited_songs_to_add = utils.get_diff_between_lists(user_playlist_songs, inherited_songs_to_add)[0]

                if len(inherited_playlist_songs) == 0:
                    # we have no songs to add anymore, all of them are already in the playlist
                    logging.log("[#] No songs to be added as the user has them all in their playlist already")
                else:
                    logging.log(f"[#] {len(inherited_songs_to_add)} songs need to be added to the playlist:")
                    logging.log(", ".join([songs_cache.get(x) for x in inherited_songs_to_add]), False)
                    user_playlist.add_songs(inherited_songs_to_add)

                # fetch new playlist data from api so we have an up2date snapshot id
                user_playlist = SpotifyPlaylist(user_playlist_id, user_playlist.user)
                user_playlist.get_all_songs()
                extender.add(user_playlist, inherited_playlists, inherited_songs_to_add, user_playlist_songs)
            
            # fetch new playlist data from api so we have an up2date snapshot id
            cache.add(user_playlist)

        logging.log(f"[#] Fetching again in {cfg.DELAY} minutes ({cfg.DELAY * 60} seconds)")
        sleep(cfg.DELAY * 60)


if __name__ == "__main__":
    main()