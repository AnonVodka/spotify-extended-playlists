from os import path, remove
import shutil
import json


class Config():
    def __init__(self):

        if not self.copy_example_config():
            self.write_config_values_from_user_input()

        self.check_config_values()
        self.get_config_values()

    def check_config_values(self) -> None:
        with open("./config.json", "r") as f:
            cfg = json.loads(f.read())
            f.close()
            vals = (cfg.get("SPOTIFY_CLIENT_ID"), cfg.get("SPOTIFY_CLIENT_SECRET"), cfg.get("IP"), cfg.get("PORT"))
            if None in vals or "CHANGEME" in vals:
                print("Some config values where invalid, regenerating config")

                remove("./config.json")
                self.copy_example_config()

                self.write_config_values_from_user_input()

                self.check_config_values()

    def get_config_values(self) -> None:
        """Reads the required credentials from the config file"""
        with open("./config.json", "r") as f:
            cfg = json.loads(f.read())
            f.close()
            self.SPOTIFY_CLIENT_ID = cfg.get("SPOTIFY_CLIENT_ID")
            self.SPOTIFY_CLIENT_SECRET = cfg.get("SPOTIFY_CLIENT_SECRET")
            self.IP = cfg.get("IP", "127.0.0.1")
            self.PORT = cfg.get("PORT", 8080)
            self.DELAY = cfg.get("DELAY", 15)
            self.SHUFFLE_SONGS = cfg.get("SHUFFLE_SONGS", False)

            with open("./config.json", "w") as f:
                f.write(json.dumps(self.__dict__))
                f.close()

    def write_config_values_from_user_input(self) -> None:
        cfg = {}
        cfg["SPOTIFY_CLIENT_ID"] = input("Please enter your spotify application client id which can be found under 'https://developer.spotify.com/dashboard/applications'/<application>:\n")
        cfg["SPOTIFY_CLIENT_SECRET"] = input("\nPlease enter your spotify application client secret which can be found under 'https://developer.spotify.com/dashboard/applications'/<application>:\n")
        print("\n---!!! Make sure that the same ip is also listed in your 'Redirect URIs' in the application panel !!!---")
        cfg["IP"] = input("Please enter the ip of your server or localhost if you're running it locally:\n")
        cfg["PORT"] = input("\nPlease enter the port that the auth server should run on (for example 8080):\n")
        cfg["DELAY"] = int(input("\nPlease enter the desired refresh delay in minutes:\n"))
        cfg["SHUFFLE_SONGS"] = True if "y" == input("\nDo you want the script to shuffle the songs its going to add(y/n):\n") else False

        try:
            with open("./config.json", "w") as f:
                f.write(json.dumps(cfg))
                f.close()

            s = "Successfully set config variables"
            print("-"*len(s))
            print(s)
            print("-"*len(s))
            for k, v in cfg.items():
                print(f" - {k}: {v}")
            print("-"*len(s))
        except BaseException as e:
            print(e)

    def copy_example_config(self) -> bool:
        """Copies the default config"""
        if path.exists("./config.json"):
            return True
        else:
            shutil.copy("./config.example.json", "./config.json")
            return False