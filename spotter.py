import tekore as tk
import json
import time
import os
from dotenv import load_dotenv

from discord import Game, Embed
from discord.ext import commands, tasks
from pathlib import Path

load_dotenv()
token_discord = os.getenv('DISCORD_TOKEN')
spotify_id = os.getenv('SPOTIFY_CLIENT_ID')
spotify_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
token_spotify = tk.request_client_token(spotify_id, spotify_secret)
data_file = Path("./data_file.json")

if data_file.is_file():
    data = data_file.open()
    data = json.load(data)

else:
    data = {}

description = "New track notification bot."
bot = commands.Bot(command_prefix='>spot ', description=description, activity=Game(name='>spot help'))
spotify = tk.Spotify(token_spotify, asynchronous=True)

async def search(query, qtype="tracks", years=[2019,2022], limit=20):
    if years is not None:
        results, = await spotify.search(f'artist:{query} year:{years[0]}-{years[1]}', types=(qtype,), limit=limit)
     else:
        results, = await spotify.search(f'artist:{query}', types=(qtype,), limit=limit)
    return results,

@bot.command()
async def sample(ctx, *, query: str = None):
    if query is None:
        await ctx.send("No search query specified.")
        return

    tracks, = search(query, limit=5)

    embed = Embed(title="Track search results", color=0x1DB954)
    embed.set_thumbnail(url="https://i.imgur.com/890YSn2.png")
    embed.set_footer(text="Reqeuested by " + ctx.author.display_name)
    for t in tracks.items:
        artist = t.artists[0].name
        url = t.external_urls["spotify"]

        message = "\n".join([
            "[Spotify](" + url + ")",
            ":busts_in_silhouette: " + artist,
            ":cd: " + t.album.name,
            ":calendar_spiral: " + t.album.release_date
        ])
        embed.add_field(name=t.name, value=message, inline=False)

    await ctx.send(embed=embed)


@bot.command()
async def follow(ctx, *, artist: str = None):
    """
    Command to follow an artist.
    """

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel and \
               msg.content.lower() in ["y", "n"]

    if artist is None:
        await ctx.send("No artist name provided.")
        return
    artists, = search(artist, qtype='artist', limit=1, artist=False)
    artist = artists.items[0]
    await ctx.send(f"Get notifications for {artist.name}? (y/n)")
    msg = await bot.wait_for('message', check=check, timeout=30)
    if msg.content.lower() == "y":
        if artist.name in data.keys():
            if msg.author.mention in data[artist.name]['mentions'][str(msg.channel.id)]:
                await ctx.send("You are already following this artist!")
                return
            if msg.channel in data[artist.name]['mentions'].keys():
                data[artist.name]['mentions'][msg.channel.id].append(msg.author.mention)
                data[artist.name]['followers'][msg.channel.id].append(msg.author.name)
            else:
                data[artist.name]['mentions'][msg.channel.id] = []
                data[artist.name]['followers'][msg.channel.id] = []
                data[artist.name]['mentions'][msg.channel.id].append(msg.author.mention)
                data[artist.name]['followers'][msg.channel.id].append(msg.author.name)
            with open(data_file, "w") as out:
                json.dump(data, out, indent="")
        else:
            tracks = []
            latest_releases, = search(artist.name)
            if len(latest_releases.items) == 0:
                latest_releases, = search(artist.name, years=[2012,2022])
            if len(latest_releases.items) == 0:
                await ctx.send(f"{artist.name} has not released any new music in the last decade."
                               f"\nAre you sure you want to follow?")
                msg = await bot.wait_for('message', check=check, timeout=30)
                if msg.content.lower() == "y":
                    latest_releases, = search(artist.name, years=None)
                else:
                    await ctx.send("Sorry bud. Exiting.")
                    return
            for t in latest_releases.items:
                other_artists = []
                for a in t.artists:
                    other_artists.append(a.id)
                if artist.id not in other_artists:
                    continue
                entry = {'album name': t.album.name,
                         'release date': t.album.release_date}
                tracks.append(entry)
            tracks = sorted(tracks, key=lambda x: x["release date"], reverse=True)
            last_release = (tracks[0]['release date'], tracks[0]['album name'])
            channel = "C" + str(msg.channel.id)
            data[artist.name] = {'followers': {channel: []},
                                 'id': artist.id,
                                 'last_release': last_release[0],
                                 'last_release_title': last_release[1],
                                 'mentions': {channel: []},
                                 'name': artist.name}
            data[artist.name]['mentions'][channel].append(msg.author.mention)
            data[artist.name]['followers'][channel].append(msg.author.name)
            with open(data_file, "w") as out:
                json.dump(data, out, indent="")
        await ctx.send(f"{msg.author.mention}, now following {artist.name}.")
        print(f"{msg.author.name}, now following {artist.name}.")
    else:
        await ctx.send("Follow canceled.")
        return


@bot.command()
async def unfollow(ctx, *, query: str = None):
    """
    Unfollow an artist.
    """

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel and \
               msg.content.lower() in ["y", "n"]

    if query is None:
        await ctx.send("No artist name provided.")
        return
    artists, = search(query, qtype="artist", limit=1)
    artist = artists.items[0]
    if artist.name not in data.keys():
        await ctx.send(f"The artist {artist.name} currently has no followers.")
        return
    elif ctx.author.mention not in data[artist.name]['mentions']:
        await ctx.send(f"You are not currently following {artist.name}.")
        return
    else:
        await ctx.send(f"Are you sure you want to unfollow {artist.name}?")
        msg = await bot.wait_for('message', check=check, timeout=30)
        if msg.content.lower() == "y":
            data[artist.name]['mentions'][msg.channel].remove(msg.author.mention)
            data[artist.name]['followers'][msg.channel].remove(msg.author.name)
            await ctx.send(f"Successfully unfollowed {artist.name}.")
            print(f"{msg.author.name} unfollowed {artist.name}.")
            if len(data[artist.name]['followers'][msg.channel]) == 0:
                del data[artist.name]['followers'][msg.channel]
                del data[artist.name]['mentions'][msg.channel]
            if len(data[artist.name]['followers']) == 0:
                del data[artist.name]
                print(f"{artist.name} deleted due to no followers.")
            with open(data_file, "w") as out:
                json.dump(data, out, indent="")
            return
        else:
            await ctx.send(f"Unfollow cancelled.")


@bot.command()
async def info(ctx, *, query: str = None):
    """
    Returns current follow information on an artist.
    """
    channel = "C" + str(ctx.channel.id)
    if query is None:
        await ctx.send("No artist name provided.")
        return
    artists, = search(query, qtype='artist', limit=1)
    artist = artists.items[0]
    if artist.name not in data.keys():
        await ctx.send(f"The artist {artist.name} currently has no followers.")
        return
    queried = data[artist.name]
    message = "\n".join([
        f"Artist Name: {queried['name']}",
        f"Spotify ID: {queried['id']}",
        f"Latest Release: {queried['last_release']}",
        f"Latest Release Title: {queried['last_release_title']}",
        f"Followers: {', '.join(queried['followers'][channel])}"
    ])
    await ctx.send(message)


@tasks.loop(hours=8)
async def update():
    print(f"Starting update @ {time.ctime()}.")
    total = len(data)
    updated = 0
    updates = []
    for artist in data:
        print(f"Checking {artist} releases...")
        tracks = []
        latest_releases, = search(artist)
        if len(latest_releases.items) == 0:
            continue
        for t in latest_releases.items:
            other_artists = []
            for a in t.artists:
                other_artists.append(a.id)
            if data[artist]['id'] not in other_artists:
                continue
            entry = {'album name': t.album.name,
                     'release date': t.album.release_date,
                     'id': t.album.id}
            tracks.append(entry)
        if len(tracks) == 0:
            continue
        tracks = sorted(tracks, key=lambda x: x["release date"], reverse=True)
        last_release = (tracks[0]['release date'], tracks[0]['album name'], tracks[0]['id'])
        if last_release[0] != data[artist]['last_release']:
            updated += 1
            data[artist]['last_release'] = last_release[0]
            data[artist]['last_release_title'] = last_release[1]
            updates.append(artist)
            for channel in data[artist]['followers']:
                chan = bot.get_channel(channel[1:])
                await chan.send(f"Attention {', '.join(data[artist]['mentions'][channel])}:\n"
                               f"New music by {artist}: {data[artist]['last_release_title']} \n"
                               f"https://open.spotify.com/album/{last_release[2]}")
    print(f" --- \n{total} artists queried. \nNew releases found for {updated} artists \n{', '.join(updates)}\n --- ")
    with open(data_file, "w") as out:
        json.dump(data, out, indent="")
    print("Update complete.")


@bot.event
async def on_ready():
    if not update.is_running():
        update.start()
    print(f"Bot up at {time.ctime()}.")

if __name__ == "__main__":
    bot.run(token_discord)