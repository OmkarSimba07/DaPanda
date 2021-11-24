import discord
import typing
import re
import os
import inspect

from inspect import Parameter
from discord import errors
from discord.ext import commands
from helpers import helper
from helpers import paginator
from .utils import time as time
from deep_translator import GoogleTranslator
from deep_translator.exceptions import LanguageNotSupportedException as UnsupportedLanguage
from helpers.context import CustomContext as Context

import helpers.consts as consts

class Utility(commands.Cog):
    """
        🛠️ Text and utility commands, mostly to display information about a server.
    """
    def __init__(self, client):
        self.client = client

    async def generate_perms(self, member:discord.Member):
        perms = [permission for permission in member.guild_permissions]
        allowed = [(f"✅ `{perm}`".replace('guild', 'server').replace('_', ' ').title()) for perm, value in perms if value]
        denied = [(f"❎ `{perm}`".replace('guild', 'server').replace('_', ' ').title()) for perm, value in perms if not value]

        if len(denied) == 0:
            allowed = ['✅ `Administartor`']

        
        embed = discord.Embed(color=member.color)
        embed.add_field(name='Allowed Permissions ({})'.format(len(allowed)), value='\n'.join(allowed), inline=True)
        if len(denied) > 0:
            embed.add_field(name='Denied Permissions ({})'.format(len(denied)), value='\n'.join(denied), inline=True)
        embed.set_author(name='Showing permissions for {}'.format(member.name), icon_url=member.display_avatar)
        
        return embed

    @commands.command(aliases=['av', 'pfp'])
    async def avatar(self, ctx: Context, *, member: typing.Union[discord.Member, discord.User] = None):
        """Displays a user's avatar"""
        user: discord.User = member or ctx.author
        embed = discord.Embed(title='Showing avatar for {}'.format(user.name))
        embed.set_image(url=user.display_avatar.replace(size=1024).url)
        if user.avatar.is_animated():
            embed.description = f"[PNG]({user.display_avatar.replace(format='png', size=1024).url}) | "\
                                f"[JPG]({user.display_avatar.replace(format='jpg', size=1024).url}) | "\
                                f"[JPEG]({user.display_avatar.replace(format='jpeg', size=1024).url}) | "\
                                f"[WEBP]({user.display_avatar.replace(format='webp', size=1024).url}) | "\
                                f"[GIF]({user.display_avatar.replace(format='gif', size=1024).url})"
        else:
            embed.description = f"[PNG]({user.display_avatar.replace(format='png', size=1024).url}) | "\
                                f"[JPG]({user.display_avatar.replace(format='jpg', size=1024).url}) | "\
                                f"[JPEG]({user.display_avatar.replace(format='jpeg', size=1024).url}) | "\
                                f"[WEBP]({user.display_avatar.replace(format='webp', size=1024).url}) | "

        await ctx.send(embed=embed)   
    
    @commands.command()
    async def banner(self, ctx:Context, *, member: typing.Union[discord.Member, discord.User] = None):
        """Displays a user's banner"""
        member: discord.User = member or ctx.author
        fetched_user = await self.client.fetch_user(member.id)
        
        if fetched_user.banner:
            embed = discord.Embed(title='Showing the banner of {}'.format(member.name), color=member.color)
            embed.set_image(url=fetched_user.banner.replace(size=1024).url)

            if fetched_user.banner.is_animated():
                banner =f"[PNG]({fetched_user.banner.replace(format='png', size=1024).url}) | "\
                        f"[JPG]({fetched_user.banner.replace(format='jpg', size=1024).url}) | "\
                        f"[JPEG]({fetched_user.banner.replace(format='jpeg', size=1024).url}) | "\
                        f"[WEBP]({fetched_user.banner.replace(format='webp', size=1024).url}) | "\
                        f"[GIF]({fetched_user.banner.replace(format='gif', size=1024).url})"
            else:
                banner =f"[PNG]({fetched_user.banner.replace(format='png', size=1024).url}) | "\
                        f"[JPG]({fetched_user.banner.replace(format='jpg', size=1024).url}) | "\
                        f"[JPEG]({fetched_user.banner.replace(format='jpeg', size=1024).url}) | "\
                        f"[WEBP]({fetched_user.banner.replace(format='webp', size=1024).url})"
            embed.description = banner
            await ctx.send(embed=embed)

        else:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='{} has no banner'.format(member.mention)))

    @commands.command(aliases=['uinfo', 'ui', 'userinfo'])
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @commands.guild_only()
    async def whois(self, ctx: commands.Context, *, member: typing.Optional[discord.Member]):
        """
        Shows a user's information. If not specified or it fails to find it, shows your own.
        """
        member = member or ctx.author
        fetched_user = await self.client.fetch_user(member.id)
   
        flags = helper.get_user_badges(member, fetched_user)
        if len(flags) != 0:
            flags = ', '.join(flags)
        else:
            flags = consts.CUSTOM_TICKS[False]

        joined = sorted(ctx.guild.members, key=lambda mem: mem.joined_at)
        pos = joined.index(member)
        positions = []
        for i in range(-5, 5):
            line_pos = pos + i
            if line_pos < 0:
                continue
            if line_pos >= len(joined):
                break
            positions.append("{0:<4}{1}{2:<20}".format(str(line_pos + 1) + ".", " " * 1 + ("> " if joined[line_pos] == member else "  "), f"{joined[line_pos]} ({joined[line_pos].joined_at.strftime('%d/%m/%Y')}) {(' ' * 10)}"))
        join_pos = "{}".format("\n".join(positions))

        if fetched_user.display_avatar.is_animated():
            avatar =f"[PNG]({fetched_user.display_avatar.replace(format='png', size=1024).url}) | "\
                    f"[JPG]({fetched_user.display_avatar.replace(format='jpg', size=1024).url}) | "\
                    f"[JPEG]({fetched_user.display_avatar.replace(format='jpeg', size=1024).url}) | "\
                    f"[WEBP]({fetched_user.display_avatar.replace(format='webp', size=1024).url}) | "\
                    f"[GIF]({fetched_user.display_avatar.replace(format='gif', size=1024).url})"
        
        else:
            avatar =f"[PNG]({fetched_user.display_avatar.replace(format='png', size=1024).url}) | "\
                    f"[JPG]({fetched_user.display_avatar.replace(format='jpg', size=1024).url}) | "\
                    f"[JPEG]({fetched_user.display_avatar.replace(format='jpeg', size=1024).url}) | "\
                    f"[WEBP]({fetched_user.display_avatar.replace(format='webp', size=1024).url})"

        if fetched_user.banner:
            if fetched_user.banner.is_animated():
                banner =f"[PNG]({fetched_user.banner.replace(format='png', size=1024).url}) | "\
                        f"[JPG]({fetched_user.banner.replace(format='jpg', size=1024).url}) | "\
                        f"[JPEG]({fetched_user.banner.replace(format='jpeg', size=1024).url}) | "\
                        f"[WEBP]({fetched_user.banner.replace(format='webp', size=1024).url}) | "\
                        f"[GIF]({fetched_user.banner.replace(format='gif', size=1024).url})"
            else:
                banner =f"[PNG]({fetched_user.banner.replace(format='png', size=1024).url}) | "\
                        f"[JPG]({fetched_user.banner.replace(format='jpg', size=1024).url}) | "\
                        f"[JPEG]({fetched_user.banner.replace(format='jpeg', size=1024).url}) | "\
                        f"[WEBP]({fetched_user.banner.replace(format='webp', size=1024).url})"
        
        mobile = {
            discord.Status.online: consts.statuses.ONLINE,
            discord.Status.idle: consts.statuses.IDLE,
            discord.Status.dnd: consts.statuses.DND,
            discord.Status.offline: consts.statuses.OFFLINE
        }[member.mobile_status]
        
        web = {
            discord.Status.online: consts.statuses.ONLINE,
            discord.Status.idle: consts.statuses.IDLE,
            discord.Status.dnd: consts.statuses.DND,
            discord.Status.offline: consts.statuses.OFFLINE
        }[member.web_status]
        
        desktop = {
            discord.Status.online: consts.statuses.ONLINE,
            discord.Status.idle: consts.statuses.IDLE,
            discord.Status.dnd: consts.statuses.DND,
            discord.Status.offline: consts.statuses.OFFLINE
        }[member.desktop_status]

        status = (
            f"[🖥️ {desktop}] **|** "
            f"[🌐 {web}] **|** "
            f"[📱 {mobile}]"
        )
    
        custom_activity = discord.utils.find(lambda act: isinstance(act, discord.CustomActivity), member.activities)
        status_str = f"{discord.utils.remove_markdown(custom_activity.name)}" if custom_activity and custom_activity.name else consts.CUSTOM_TICKS[False]

        activity = discord.utils.find(lambda act: isinstance(act, discord.Activity)\
                                               or isinstance(act, discord.Spotify)\
                                               or isinstance(act, discord.Game)\
                                               or isinstance(act, discord.Streaming), member.activities)
        if activity:
            if activity.type == discord.ActivityType.playing:
                if isinstance(activity, discord.Game):
                    activityType = 'Playing **{}**'.format(activity.name)
                else:
                    if activity.start:
                        activityType = 'Playing **{}** for **{}**'.format(activity.name, time.human_timedelta(activity.start, accuracy=1, suffix=False))
                    else:
                        activityType = 'Playing **{}**'.format(activity.name)
                        
            elif activity.type == discord.ActivityType.streaming:
                activityType = 'Streaming **[{}]({})**'.format(activity.name, activity.url)
            
            elif activity.type == discord.ActivityType.listening:
                if isinstance(activity, discord.Spotify):
                    activityType = 'Listening To **[{}](https://open.spotify.com/track/{})**'.format(activity.title ,activity.track_id)
                else:
                    activityType = 'Listening To **{}**'.format(activity.name)

            elif activity.type == discord.ActivityType.watching:
                activityType = 'Watching **{}**'.format(activity.name)
            
            elif activity.type == discord.ActivityType.custom:
                activityType = 'Custom Activity **{}**'.format(activity.name)
            
            elif activity.type == discord.ActivityType.competing:
                activityType = 'Competing in **{}**'.format(activity.name)
            else:
                activityType = 'Unknown activity'

        else:
            activityType = consts.CUSTOM_TICKS[False]

        try:
            is_blacklisted = self.client.blacklist[member.id]
        except KeyError:
            is_blacklisted = False

        try:
            is_afk = self.client.afk_users[member.id]
        except KeyError:
            is_afk = False

        bamboo = self.client.bal(member.id)

        embed = discord.Embed(title='Showing info for {}'.format(fetched_user.name), color=member.color)   
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="ℹ️ General Information",
                        value=f"\n╰ **ID:** `{member.id}`"
                              f"\n╰ **Username:** `{fetched_user.name}`"
                              f"\n╰ **Discriminator:** `#{fetched_user.discriminator}`"
                              f"\n╰ **Nickname:** {(member.nick or consts.CUSTOM_TICKS[False])}"
                              f"\n╰ **Mention:** {member.mention}")

        embed.add_field(name="<:members:658538493470965787> User Info",
                        value=f"\n╰ **Created:** {discord.utils.format_dt(member.created_at, style='f')} {discord.utils.format_dt(member.created_at, style='R')}"
                              f"\n╰ **Badges:** {flags}"
                              f"\n╰ **Status:** {status}"
                              f"\n╰ **Activity:** {activityType}"
                              f"\n╰ **Status:** {status_str}"
                              f"\n╰ **Voice Channel:** {member.voice.channel.mention if member.voice else consts.CUSTOM_TICKS[False]}"
                        ,inline=False)

        embed.add_field(name="<:slash:782701715479724063> Other",
                        value=f"\n╰ **Backlisted:** {consts.CUSTOM_TICKS[is_blacklisted]}"
                              f"\n╰ **Afk:** {consts.CUSTOM_TICKS[is_afk]}"
                              "\n╰ **Bamboo:** {:,} <:bamboo:911241395434565652>".format(bamboo)
                        ,inline=False)

        if member.premium_since:
            embed.add_field(name="<:booster:895429394376572928> Boosting since:",
                            value=f"╰ **Date:** {discord.utils.format_dt(member.premium_since, style='f')} ({discord.utils.format_dt(member.premium_since, style='R')})"
                            ,inline=False)

        if member.avatar:
            embed.add_field(name="<:rich_presence:658538493521166336> Avatar",
                            value=(
                                f"\n╰ {avatar}"
                            ),inline=False)

        if fetched_user.banner:
            embed.add_field(name="<:rich_presence:658538493521166336> Banner",
                            value=(
                                f"\n╰ {banner}"
                            ),inline=True) 

        embed.add_field(name="<:joined:903350386646212678> Join Info",
                value=(
                    f"\n╰ **Joined:** {discord.utils.format_dt(member.joined_at, style='f')} {discord.utils.format_dt(member.joined_at, style='R')}"
                    f"\n╰ **Join Position:**"
                    f"\n```python"
                    f"\n{join_pos}"
                    f"\n```"
                ),inline=False)    

        roles = [r.mention for r in member.roles if r != ctx.guild.default_role]
        if roles:
            if len(roles) < 10 and len(roles) > 1:
                embed.add_field(name="<:role:808826577785716756> Top Role",
                                value=member.top_role.mention, inline=False)
                
                embed.add_field(name="<:role:808826577785716756> Roles",
                                value=" ".join(roles[::-1]), inline=False)
            else:
                embed.add_field(name="<:role:808826577785716756> Top Role",
                                value=member.top_role.mention, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(aliases=["si"])
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context, guild_id: int = None):
        """
        Shows the current server's information.
        """
        if guild_id and await self.client.is_owner(ctx.author):
            guild = self.client.get_guild(guild_id)
            if not guild:
                return await ctx.send(embed=discord.Embed(title='Something went wrong...', description="I couldn't find that server. Make sure the ID you entered was correct.", color=discord.Color.red()))
        else:
            guild = ctx.guild

        try:
            bannedMembers = len(await guild.bans())
        except:
            bannedMembers = "Couldn't get banned members."   
        
        if guild.premium_tier == 0:
            levelEmoji = "<:Level0_guild:895938129498869790>"
        if guild.premium_tier == 1:
            levelEmoji = "<:Level1_guild:895938143465906176>"
        if guild.premium_tier == 2:
            levelEmoji = "<:Level2_guild:895938192904171541>"
        if guild.premium_tier == 3:
            levelEmoji = "<:Level3_guild:895938217088540692>"

        verification_level1 = str(guild.verification_level)
        verification_level = verification_level1.capitalize()

        if verification_level == "Low":
            verificationEmote = "<:low_verification:890313091957551114>"
        elif verification_level == "Medium":
            verificationEmote = "<:medium_verifiaction:890312470894358549>"
        elif verification_level == "High":
            verificationEmote = "<:high_verifiaction:890313146357653544>"
        elif verification_level == "Highest":
            verificationEmote = "<:highest_verifiaction:890313190452367380>"
        else:
            verificationEmote = "<:none_verifiaction:890312616172474378>"

        if str(guild.explicit_content_filter) == "no_role":
            explictContentFilter = "Scan media content from members without a role."
        elif str(guild.explicit_content_filter) == "all_members":
            explictContentFilter = "Scan media from all members."
        else:
            explictContentFilter = "Don't scan any media content."

        statuses = [len(list(filter(lambda m: str(m.status) == "online", guild.members))),
                    len(list(filter(lambda m: str(m.status) == "idle", guild.members))),
                    len(list(filter(lambda m: str(m.status) == "dnd", guild.members))),
                    len(list(filter(lambda m: str(m.status) == "offline", guild.members)))]

        last_boost = max(guild.members, key=lambda m: m.premium_since or guild.created_at)
        if last_boost.premium_since is not None:
            boost = (f"`{last_boost}`"
                    f"\n╰ **Date:** {discord.utils.format_dt(last_boost.premium_since, style='f')} {discord.utils.format_dt(last_boost.premium_since, style='R')}")
        else:
            boost = "No active boosters"

        embed = discord.Embed(title=guild.name)
        embed.add_field(name="ℹ️ General information:",
                        value=f"\n╰ **ID:** `{guild.id}`"
                              f"\n╰ **Owner:** `{guild.owner}`"
                              f"\n╰ **Explicit content filter:** {explictContentFilter}"
                              f"\n╰ **Filesize limit:** {helper.convert_bytes(guild.filesize_limit)}"
                              f"\n╰ **Created:** {discord.utils.format_dt(guild.created_at, style='f')} ({discord.utils.format_dt(guild.created_at, style='R')})"
                              f"\n╰ **Verification level:** {verificationEmote} ({verification_level})"
                              f"\n╰ **Region:** {helper.get_server_region_emote(guild)} ({str(helper.get_server_region(guild))})",
                              inline=True)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            if guild.icon.is_animated():
                icon =  f"[PNG]({guild.icon.replace(format='png', size=1024).url}) | "\
                        f"[JPG]({guild.icon.replace(format='jpg', size=1024).url}) | "\
                        f"[JPEG]({guild.icon.replace(format='jpeg', size=1024).url}) | "\
                        f"[WEBP]({guild.icon.replace(format='webp', size=1024).url}) | "\
                        f"[GIF]({guild.icon.replace(format='gif', size=1024).url})"
            
            else:
                icon =  f"[PNG]({guild.icon.replace(format='png', size=1024).url}) | "\
                        f"[JPG]({guild.icon.replace(format='jpg', size=1024).url}) | "\
                        f"[JPEG]({guild.icon.replace(format='jpeg', size=1024).url}) | "\
                        f"[WEBP]({guild.icon.replace(format='webp', size=1024).url})"
            
            embed.add_field(name="<:rich_presence:658538493521166336> Server Icon",
                            value=(f"\n╰ {icon}"),inline=False)
        
        if guild.banner:
            if guild.banner.is_animated():
                banner= f"[PNG]({guild.banner.replace(format='png', size=1024).url}) | "\
                        f"[JPG]({guild.banner.replace(format='jpg', size=1024).url}) | "\
                        f"[JPEG]({guild.banner.replace(format='jpeg', size=1024).url}) | "\
                        f"[WEBP]({guild.banner.replace(format='webp', size=1024).url}) | "\
                        f"[GIF]({guild.banner.replace(format='gif', size=1024).url})"
            
            else:
                banner= f"[PNG]({guild.banner.replace(format='png', size=1024).url}) | "\
                        f"[JPG]({guild.banner.replace(format='jpg', size=1024).url}) | "\
                        f"[JPEG]({guild.banner.replace(format='jpeg', size=1024).url}) | "\
                        f"[WEBP]({guild.banner.replace(format='webp', size=1024).url})"
           
            embed.add_field(name="<:rich_presence:658538493521166336> Server Banner",
                            value=(f"\n╰ {banner}"),inline=False)        

        embed.add_field(name=f"<:members:658538493470965787> Members ({guild.member_count})",
                        value=f"\n╰ **People:** {len([m for m in guild.members if not m.bot])}"
                              f"\n╰ **Bots:** {len([m for m in guild.members if m.bot])}"
                              f"\n╰ **Statuses:** {consts.statuses.ONLINE} {statuses[0]} | {consts.statuses.IDLE} {statuses[1]} | {consts.statuses.DND} {statuses[2]} | {consts.statuses.OFFLINE} {statuses[3]}"
                              f"\n╰ **Banned Members:** {bannedMembers}"
                              ,inline=False)

        embed.add_field(name=f"<:channel:585783907841212418> Channels ({len(guild.channels)})",
                        value=f"\n╰ **Categories:** {len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])}"
                              f"\n╰ **Voice Channels:** {len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])}"
                              f"\n╰ **Text Channels:** {len([c for c in guild.channels if isinstance(c, discord.TextChannel)])}"
                              f"\n╰ **Stages:** {len([c for c in guild.channels if isinstance(c, discord.StageChannel)])}"
                              ,inline=False)

        embed.add_field(name="<:emoji_ghost:658538492321595393> Emojis:",
                        value=f"\n╰ **Static:** {len([e for e in guild.emojis if not e.animated])}/{guild.emoji_limit}"
                              f"\n╰ **Animated:** {len([e for e in guild.emojis if e.animated])}/{guild.emoji_limit}",
                              inline=False)
                              
        embed.add_field(name="<:booster:895429394376572928> Server Boosts",
                        value=f"\n╰ **Level:** {levelEmoji} ({guild.premium_tier})"
                              f"\n╰ **Boosts:** {guild.premium_subscription_count}"
                              f"\n╰ **Latest booster:** {boost}"
        )

        await ctx.send(embed=embed)

    @commands.command(help="Shows you a list of emotes from this server")
    async def emojilist(self, ctx):
        guild = ctx.guild

        guildEmotes = guild.emojis
        emotes = []

        for emoji in guildEmotes:

          if emoji.animated:
             emotes.append(f"<a:{emoji.name}:{emoji.id}> **|** {emoji.name} **|** [`<a:{emoji.name}:{emoji.id}>`]({emoji.url})")

          if not emoji.animated:
              emotes.append(f"<:{emoji.name}:{emoji.id}> **|** {emoji.name} **|** [`<:{emoji.name}:{emoji.id}>`]({emoji.url})")

        menu = paginator.ViewPaginator(paginator.ServerEmotesEmbedPage(data=emotes, guild=guild), ctx=ctx)
        await menu.start()

    @commands.command(aliases=['perms'])
    @commands.guild_only()
    async def permissions(self, ctx: commands.Context, member: discord.Member = None):
        """Shows a member's permissions."""
        if member is None:
            member = ctx.author
        
        await ctx.send(embed=await self.generate_perms(member))

    @commands.command()
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    async def emoji_clone(self, ctx: commands.Context, server_emoji: typing.Optional[typing.Union[discord.Embed, discord.PartialEmoji]], index: int = 1):
        """
        Clones an emoji into the current server
        """
        if ctx.message.reference:
            custom_emoji = re.compile(r"<a?:[a-zA-Z0-9_]+:[0-9]+>")
            emojis = custom_emoji.findall(ctx.message.reference.resolved.content)
            if not emojis:
                raise errors.NoEmojisFound
            try:
                server_emoji = await commands.PartialEmojiConverter().convert(ctx, emojis[index - 1])
            except IndexError:
                return await ctx.send(f"Emoji out of index {index}/{len(emojis)}!" f"\nIndex must be lower or equal to {len(emojis)}")

        if not server_emoji:
            raise commands.MissingRequiredArgument(
                Parameter(name='server_emoji', kind=Parameter.POSITIONAL_ONLY))

        file = await server_emoji.read()
        guild = ctx.guild
        server_emoji = await guild.create_custom_emoji(name=server_emoji.name, image=file, reason=f"Cloned emoji, requested by {ctx.author}")
        embed = discord.Embed(color = discord.Color.blurple())
        embed.description = f"Done! cloned {server_emoji}"
        await ctx.send(embed=embed)
    
    @commands.command()
    async def afk(self, ctx: commands.Context, *, reason: commands.clean_content = 'No reason specified'):
        if ctx.author.id in self.client.afk_users and ctx.author.id in self.client.auto_un_afk and self.client.auto_un_afk[ctx.author.id] is True:
            return
        if ctx.author.id not in self.client.afk_users:
            await self.client.db.execute('INSERT INTO afk (user_id, start_time, reason) VALUES ($1, $2, $3) '
                                      'ON CONFLICT (user_id) DO UPDATE SET start_time = $2, reason = $3',
                                      ctx.author.id, ctx.message.created_at, reason[0:1800])
            self.client.afk_users[ctx.author.id] = True
            
            embed = discord.Embed(title = f'Status Changed <:away2:464520569862357002>',description=f'{ctx.author.mention} is going AFK with reason: {reason}',color=discord.Color.orange())
            await ctx.send(embed=embed)
        else:
            self.client.afk_users.pop(ctx.author.id)
            await self.client.db.execute('INSERT INTO afk (user_id, start_time, reason) VALUES ($1, null, null) '
                                      'ON CONFLICT (user_id) DO UPDATE SET start_time = null, reason = null', ctx.author.id)
            
            embed = discord.Embed(title=f'Status Changed <:online2:464520569975603200>',description=f'{ctx.author.mention} is no longer AFK',color=discord.Color.green())
            await ctx.send(embed=embed)

    @commands.command()
    async def translate(self, ctx:commands.Context, language:str, *,input:str):   
        try:
            translator = GoogleTranslator(source='auto', target=language.lower())
            translated = translator.translate(input)
        except UnsupportedLanguage:
            return await ctx.send(embed=discord.Embed(title='Error Occured', description='Please input valid language to translate to'))
            

        #if translator.source == translator.target:
            #return await ctx.send(embed=discord.Embed(title='Error Occured', description='Can\'t translate from `{}` to `{}`'.format(translated.source.upper(), translated.target.upper())))
            
        
        embed=discord.Embed()
        embed.add_field(name=f'Text in `{language.capitalize() if len(language) != 2 else language.upper()}`:', value=
                    f"\n```fix"
                    f"\n{translated}"
                    f"\n```", inline=False)
        embed.set_footer(text='Please remember, that the translations can\'t be a 100% accurate')

        await ctx.send(embed=embed)

    @commands.command(aliases=['sourcecode', 'code'], usage="[command|command.subcommand]")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def source(self, ctx, *, command: str = None):
        """
        Links to the bot's code, or a specific command's
        """
        global obj
        source_url = 'https://github.com/MiroslavRosenov/DaPanda'
        branch = 'master'
        license_url = f'{source_url}/blob/{branch}/LICENCE'
        mpl_advice = f'**This code is licensed under [MPL]({license_url})**' \
                     f'\nRemember that you must use the ' \
                     f'\nsame license! [[read more]]({license_url}#L160-L168)'
        obj = None

        if command is None:
            embed = discord.Embed(title=f'Here\'s my source code.',
                                  description=mpl_advice)
            embed.set_image(
                url='https://image.prntscr.com/image/BMmJV90XTwmmeD91diWlaQ.png')
            return await ctx.send(embed=embed, view=helper.Url(source_url, label='Open on GitHub', emoji='<:github:744345792172654643>'))

        if command == 'help':
            src = type(self.client.help_command)
            module = src.__module__
            filename = inspect.getsourcefile(src)
            obj = 'help'
        else:
            obj = self.client.get_command(command.replace('.', ' '))
            if obj is None:
                embed = discord.Embed(title=f'Couldn\'t find command.',
                                      description=mpl_advice)
                embed.set_image(
                    url='https://image.prntscr.com/image/BMmJV90XTwmmeD91diWlaQ.png')
                return await ctx.send(embed=embed,
                                      view=helper.Url(source_url, label='Open on GitHub', emoji='<:github:744345792172654643>'),
                                      footer=False)                      
            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith('discord'):
            # not a built-in command
            location = os.path.relpath(filename).replace('\\', '/')
        else:
            location = module.replace('.', '/') + '.py'
            source_url = 'https://github.com/Rapptz/discord.py'
            branch = 'master'

        final_url = f'{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}'
        
        embed = discord.Embed(title=f'Here\'s `{str(obj)}`')
        embed.description = mpl_advice
        embed.set_image(url='https://image.prntscr.com/image/BMmJV90XTwmmeD91diWlaQ.png')
        embed.set_footer(text=f"{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}")

        if obj.cog.qualified_name == 'Music':
            embed.add_field(name='Attention ⚠️', value = (
                "Please understand Music bots are complex,"
                "and this code can be daunting to a beginner."
            ))

        await ctx.send(embed=embed, view=helper.Url(final_url, label=f'Here\'s {str(obj)}', emoji='<:github:744345792172654643>'))

def setup(client):
    client.add_cog(Utility(client))
