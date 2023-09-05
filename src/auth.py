from spotipy import SpotifyOAuth
import os
from bottle import Bottle, request

class SpotifyOAuthHandler(SpotifyOAuth):
    def __init__(self, client_id, client_secret, scope, ip="127.0.0.1", port="8080", cache_path=".auth-cache"):
        self.ip = ip
        self.port = port

        super().__init__( 
            client_id,
            client_secret,
            f"http://{ip}:{port}",
            scope=scope,
            cache_path=cache_path 
        )

        token = self.get_token()
        if token == None:            
            self.start_webserver()

    def get_token(self) -> str:        
        validation = self.validate_token(self.cache_handler.get_cached_token())
        return None if validation is None else validation.get("access_token", None)

    def start_webserver(self) -> None: 

        app = Bottle()

        @app.route('/')
        def index():
                
            url = request.url
            code = self.parse_response_code(url)

            if code != url:
                print("[#] Found Spotify auth code in Request URL! Trying to get valid access token...")
                access_token = self.get_access_token(code, False)
                if access_token:
                    print("[#] Access token available! Please restart the application")
                    os._exit(1)
                    
            return htmlForLoginButton()

        def htmlForLoginButton():
            auth_url = self.get_authorize_url()
            htmlLoginButton = "<center><a href='" + auth_url + "'>Login to Spotify</a></center>"
            return htmlLoginButton

        print(f"[#] Running web server on {self.ip}:{self.port}..")
        print(f"[#] Please visit the following link to proceed with the script..")
        print(f"\t\thttp://{self.ip}:{self.port}/")
        app.run(host=self.ip, port=self.port, quiet=True)