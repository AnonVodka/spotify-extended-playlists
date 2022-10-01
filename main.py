import threading
import re
import os
import spotipy

from spotipy.oauth2 import SpotifyOAuth
from bottle import Bottle, ServerAdapter, request
from time import sleep

from config import Config

import json

cfg = Config()

SPOTIPY_CLIENT_ID = cfg.CLIENT_ID
SPOTIPY_CLIENT_SECRET = cfg.CLIENT_SECRET
SPOTIPY_REDIRECT_URI = f'http://{cfg.IP}:{cfg.PORT}'
SCOPE = 'playlist-modify-public playlist-modify-private'
CACHE = '.spotipyoauthcache'


def get_diff_between_lists(a, b, c = None):
    not_in_a = []
    not_in_b = []

    for el in a:
        if c is None:
            if el not in b:
                not_in_b.append(el)
        else:
            if el not in b and el not in c:
                not_in_b.append(el)
    
    for el in b:
        if c is None:
            if el not in a:
                not_in_a.append(el)
        else:
            if el not in a and el not in c:
                not_in_a.append(el)

    return (not_in_a, not_in_b)

def remove_songs_from_playlist(sp: spotipy.Spotify, id, songs):
    if len(songs) > 100:
        for i in range(0, len(songs), 100):
            sp.playlist_remove_all_occurrences_of_items(id, songs[i:100+i])
    else:
        sp.playlist_remove_all_occurrences_of_items(id, songs)

def add_songs_to_playlist(sp: spotipy.Spotify, id, songs):
    if len(songs) > 100:
        for i in range(0, len(songs), 100):
            sp.playlist_add_items(id, songs[i:100+i])
    else:
        sp.playlist_add_items(id, songs)

def get_song_name(track):
    return f'{track["name"]} - {", ".join([x["name"] for x in track["artists"]])}'

def get_all_playlist_songs(sp: spotipy.Spotify, playlist):
    songs = {}

    total_songs = playlist["tracks"]["total"]
    id = playlist["id"]

    if total_songs == 0:
        return songs

    if total_songs > 100:
        for i in range(0, total_songs, 100):
            tmp = sp.playlist_items(id, limit=100, offset=i)

            for x in tmp:
                track = x["track"]
                songs.update({
                    track["id"]: get_song_name(track)
                })
    else:
        tmp = playlist["tracks"]["items"]
        for x in tmp:
            track = x["track"]
            songs.update({
                track["id"]: get_song_name(track)
            })

    return songs

def do_spotify_stuff(token, stop_server=False):

    if stop_server:
        print("Stopping http server")
        server.stop()

    print("Using token to create spotify object")
    sp = spotipy.Spotify(token)

    if not os.path.exists("extended-playlists"):
        os.makedirs("extended-playlists")

    while True:
        print("[#] Fetching user playlists")
        user_playlists = sp.user_playlists(cfg.CLIENT_USER_NAME)
        while user_playlists:
            for user_playlist in user_playlists['items']:

                user_playlist_id = user_playlist["id"]
                user_playlist_desc = user_playlist["description"].replace("&#x2F;", "/")

                if len(user_playlist_desc) == 0:
                    continue

                user_playlist = sp.playlist(user_playlist_id)
                user_playlist_name = user_playlist["name"].replace("/", "-")
                user_playlist_songs = get_all_playlist_songs(sp, user_playlist)

                songs_cache = user_playlist_songs

                user_playlist_songs = list(user_playlist_songs.keys())

                open(f"data/{user_playlist_name}.json", "w").write(json.dumps(user_playlist))

                if "extends:" not in user_playlist_desc:
                    # this playlist has a description
                    # but doesnt extend any other playlists
                    # so skip
                    continue

                user_playlist_desc = user_playlist_desc[user_playlist_desc.index("extends:"):]

                # get spotify playlist id from url
                urls = re.findall("(https?://[^\s]+)", user_playlist_desc)

                if len(urls) > 0:
                    # we found some urls in the description
                    # make sure they are valid spotify urls

                    if os.path.exists(f"extended-playlists/{user_playlist_id}.json") and len(user_playlist_songs) == 0:
                        print("[!] Playlist is empty, removing data file")
                        os.remove(f"extended-playlists/{user_playlist_id}.json")

                    songs_to_add = []

                    for url in urls:
                        if "open.spotify.com/playlist" not in url:
                            print(f"[!] Skipping {url} because its not a valid spotify playlist url")
                            continue

                        inherited_playlist_id = url.split("/")[-1].split("?")[0]

                        # basic checks to validate the authentizity of an id
                        if not re.match("[0-9A-Za-z_-]{22}", inherited_playlist_id):
                            print(f"[!] Skipping {inherited_playlist_id} as its not a valid id")
                            continue

                        inherited_playlist = sp.playlist(inherited_playlist_id)

                        inherited_songs = get_all_playlist_songs(sp, inherited_playlist)

                        songs_cache.update(inherited_songs)

                        songs_to_add += list(inherited_songs.keys())

                    if os.path.exists(f"extended-playlists/{user_playlist_id}.json"):
                        # this playlist was already extended once
                        # so get user added songs and script added songs 
                        # and do some comparison to see if the inherited playlist changed
                        # or if the user added/removed songs

                        print(f"[#] Playlist {user_playlist_id}-{user_playlist_name} was already extended before, comparing data to file")

                        info = json.loads(open(f"extended-playlists/{user_playlist_id}.json").read())

                        user_added_songs = info["user_added_songs"]
                        script_added_songs = info["script_added_songs"]   

                        # check if the user removed any songs
                        removed_songs = get_diff_between_lists(user_playlist_songs, user_added_songs, script_added_songs)[0]

                        if len(removed_songs) > 0:
                            print("[#] The user removed the following songs from their playlist: " + ", ".join([songs_cache.get(x, "UNKNOWN") for x in removed_songs]) )
                            user_added_songs = [x for x in user_added_songs if x not in removed_songs]

                        # get all songs that are arent in inherited_songs nor script_added_songs
                        # those are the songs the user has added manually
                        # and update user_added_songs
                        diff = get_diff_between_lists(user_playlist_songs, songs_to_add, script_added_songs)[1]
                        new_user_added_songs = get_diff_between_lists(user_added_songs, diff)[0]

                        if len(new_user_added_songs) > 0:
                            print("[!] The user added the following songs to their playlist: " + ", ".join([songs_cache.get(x, "UNKNOWN") for x in new_user_added_songs]))
                            user_added_songs += new_user_added_songs

                        # check if there are any differences between already inherited songs and the to inherite songs
                        # make sure that we are skipping user added songs
                        (not_in_a, not_in_b) = get_diff_between_lists(songs_to_add, script_added_songs, user_added_songs)

                        if len(not_in_a) == 0 and len(not_in_b) == 0:
                            print("[#] No songs to be added or removed")

                        else:
                            if len(not_in_a) > 0:
                                # songs got removed from the inherited playlist
                                # remove excessive songs from user playlist
                                print("[-] The following songs need to be removed: " + ', '.join([songs_cache.get(x, "UNKNOWN") for x in not_in_a]))   
                                script_added_songs = [x for x in script_added_songs if x not in not_in_a]
                                remove_songs_from_playlist(sp, user_playlist_id, not_in_a)

                            if len(not_in_b) > 0:
                                # songs got added to the inherited playlist
                                # add missing songs to the playlist
                                # get the difference between the existing songs and the songs we need to add
                                # so that we dont add songs that are already in the playlist coz the user added them lol
                                not_in_b = get_diff_between_lists(user_playlist_songs, not_in_b)[0]

                                print(user_playlist_songs)

                                print("[+] The following songs need to be added: " + ', '.join([songs_cache.get(x, "UNKNOWN") for x in not_in_b]))  

                                add_songs_to_playlist(sp, user_playlist_id, not_in_b)
                                script_added_songs += not_in_b
                        

                    else:
                        user_added_songs = user_playlist_songs
                        script_added_songs = get_diff_between_lists(user_added_songs, songs_to_add)[0]

                        if len(script_added_songs) == 0:
                            print("[!] No songs to be added as the user already has them all in their playlist")
                        else:
                            print("[#] The following songs need to be added: " + ", ".join([songs_cache.get(x, "UNKNOWN") for x in script_added_songs]))
                            add_songs_to_playlist(sp, user_playlist_id, script_added_songs)
                        
                    open(f"extended-playlists/{user_playlist_id}.json", "w").write(json.dumps({
                        "name": user_playlist_name,
                        "script_added_songs": script_added_songs,
                        "user_added_songs": user_added_songs
                    }))

                    open(f"data/{inherited_playlist_id}.json", "w").write(json.dumps(inherited_playlist))

            if user_playlists['next']:
                user_playlists = sp.next(user_playlists)
            else:
                user_playlists = None

        sleep(5)



sp_oauth = SpotifyOAuth( 
    SPOTIPY_CLIENT_ID, 
    SPOTIPY_CLIENT_SECRET,
    SPOTIPY_REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE 
)

token_info = sp_oauth.get_cached_token()

if token_info:
    do_spotify_stuff(token_info["access_token"])

else:
    class MyWSGIRefServer(ServerAdapter):
        server = None

        def run(self, handler):
            from wsgiref.simple_server import make_server, WSGIRequestHandler
            if self.quiet:
                class QuietHandler(WSGIRequestHandler):
                    def log_request(*args, **kw): pass
                self.options['handler_class'] = QuietHandler
            self.server = make_server(self.host, self.port, handler, **self.options)
            self.server.serve_forever()

        def stop(self):
            self.server.shutdown()

    server = MyWSGIRefServer(host=cfg.IP, port=cfg.PORT)

    app = Bottle()

    @app.route('/')
    def index():
            
        access_token = ""
        token_info = sp_oauth.get_cached_token()
        if token_info:
            print("Found cached token!")
            access_token = token_info['access_token']
        else:
            url = request.url
            code = sp_oauth.parse_response_code(url)
            if code != url:
                print("Found Spotify auth code in Request URL! Trying to get valid access token...")
                access_token = sp_oauth.get_access_token(code, False)

        if access_token:
            print("Access token available!")
            spotify_thread = threading.Thread(target=do_spotify_stuff, args=(access_token, True))
            print("Staring spotify thread")
            spotify_thread.start()
        else:
            return htmlForLoginButton()

    def htmlForLoginButton():
        auth_url = getSPOauthURI()
        htmlLoginButton = "<center><a href='" + auth_url + "'>Login to Spotify</a></center>"
        return htmlLoginButton

    def getSPOauthURI():
        auth_url = sp_oauth.get_authorize_url()
        return auth_url

    try:
        app.run(server=server)
    except:
        print('Bye')

