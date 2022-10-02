## Requirements
- Python3.6 or higher
- [A spotify developer application](#how-to-create-a-spotify-developer-application)
- [Client ID and Secret of your application](#how-to-get-the-client-id-and-client-secret-from-your-application)

#

## Installation
- Fork the github repo
- Install the required libraries using "pip install -r requirements.txt"
- Start the script using "python3 main.py"
- When prompted, enter the requested settings(client id, client secret, ip, port, fetch delay)
- Once thats done, continue with [usage](#usage)

#

## Usage
- If you've successfully completed the [installation steps](#installation) you may continue here
- If its your first time launching the script, it'll start a web server and ask you to visit a specifc website, its required so that the script can get a unique token to login to your account
- Once your on the website, simply hit the "login to spotify" button, wait for a redirect and close the website
- If you see "Access token available! Please restart the application" in the console, you've done everything right and can now start the script again
- You're basically done here, just let the script run and check every once in a while if it errored
  
#

## How to create a spotify developer application
- visit [the spotify developer application site](https://developer.spotify.com/dashboard/applications) and, if prompted, login
- create a new application by clicking on "create an app"
- ![Create an app - dashboard](https://i.imgur.com/oXVwEm8.png)
- enter your desired application name, doesnt matter what you choose
- optional: enter a discription, there is no need to do this though
- agree to the terms of service and hit "create" 
- ![Create an app - popup](https://i.imgur.com/mmVkdx3.png)

#

## How to get the client id and client secret from your application
- visit [the spotify developer application site](https://developer.spotify.com/dashboard/applications) and, if prompted, login
- click on [your spotify application](#how-to-create-a-spotify-developer-application)
- on the left side of your screen you should see a few things, like the application name, description, status and your client id 
- ![Application panel](https://i.imgur.com/cduOSjf.png)
- copy the weird looking text next to "Client ID" and save that somewhere, you're going to need that later
- click on "show client secret" to reveal the application client secret and save that somewhere, you're going to need that later as well

## How to add a redirect URI
- visit [the spotify developer application site](https://developer.spotify.com/dashboard/applications) and, if prompted, login
- click on [your spotify application](#how-to-create-a-spotify-developer-application)
- You should see a green button called "edit settings" on your right side of the screen, click that
- Locate "Redirect URIs" and enter the same ip you've entered in [the installation steps](#installation) and hit "add"
- Hit "Save" and close the page