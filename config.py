from os import path, remove
import shutil
import json


class Config():
    def __init__(self):

        if not self.copy_example_config():
            self.write_config_values_from_user_input()

        self.check_config_values()
        self.get_config_values()

    def check_config_values(self):
        with open("./config.json", "r") as f:
            cfg = json.loads(f.read())
            f.close()
            vals = (cfg.get("SPOTIFY_CLIENT_ID"), cfg.get("SPOTIFY_CLIENT_SECRET"), cfg.get("IP"), cfg.get("PORT"), cfg.get("DELAY"))
            if None in vals or "CHANGEME" in vals:
                print("Some config values where invalid, regenerating config")

                remove("./config.json")
                self.copy_example_config()

                self.write_config_values_from_user_input()

                self.check_config_values()

    def get_config_values(self):
        """Reads the required credentials from the config file"""
        with open("./config.json", "r") as f:
            cfg = json.loads(f.read())
            f.close()
            self.CLIENT_ID = cfg.get("SPOTIFY_CLIENT_ID")
            self.CLIENT_SECRET = cfg.get("SPOTIFY_CLIENT_SECRET")
            self.IP = cfg.get("IP", "127.0.0.1")
            self.PORT = cfg.get("PORT", 8080)
            self.DELAY = cfg.get("DELAY", 15)

    def write_config_values_from_user_input(self):
        cfg = {"SPOTIFY_CLIENT_ID": None, "SPOTIFY_CLIENT_SECRET": None, "SPOTIFY_USER_NAME": None}
        cfg["SPOTIFY_CLIENT_ID"] = input("Please enter your spotify application client id which can be found under 'https://developer.spotify.com/dashboard/applications'/<application>:\n")
        cfg["SPOTIFY_CLIENT_SECRET"] = input("Please enter your spotify application client secret which can be found under 'https://developer.spotify.com/dashboard/applications'/<application>:\n")
        cfg["IP"] = input("Please enter the ip of your server or localhost if you're running it locally:\n")
        print("---!!! Make sure that the same ip is also listed in your 'Redirect URIs' in the application panel !!!---")
        cfg["PORT"] = int(input("Please enter the port that the auth server should run on (for example 8080):\n"))
        cfg["DELAY"] = int(input("Please enter the desired refresh delay in minutes:\n"))

        try:
            with open("./config.json", "w") as f:
                f.write(json.dumps(cfg))
                f.close()

            s = "Successfully set config variables"
            print("-"*len(s))
            print(s)
            print("-"*len(s))
        except BaseException as e:
            print(e)

    def copy_example_config(self):
        """Copies the default config"""
        if path.exists("./config.json"):
            return True
        else:
            shutil.copy("./config.example.json", "./config.json")
            return False