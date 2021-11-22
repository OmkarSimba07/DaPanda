import datetime
import aiohttp
import asyncio
import discord
import logging
import math
import pomice
import re
import time as t

from ._music.errors import *
from ._music.player import QueuePlayer as Player
from async_timeout import timeout
from discord.ext import commands
from helpers import paginator
from helpers.context import CustomContext as Context
from helpers.helper import convert_bytes
from typing import Union


URL_RX = re.compile(r'https?://(?:www\.)?.+')
HH_MM_SS_RE = re.compile(r"(?P<h>\d{1,2}):(?P<m>\d{1,2}):(?P<s>\d{1,2})")
MM_SS_RE = re.compile(r"(?P<m>\d{1,2}):(?P<s>\d{1,2})")
HUMAN_RE = re.compile(r"(?:(?P<m>\d+)\s*m\s*)?(?P<s>\d+)\s*[sm]")
OFFSET_RE = re.compile(r"(?P<s>(?:\-|\+)\d+)\s*s", re.IGNORECASE)

def setup(bot):
    bot.add_cog(Music(bot))

def format_time(milliseconds: Union[float, int]) -> str:
    hours, rem = divmod(int(milliseconds // 1000), 3600)
    minutes, seconds = divmod(rem, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

class Music(commands.Cog):
    """
    🎵 Commands related to playing music through the bot in a voice channel.
    """
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_before_invoke(self, ctx: Context):
        if (is_guild := ctx.guild is not None)\
            and ctx.command.name not in ('lyrics', 'current', 'queue', 'nodes', 'toggle', 'role', 'settings', 'dj'):
            await self.ensure_voice(ctx)

        if (is_guild := ctx.guild is not None)\
            and ctx.command.name in ('current', 'queue'):

            if (ctx.voice_client is None):
                raise NoPlayer

        return is_guild
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if (player := member.guild.voice_client) is None:
            player = self.bot.pomice.get_node().get_player(member.guild.id)
        
        if not player:
            return
        
        if member.id == self.bot.user.id \
            and after.channel:

            if not player.is_paused:
                await player.set_pause(True)
                await asyncio.sleep(1)
                await player.set_pause(False)
        
        if member.id == self.bot.user.id \
            and not after.channel:
                
            await player.destroy()

        if member.bot:
            return
        
        if member.id == player.dj.id \
            and not after.channel:
            members = self.get_members(player.channel.id)
            
            if len(members) != 0:
                for m in members:
                    if m == player.dj or m.bot:
                        continue
                    else:
                        player.dj = m
            else:
                return
            
            await player.text_channel.send(embed=discord.Embed(title=f'New DJ', description=f'The DJ has been assigned to {player.dj.mention}', color=discord.Color.green()))
            return
        
        if after.channel and\
            after.channel.id == player.channel.id \
            and player.dj not in player.channel.members \
            and player.dj != member:
            
            if not member.bot:
                player.dj = member
            else:
                return
            
            await player.text_channel.send(embed=discord.Embed(title=f'New DJ', description=f'The DJ has been assigned to {player.dj.mention}', color=discord.Color.green()))
            return

    @commands.Cog.listener()
    async def on_pomice_track_start(self, player: Player, track: pomice.Track):
        track: pomice.Track = player.current.original
        ctx: Context = track.ctx
        
        if player.loop == 1:
            return

        if player.loop == 2 and player.queue.is_empty:
            return

        player.message = await ctx.send(embed=self.build_embed(player), reply=False)

    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: Player, track: pomice.Track, reason: str):
        text: discord.TextChannel = player.text_channel
        channel: discord.TextChannel = player.channel
        player.clear_votes()

        if player.loop == 1:
            await player.play(track)
            return
        
        if player.loop == 2:
            player.queue.put(track)
        
        try:
            await player.message.delete()
        except discord.HTTPException:
            pass

        try:
            async with timeout(300): 
                track = await player.queue.get_wait()
                
                try:
                    await player.play(track, ignore_if_playing=True)
                except Exception as e:
                    self.bot.dispatch("pomice_track_end", player, track, "Failed playin the next track in a queue")
                    logging.error(e)
                    raise TrackFailed(track)
                
        except asyncio.TimeoutError:
            embed=discord.Embed(title='Left due to inactivity', color=discord.Color.red())
            embed.description=f'I\'ve left {channel.mention}, due to inactivity in the past 5 minutes.'
            try:
                await player.destroy()
            except:
                pass
            else:
                await text.send(embed=embed)
        else:
            pass  

    async def cog_command_error(self, ctx: Context, error):
        embed = getattr(error, 'embed', None) if hasattr(error, 'custom') else None
        if embed:
            await ctx.send(embed=embed)
        
    async def ensure_voice(self, ctx:Context):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        should_connect = ctx.command.name in ('play', 'connect', 'playnext', 'playnow')
        player = ctx.voice_client
        
        if ctx.command.name in ('connect') and player:
            raise AlreadyConnectedToChannel(ctx)

        if not ctx.author.voice or not (channel := ctx.author.voice.channel):
            raise NoConnection

        if not player:
            if not should_connect:
                raise NoVoiceChannel 
              
            if ctx.guild.afk_channel:
                if channel.id == ctx.guild.afk_channel.id:
                    raise AfkChannel

            permissions = channel.permissions_for(ctx.me)

            if not permissions.connect:
                raise NoPerms('CONNECT', channel)

            if not permissions.speak:
                raise NoPerms('SPEAK', channel)

            if channel.user_limit != 0:
                limit = channel.user_limit
                if len(channel.members) == limit:
                    raise FullVoiceChannel(ctx)

            player = await channel.connect(cls=Player)
            player.text_channel = ctx.channel
            player.dj = ctx.author
        
        else:
            if int(player.channel.id) != channel.id:
                raise IncorrectChannelError(ctx)
            if int(player.text_channel) != ctx.channel.id:
                raise IncorrectTextChannelError(ctx)

    def get_channel(self, id:int):
        return self.bot.get_channel(id)

    def get_members(self, channel_id:int):
        channel = self.bot.get_channel(int(channel_id))
        return list(member for member in channel.members if not member.bot)

    async def get_tracks(self, ctx: Context, query:str):
        return await ctx.voice_client.get_tracks(query.strip("<>"), ctx=ctx)

    def get_thumbnail(self, track:pomice.Track) -> Union[str, discord.embeds._EmptyEmbed]:
        if (thumbnail := track.info.get("thumbnail")):
            return thumbnail
        elif any(i in track.uri for i in ("youtu.be", "youtube.com")):
            return "https://img.youtube.com/vi/{}/maxresdefault.jpg".format(track.identifier)
        else:
            return discord.embeds.EmptyEmbed

    def build_embed(self, player:pomice.Player):
        track: pomice.Track = player.current
        
        if not track.spotify:
            track: pomice.Track = player.current.original

        if track.is_stream:
            length = "<:status_streaming:596576747294818305> Live Stream"
        else:
            length = format_time(track.length)

        title = track.title if not track.spotify else str(track.title)
        embed = discord.Embed(title=f"Now playing 🎵")
        embed.description=f"**[{title}]({track.uri})**"
        embed.set_thumbnail(url=self.get_thumbnail(track))
        embed.add_field(name="Duration:", value=length)
        embed.add_field(name="Requested by:", value=track.requester.mention)
        embed.add_field(name="Artist:" if not ", " in track.author else "Artists:", value=track.author)

        if track.uri.startswith("https://open.spotify.com/"):
            embed.set_footer(text="Spotify Track", icon_url='https://cdn.discordapp.com/emojis/904696493447974932.png?size=96')
        
        elif track.uri.startswith("https://soundcloud.com/"):
            embed.set_footer(text="SoundClound Track", icon_url="https://cdn.discordapp.com/emojis/314349923090825216.png?size=96")

        elif track.uri.startswith("https://www.youtube.com/"):
            embed.set_footer(text="YouTube Track", icon_url="https://cdn.discordapp.com/emojis/593301958660718592.png?size=96")
        
        else:
            pass
        
        return embed

    def is_privileged(self, ctx:Context):
        """Check whether the user have perms to be DJ"""
        player = ctx.voice_client 

        dj_only = self.bot.dj_only(ctx.guild)
        dj_role = self.bot.dj_role(ctx.guild)
        
        if not dj_only:
            return True

        elif dj_role and dj_role in ctx.author.roles:
            return True
        
        elif player.dj == ctx.author:
            return True

        elif ctx.author.guild_permissions.manage_roles:
            return True

        else:
            return False

    def required(self, ctx:Context):
        """Method which returns required votes based on amount of members in a channel."""
        members = len(self.get_members((ctx.voice_client).channel.id))
        return math.ceil(members / 2.5)

    @commands.command(aliases=["p",])
    async def play(self, ctx:Context, *, query: str):
        """Loads your input and adds it to the queue"""
        player = ctx.voice_client 
        
        try:
            results = await self.get_tracks(ctx, query)
        except pomice.TrackLoadError:
            raise LoadFailed
        
        if not results:
            raise NoMatches

        if isinstance(results, pomice.Playlist):
            tracks = results.tracks
            for track in tracks:
                player.queue.put(track)
            
            if results.spotify:
                thumbnail = results.thumbnail
            else:
                thumbnail = self.get_thumbnail(results.tracks[0])

            embed = discord.Embed(title = "Added a playlist to the queue")
            embed.set_thumbnail(url=thumbnail or discord.embeds.EmptyEmbed)
            embed.description = f'**[{results}]({query})** with {len(tracks)} songs.'
            await ctx.send(embed=embed)

        else:
            track = results[0]
            player.queue.put(track)

            embed=discord.Embed(title = "Added a track to the queue")
            embed.description = f"**[{track.title.upper()}]({track.uri})**"
            embed.set_thumbnail(url=self.get_thumbnail(track))
            await ctx.send(embed=embed)
            
        if not player.is_playing:
            await player.play(player.queue.get())

    @commands.command(aliases=["pn",])
    async def playnext(self, ctx:Context, *, query: str):
        """Loads your input and adds to the top of the queue"""
        player = ctx.voice_client 
        
        try:
            results = await self.get_tracks(ctx, query)
        except pomice.TrackLoadError:
            raise LoadFailed
        
        if not results:
            raise NoMatches

        if isinstance(results, pomice.Playlist):
            tracks = results.tracks
            for track in reversed(tracks):
                player.queue.put_at_front(track)
            
            if results.spotify:
                thumbnail = results.thumbnail
            else:
                thumbnail = self.get_thumbnail(results.tracks[0])

            embed = discord.Embed(title = "Added a playlist to the queue")
            embed.set_thumbnail(url=thumbnail or discord.embeds.EmptyEmbed)
            embed.description = f'**[{results}]({query})** with {len(tracks)} songs.'
            await ctx.send(embed=embed)

        else:
            track = results[0]
            player.queue.put_at_front(track)

            embed=discord.Embed(title = "Added a track to the queue")
            embed.description = f"**[{track.title.upper()}]({track.uri})**"
            embed.set_thumbnail(url=self.get_thumbnail(track))
            await ctx.send(embed=embed)
            
        if not player.is_playing:
            track = player.queue.get()
            await player.play(track)

    @commands.command(aliases=["pnow",])
    async def playnow(self, ctx:Context, *, query: str):
        """Loads your input and plays it instantly"""
        player = ctx.voice_client 
        
        try:
            results = await self.get_tracks(ctx, query)
        except pomice.TrackLoadError:
            raise LoadFailed
        
        if not results:
            raise NoMatches

        if isinstance(results, pomice.Playlist):
            tracks = results.tracks
            for track in reversed(tracks):
                player.queue.put_at_front(track)
            
            if results.spotify:
                thumbnail = results.thumbnail
            else:
                thumbnail = self.get_thumbnail(results.tracks[0])

            embed = discord.Embed(title = "Added a playlist to the queue")
            embed.set_thumbnail(url=thumbnail or discord.embeds.EmptyEmbed)
            embed.description = f'**[{results}]({query})** with {len(tracks)} songs.'
            await ctx.send(embed=embed)

        else:
            track = results[0]
            player.queue.put_at_front(track)

            embed=discord.Embed(title = "Added a track to the queue")
            embed.description = f"**[{track.title.upper()}]({track.uri})**"
            embed.set_thumbnail(url=self.get_thumbnail(track))
            await ctx.send(embed=embed)
        
        if player.loop == 1:
            player.loop = 0

        if not player.is_playing:
            track = player.queue.get()
            await player.play(track)
        else:
            await player.stop()

    @commands.command(aliases=["join",])
    async def connect(self, ctx:Context):
        """Connects the bot to your voice channel"""
        await ctx.send(embed=discord.Embed(title='Successfully Connected', description = f'Connected to {ctx.voice_client.channel.mention}'))

    @commands.command(aliases=["np",])
    async def current(self, ctx:Context):
        """Displays info about the current track in the queue"""
        player = ctx.voice_client
        if not player:
            raise NoPlayer

        if not player.is_playing:
            raise NoCurrentTrack
        
        await ctx.send(embed=self.build_embed(player))

    @commands.command(aliases=["dc", "begone", "fuckoff", "gtfo"])
    async def disconnect(self, ctx:Context):
        """Disconnects the player from its voice channel."""
        player = ctx.voice_client
        channel = player.channel
        if not self.is_privileged(ctx):
            raise NotAuthorized

        await player.destroy()
        await ctx.send(embed=discord.Embed(title=f"Successfully disconnected", description=f'Disconnected from {channel.mention}'))

    @commands.command(aliases=["next"])
    async def skip(self, ctx: Context):
        """Skips the currently playing track"""
        player = ctx.voice_client

        if not player.current:
            raise NoCurrentTrack

        if self.is_privileged(ctx):
            await player.skip()
        
        else:
            required = self.required(ctx)

            if required == 1:
                await player.skip()
                return
                
            if not player.current_vote:
                player.current_vote = ctx.command.name
                player.add_vote(ctx.author)
                
                embed = discord.Embed(title='A vote has been started')
                embed.description = '{} has started a vote for skipping [{}]({})'.format(ctx.author.mention, player.current.title, player.current.uri)
                embed.set_footer(text='Current votes: {} / {}'.format(len(player.votes), required))
                
                return await ctx.send(embed=embed)
        
            if ctx.author in player.votes:
                raise AlreadyVoted

            player.add_vote(ctx.author)
            if len(player.votes) >= required:
                embed = discord.Embed(title='Vote passed')
                embed.description = 'The required amout of votes ({}) has been reached'.format(required)
                embed.set_footer(text='Current votes: {} / {}'.format(len(player.votes), required))
                
                await ctx.send(embed=embed)
                await player.skip()
            else:
                await ctx.send(f'{ctx.author.mention} has voted')
                embed = discord.Embed(title='Vote added')
                embed.description = '{} has voted for skipping [{}]({})'.format(ctx.author.mention, player.current.title, player.current.uri)
                embed.set_footer(text='Current votes: {} / {}'.format(len(player.votes), required))

                await ctx.send(embed=embed)

    @commands.command(aliases=["stfu"])
    async def stop(self, ctx:Context):
        """Stops the currently playing track and returns to the beginning of the queue"""
        player = ctx.voice_client

        if not player.queue.is_empty:
            player.queue.clear()
        
        if player.loop == 1:
            player.loop = 0
        
        await player.stop()
        await ctx.send(embed=discord.Embed(title='Playback stopped', description = "The playback was stopped and queue cleared"))

    @commands.command()
    async def clear(self, ctx:Context):
        """Removes all tracks from the queue"""
        player = ctx.voice_client

        if player.queue.is_empty:
            raise QueueIsEmpty
            
        player.queue.clear()
        await ctx.send(embed=discord.Embed(title='Queue cleared', description = "The playback was stopped and queue cleared"))

    @commands.command(aliases=["q", "upcoming"])
    async def queue(self, ctx:Context):
        """Displays the current song queue"""
        player = ctx.voice_client
        
        if player.queue.is_empty:
            raise QueueIsEmpty
        
        info = []
        for track in player.queue:
            info.append(f'**[{track.title.upper()}]({track.uri})** ({format_time(track.length)})\n')
        
        menu = paginator.ViewPaginator(paginator.QueueMenu(info, ctx), ctx=ctx)
        await menu.start()
    
    @commands.command()
    async def seek(self, ctx:Context, *, time:str):
        """Seeks to a position in the track"""
        player = ctx.voice_client
        
        if not player.is_playing:
            raise NoCurrentTrack
        
        milliseconds = 0

        if match := HH_MM_SS_RE.fullmatch(time):
            milliseconds += int(match.group("h")) * 3600000
            milliseconds += int(match.group("m")) * 60000
            milliseconds += int(match.group("s")) * 1000
            new_position = milliseconds

        elif match := MM_SS_RE.fullmatch(time):
            milliseconds += int(match.group("m")) * 60000
            milliseconds += int(match.group("s")) * 1000
            new_position = milliseconds

        elif match := OFFSET_RE.fullmatch(time):
            milliseconds += int(match.group("s")) * 1000

            position = player.position
            new_position = position + milliseconds

        elif match := HUMAN_RE.fullmatch(time):
            if m := match.group("m"):
                if match.group("s") and time.lower().endswith("m"):
                    embed = discord.Embed(title='Invalid timestamp', color=discord.Color.red())
                    embed.add_field(name='Here are the supported timestamps:', value=(
                        "\n```yaml"
                        f"\n{ctx.clean_prefix}seek 01:23:30"
                        f"\n{ctx.clean_prefix}seek 00:32"
                        f"\n{ctx.clean_prefix}seek 2m 4s"
                        f"\n{ctx.clean_prefix}seek 50s"
                        f"\n{ctx.clean_prefix}seek +30s"
                        f"\n{ctx.clean_prefix}seek -23s"
                        "\n```"
                        ))

                    return await ctx.send(embed=embed)
                milliseconds += int(m) * 60000
            if s := match.group("s"):
                if time.lower().endswith("m"):
                    milliseconds += int(s) * 60000
                else:
                    milliseconds += int(s) * 1000

            new_position = milliseconds

        else:
            embed = discord.Embed(title='Invalid timestamp', color=discord.Color.red())
            embed.add_field(name='Here are the supported timestamps:', value=(
                "\n```yaml"
                f"\n{ctx.clean_prefix}seek 01:23:30"
                f"\n{ctx.clean_prefix}seek 00:32"
                f"\n{ctx.clean_prefix}seek 2m 4s"
                f"\n{ctx.clean_prefix}seek 50s"
                f"\n{ctx.clean_prefix}seek +30s"
                f"\n{ctx.clean_prefix}seek -23s"
                "\n```"
                ))

            return await ctx.send(embed=embed)

        if new_position < 0 or new_position > player.current.length-1:
            raise InvalidSeek
        

        await ctx.send(embed=discord.Embed(title='Track sought', description="The current track was sought to {}".format(format_time(new_position))))
        await player.seek(new_position)

    @commands.command()
    async def pause(self, ctx:Context):
        """Pauses playback (if possible)"""
        player = ctx.voice_client

        if not self.is_privileged(ctx):
            raise NotAuthorized
        
        if player.is_paused:
            raise PlayerIsAlreadyPaused
        
        await player.set_pause(True)
        await ctx.send(embed=discord.Embed(title='Track paused', description = "The current track was paused."))

    @commands.command()
    async def resume(self, ctx:Context):
        """Resumes playback (if possible)"""
        player = ctx.voice_client

        if not self.is_privileged(ctx):
            raise NotAuthorized
        
        if not player.is_paused:
            raise PlayerIsNotPaused
        
        await player.set_pause(False)
        await ctx.send(embed=discord.Embed(title='Track resumed', description = "The current track was resumed."))

    @commands.command(aliases=["vol"])
    async def volume(self, ctx:Context, volume:Union[int, str]):
        """Sets the player's volume; If you input "reset", it will set the volume back to default"""
        player = ctx.voice_client

        if not self.is_privileged(ctx):
            raise NotAuthorized
        
        if isinstance(volume, str):
            if volume.lower() == "reset":
                await player.set_volume(100)
                await ctx.send(embed=discord.Embed(title='Volume updated', description = f"The player's volume has been set up to `100%`"))
            else:
                raise InvalidInput
        
        if isinstance(volume, int):
            if volume >= 126 or volume <= 0:
                raise InvalidVolume
            await player.set_volume(volume)
            await ctx.send(embed=discord.Embed(title='Volume updated', description = f"The player's volume has been set up to `{volume}%`"))

    @commands.command()
    async def shuffle(self, ctx:Context):
        """Randomizes the current order of tracks in the queue"""
        player = ctx.voice_client

        if not self.is_privileged(ctx):
            raise NotAuthorized

        if player.queue.is_empty:
            raise NothingToShuffle

        player.queue.shuffle()
        await ctx.send(embed=discord.Embed(title='Queue randomized', description='The queue was shuffled'))

    @commands.group(invoke_without_command=True)
    async def loop(self, ctx:Context):
        await ctx.send_help(ctx.command)
        
    @loop.command()
    async def track(self, ctx:Context):
        """Starts looping your currently playing track"""
        player:Player = ctx.voice_client

        if not self.is_privileged(ctx):
            raise NotAuthorized

        if not player.current:
            raise NoCurrentTrack

        if player.loop == 1:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='Loop mode is already set to `TRACK`', color=discord.Color.red()))

        player.loop = 1
        await ctx.send(embed=discord.Embed(title='Looping current track', description='Loop mode has been set up to `TRACK`'))

    @loop.command()
    async def playlist(self, ctx:Context):
        """Starts looping your currently playing track"""
        player:Player = ctx.voice_client

        if not self.is_privileged(ctx):
            raise NotAuthorized
        
        if player.queue.is_empty:
            raise QueueIsEmpty

        if player.loop == 2:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='Loop mode is already set to `PLAYLIST`', color=discord.Color.red()))

        player.loop = 2
        await ctx.send(embed=discord.Embed(title='Looping playlist', description='Loop mode has been set up to `PLAYLIST`'))

    @loop.command()
    async def disable(self, ctx:Context):
        """Starts looping your currently playing track"""
        player:Player = ctx.voice_client

        if not self.is_privileged(ctx):
            raise NotAuthorized
        
        if player.loop == 0:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='Loop mode is already set to `DISABLED`', color=discord.Color.red()))

        player.loop = 0
        await ctx.send(embed=discord.Embed(title='Looping track', description='Loop mode was set to `DISABLED`'))

    @commands.command()
    async def lyrics(self, ctx:Context, *, query: str):
        """Searches for lyrics based on your query"""
        async with aiohttp.ClientSession() as session:
            lyrics = await session.get(f'https://evan.lol/lyrics/search/top?q={query}')
            lyrics = await lyrics.json()
        try:
            title = f'{lyrics["artists"][0]["name"]} - {lyrics["name"]}'
            href=f'https://open.spotify.com/track/{lyrics["id"]}'
            image = lyrics["album"]["icon"]["url"]
            text = lyrics["lyrics"]
            lyrics = [text[i:i+2000] for i in range(0, len(text), 2000)]
            menu = paginator.ViewPaginator(paginator.LyricsPageSource(title, href, lyrics, image, ctx),ctx=ctx)
            await menu.start()
        except KeyError:
            raise NoLyrics

    @commands.group(invoke_without_command=True)
    async def dj(self, ctx:Context):
        await ctx.send_help(ctx.command)

    @commands.check_any(commands.has_permissions(manage_roles=True) 
                       , commands.has_permissions(manage_guild=True) 
                       , commands.is_owner())
    @dj.command()
    async def toggle(self, ctx:Context):
        """Toggles wheneve a DJ is requered to use DJ"""
        state:bool = not (self.bot.dj_only(ctx.guild))

        await self.bot.db.execute(
            "INSERT INTO music(guild_id, dj_only) VALUES ($1, $2)"
            "ON CONFLICT (guild_id) DO UPDATE SET dj_only = $2",
            ctx.guild.id, state)

        self.bot.dj_modes[ctx.guild.id] = state
        await ctx.send(embed=discord.Embed(title='Control mode updated', description=f'DJ olny has been toggled to {state}'))

    @commands.check_any(commands.has_permissions(manage_roles=True) 
                       , commands.has_permissions(manage_guild=True) 
                       , commands.is_owner())
    @dj.command()
    async def role(self, ctx:Context, role:Union[discord.Role, str]):
        """Sets which role will be treated as DJ role. If you input 'remove' it will remove it"""
        if isinstance(role, str):
            if role.lower() == 'remove':
                await self.bot.db.execute(
                    "INSERT INTO music(guild_id, dj_role_id) VALUES ($1, $2) "
                    "ON CONFLICT (guild_id) DO UPDATE SET dj_role_id = $2",
                    ctx.guild.id, None)

                self.bot.dj_roles[ctx.guild.id] = None
                await ctx.send(embed=discord.Embed(title='DJ Role removed', description=f'DJ role has been `removed` from thos server', color=discord.Color.red()))
            else:
                raise InvalidInput
        
        else:
            await self.bot.db.execute(
                "INSERT INTO music(guild_id, dj_role_id) VALUES ($1, $2) "
                "ON CONFLICT (guild_id) DO UPDATE SET dj_role_id = $2",
                ctx.guild.id, role.id)

            self.bot.dj_roles[ctx.guild.id] = role.id
            await ctx.send(embed=discord.Embed(title='DJ Role updated', description=f'DJ role has been set to {role.mention}'))

    @dj.command()
    async def settings(self, ctx: Context):
        """Shows the music settings for the server"""
        player:Player = ctx.voice_client
        dj_only:bool = self.bot.dj_only(ctx.guild)
        dj_role = self.bot.dj_role(ctx.guild)
             
        if not player:
            dj_current = None
        else:
            dj_current = player.dj.mention

        embed=discord.Embed(title=f'Music settings for {ctx.guild.name}',
                            description=(
                                "\n```fix"
                                "\nDJ - this member can use DJ commands, no matter the settings"
                                "\n"
                                "\nDJ Role - anyone with that role (if it's set) can use DJ commands"
                                "\n"
                                "\nDJ Only - whenever everyone can use DJ commands"
                                "\n```"
                            ))
        embed.add_field(name='DJ', value=dj_current)
        embed.add_field(name='DJ Role', value=dj_role.mention if dj_role else None)
        embed.add_field(name='DJ Only', value=dj_only)

        await ctx.send(embed=embed)

    @dj.command()
    async def swap(self, ctx:Context, member:discord.Member = None):
        """Swap the current DJ to another member in the voice channel."""
        player:Player = ctx.voice_client
        
        if not self.bot.dj_only(ctx.guild):
            return await ctx.send(embed=discord.Embed(title='Error Occured', description='Cannot use this this command while `DJ Only` is set to `False`'))

        if not self.is_privileged(ctx): 
            raise NotAuthorized

        members = self.get_members(player.channel.id)

        if member and member not in members:
            return await ctx.send(embed=discord.Embed(title='Error Occured', description=f'{member.mention} is not currently in voice, so can not be a DJ', color=discord.Color.red()))
        
        if member and member == player.dj:
            return await ctx.send(embed=discord.Embed(title='Error Occured', description='Cannot swap DJ to the current DJ...', color=discord.Color.red()))

        if len(members) == 1:
            return await ctx.send(embed=discord.Embed(title='Error Occured', description='No more members to swap to', color=discord.Color.red()))

        if member:
            player.dj = member
            return await ctx.send(embed=discord.Embed(title=f'New DJ', description=f'The DJ has been assigned to {player.dj.mention}', color=discord.Color.green()))

        for m in members:
            if m == player.dj or m.bot:
                continue
            else:
                player.dj = m
                return await ctx.send(embed=discord.Embed(title=f'New DJ', description=f'The DJ has been assigned to {m.mention}', color=discord.Color.green()))

    @commands.command()
    async def nodes(self, ctx:Context):
        nodes = [x for x in self.bot.pomice.nodes.values()]
        raw = []

        for node in nodes:
            stats = node._stats

            before = t.monotonic()
            async with self.bot.session.get(node._rest_uri):
                now = t.monotonic()
                ping = round((now - before) * 1000)
            uptime = str(datetime.timedelta(milliseconds=stats.uptime))
            uptime = uptime.split('.')
            
            raw.append([
                {'Identifier': '`{}`'.format(node._identifier)}, 
                {'All Players': '`{}`'.format(stats.players_total)},
                {'Active Players': '`{}`'.format(stats.players_active)},
                {'Free RAM': '`{}`'.format(convert_bytes(stats.free))}, 
                {'Used RAM': '`{}`'.format(convert_bytes(stats.used))}, 
                {'All RAM': '`{}`'.format(convert_bytes(stats.allocated))}, 
                {'Ping': '`{} ms`'.format(ping)},
                {'Available': '`{}`'.format(node._available)}, 
                {'Uptime': '`{}`'.format(uptime[0])}
                      ])

        menu = paginator.ViewPaginator(paginator.NodesMenu(raw, ctx),ctx=ctx)
        await menu.start()
        

