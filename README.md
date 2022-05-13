# Spotter
Source code for a Discord bot built to notify you when a followed artist releases new music.

## Setup
To set it up, you'll need to make a discord bot account and configure it, details of which can be found here: https://discordpy.readthedocs.io/en/stable/discord.html
Once you've created the bot and joined it to your server, take the token and save it in a .env file as DISCORD_TOKEN=(token goes here).
Then, you'll need to set up a developer account on Spotify and make an application; you can do this here: https://developer.spotify.com/dashboard/applications
Once you've crated the developer account, take the client ID and client secret and save it in the same .env file as SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.
Then all you need to do is install requirements with pip install -r requirements.txt, run the bot with python3 spotter.py and you're ready to go!

## Bot Use
The bot uses the command prefix >spot, and the currently available commands are sample, follow, unfollow, and info.

\>spot sample will return a sampling of five tracks from a specified artist:

\>spot follow will follow a specified artist, checking every 8 hours for new releases and pinging you with a message once there is one:

\>spot unfollow will unfollow an artist you've followed:

\>spot info will return the information about an artist that has at least 1 follower, to include latest release info and which users are following them:

