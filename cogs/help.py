import aiohttp
import discord
import sys
import psutil
import time

from discord.ext import commands
from helpers import paginator
from helpers import helper
from .utils import time as time_

def setup(bot):
    bot.add_cog(About(bot))

with open('/root/bot/helpers/news.txt') as f:
        newsFileContext = f.read()
        news = str(newsFileContext)

class Invites(discord.ui.View):
    def __init__(self ,ctx: commands.Context):
        super().__init__()
        self.add_item(discord.ui.Button(emoji="<:website:908421962538307645>", label='Website', url=ctx.bot.website_url))
        self.add_item(discord.ui.Button(emoji='<:github:744345792172654643>', label='Source', url=ctx.bot.source_url))
        self.add_item(discord.ui.Button(emoji="<:invite:658538493949116428>", label='Invite Me', url=ctx.bot.invite_url))
        self.add_item(discord.ui.Button(emoji="<:top_gg:895376601112514581>", label='Vote', url=ctx.bot.top_gg))
    
class MyHelp(commands.HelpCommand):
    def get_minimal_command_signature(self, command):
        if isinstance(command, commands.Group):
            return '[G] %s%s %s' % (self.context.clean_prefix, command.qualified_name, command.signature)
        return '(c) %s%s %s' % (self.context.clean_prefix, command.qualified_name, command.signature)

    @staticmethod
    def get_command_name(command):
        return '%s' % command.qualified_name

    def common_command_formatting(self, embed_like, command):
        embed_like.title = self.get_command_signature(command)
        if command.description:
            embed_like.description = f'{command.description}\n\n```yml\n{command.help}\n```'
        else:
            embed_like.description = command.help or '```yml\nNo help found...\n```'

    # !help
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Help Menu')
        embed.description = (
            f"\n🕐 Uptime: `{time_.human_timedelta(self.context.bot.start_time, suffix=False)}`"
            f"\n<:slash:782701715479724063> Total Commands: {len(list(self.context.bot.commands))}")

        cogs = []
        for cog, commands in mapping.items():
            if cog is None or cog.qualified_name in self.context.bot.ignored_cogs:
                continue
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [self.get_command_name(c) for c in filtered]
            if command_signatures:
                emoji = cog.description[0:1]
                cogs.append(f"\n{emoji} `{self.context.clean_prefix}help {cog.qualified_name.lower()}`"
                            f"\n{cog.description.replace(emoji, '> ')}\n")

        embed.add_field(name=f'<:categories:895425612804661299> **Available categories ({len(cogs)})** ',
                        value=(f"{''.join(cogs)}"), inline=True)
        
        #embed.set_image(url='https://dapanda.xyz/assets/banner.png')
        await self.context.send(embed=embed, view=Invites(self.context))
        

    # !help <command>
    async def send_command_help(self, command):
        ctx = self.context
        if command.cog.qualified_name in ctx.bot.ignored_cogs and ctx.author.id != ctx.bot.owner_id:
            return await ctx.send(embed=discord.Embed(title='Forbidden', description='You don\'t have permissions to view this asset', color=discord.Color.red()))
        
        alias = command.aliases
        if command.help:
            command_help = command.help.replace("%PRE%", self.context.clean_prefix)
        else:
            command_help = 'No help given...'
        if alias:
            embed = discord.Embed(title=f"Information about: {self.context.clean_prefix}{command}", 
                                  description=(
                                            f"\n```yml"
                                            f"\n      usage: {self.get_minimal_command_signature(command)}"
                                            f"\n    aliases: {', '.join(alias)}"
                                            f"\ndescription: {command_help}"
                                            f"\n```"
                                            ))
        else:
            embed = discord.Embed(title=f"Information about {self.context.clean_prefix}{command}", 
                                  description=(
                                            f"\n```yml"
                                            f"\n      usage: {self.get_minimal_command_signature(command)}"
                                            f"\ndescription: {command_help}"
                                            f"\n```"
                                            ))
     
        await self.context.send(embed=embed)

    # !help <cog>
    async def send_cog_help(self, cog):
        ctx = self.context
        if cog.qualified_name in ctx.bot.ignored_cogs and ctx.author.id != ctx.bot.owner_id:
            return await ctx.send(embed=discord.Embed(title='Forbidden', description='You don\'t have permissions to view this asset', color=discord.Color.red()))
        
        entries = cog.get_commands()
        menu = paginator.ViewPaginator(paginator.GroupHelpPageSource(cog, entries, prefix=ctx.clean_prefix, color=ctx.color),
                                       ctx=ctx, compact=True)
        await menu.start()

    # !help <group>
    async def send_group_help(self, group):
        ctx = self.context
        if group.cog.qualified_name in ctx.bot.ignored_cogs and ctx.author.id != ctx.bot.owner_id:
            return await ctx.send(embed=discord.Embed(title='Forbidden', description='You don\'t have permissions to view this asset', color=discord.Color.red()))
        
        entries = [command for command in group.commands]
        menu = paginator.ViewPaginator(paginator.GroupHelpPageSource(group, entries, prefix=ctx.clean_prefix, color=ctx.color),
                                       ctx=ctx, compact=True)
        await menu.start()

    async def send_error_message(self, error):
        await self.context.send(embed=discord.Embed(title='Error occured', description=error))

class About(commands.Cog):
    """
    🐼 Commands related to the bot itself, that have the only purpose to show information.
    """
    def __init__(self, bot):
        self.bot = bot
        help_command = MyHelp()
        help_command.cog = self
        bot.help_command = help_command
        bot.session = aiohttp.ClientSession()

    @commands.command(help="Shows info about the bot")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def about(self, ctx):
        """Tells you information about the bot itself."""
        permissions = [permission for permission in ctx.me.guild_permissions]
        allowed = []
        for name, value in permissions:
            name = name.replace("_", " ").replace("guild", "server").title()

            if value and name:
                allowed.append(f"`{name}`")

        if 'Administrator' in allowed:
            allowed = ["Administrator"]  

        if len(allowed) == 0:
            allowed = ['None']         

        information = await self.bot.application_info()
        text_channels = len([channel for channel in self.bot.get_all_channels() if isinstance(channel, discord.TextChannel)])
        voice_channels = len([channel for channel in self.bot.get_all_channels() if isinstance(channel, discord.VoiceChannel)])
        categories = len([channel for channel in self.bot.get_all_channels() if isinstance(channel, discord.CategoryChannel)])
        stage_channels = len([channel for channel in self.bot.get_all_channels() if isinstance(channel, discord.StageChannel)])
        channels = len([channel for channel in self.bot.get_all_channels()])

        ver = sys.version_info
        full_version = f"{ver.major}.{ver.minor}.{ver.micro}"
        
        memory_usage = psutil.Process().memory_percent()
        cpu_usage = psutil.cpu_percent()

        prefixes = await ctx.bot.get_pre(ctx.bot, ctx.message, raw_prefix=True)
        prefix = f'{self.bot.user.mention}'
        for x in prefixes:
            prefix += f', `{x}`'
        
        embed = discord.Embed(title=f'Information about me (DaPanda)', url=self.bot.invite_url)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        embed.add_field(name=f'<:partnernew:754032603081998336> Servers ({len(self.bot.guilds)})', value=
        f"\n╰ <:members:658538493470965787> Members: {len(self.bot.users):,}"
        f"\n╰ <:bot:891076085314388058> Bots: {len(list(filter(lambda m : m.bot, self.bot.users))):,}", inline=True)

        embed.add_field(name=f'<:rich_presence:658538493521166336> Channels ({channels})', value=
        f"\n╰ <:categories:895425612804661299> Categories : {categories}"
        f"\n╰ <:voice:585783907673440266> Voice: {voice_channels}"
        f"\n╰ <:channel:585783907841212418> Text: {text_channels}"
        f"\n╰ <:stagechannel:824240882793447444> Stages: {stage_channels}", inline=False)
        
        embed.add_field(name='🖥️ Processes', value=
        f"\n╰ `{memory_usage:.2f}% RAM` ussage"
        f"\n╰ `{cpu_usage:.2f}% CPU` ussage", inline=True)

        embed.add_field(name='⚙️ Versions', value=
        f"\n╰ <:dpy:596577034537402378> Discord: `{discord.__version__}`"
        f"\n╰ <:python:596577462335307777> Python: `{full_version}`", inline=True)

        embed.add_field(name=f'🔓 Server Permissions ({len(allowed)})', value=
        f"\n╰ {', '.join(allowed)}"
        , inline=False)
        
        embed.set_footer(text=f'Made by {information.owner}', icon_url=information.owner.display_avatar.url)
        
        await ctx.send(embed=embed, view=Invites(ctx))

    @commands.command()
    async def suggest(self, ctx: commands.Context, *, suggestion):
        channel = self.bot.get_channel(884991926347128882)
        embed = discord.Embed(colour=ctx.me.color,
                              title="Suggestion successful!")
        embed.add_field(name="Thank you!", value="Your suggestion has been sent to the moderators of DaPanda!")
        embed.add_field(name="Your suggestion:", value=f"```\n{suggestion}\n```")
        embed2 = discord.Embed(colour=ctx.me.color,
                               title=f"Suggestion from {ctx.author}",
                               description=f"```\n{suggestion}\n```")
        embed2.set_footer(text=f"Sender ID: {ctx.author.id}")

        if ctx.message.attachments:
            file = ctx.message.attachments[0]
            spoiler = file.is_spoiler()
            if not spoiler and file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                embed.set_image(url=file.url)
                embed2.set_image(url=file.url)
            elif spoiler:
                embed.add_field(name='Attachment', value=f'||[{file.filename}]({file.url})||', inline=False)
                embed2.add_field(name='Attachment', value=f'||[{file.filename}]({file.url})||', inline=False)
            else:
                embed.add_field(name='Attachment', value=f'[{file.filename}]({file.url})', inline=False)
                embed2.add_field(name='Attachment', value=f'[{file.filename}]({file.url})', inline=False)

        await channel.send(embed=embed2)
        await ctx.send(embed=embed)

    @commands.command(aliases=['add'],description="Send an invite link")
    async def invite(self, ctx: commands.Context):
        embed = discord.Embed(title='Invite me to you server !',description='Current Permissions: `Administator` and `Slash Commands`')
        await ctx.send(embed=embed, view=helper.Url(self.bot.invite_url, label='Invite me', emoji='<:invite:658538493949116428>'))

    @commands.command(aliases=['web'],description="Send an invite link")
    async def website(self, ctx: commands.Context):
        await ctx.send(self.bot.website_url)

    @commands.command(aliases=['online','up'],description="Shows you the uptime of the bot")
    async def uptime(self, ctx: commands.Context):
        embed = discord.Embed(title='Uptime status',description=f'I\'ve been online for `{time_.human_timedelta(self.bot.start_time, suffix=False)}` or since {discord.utils.format_dt(self.bot.start_time)}')
        await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def ping(self, ctx):
        """Checks the bot's ping to Discord"""
        pings = []

        typings = time.monotonic()
        await ctx.trigger_typing()

        typinge = time.monotonic()
        typingms = (typinge - typings) * 1000
        pings.append(typingms)

        start = time.perf_counter()

        discords = time.monotonic()
        url = "https://discordapp.com/"

        async with self.bot.session.get(url) as resp:
            if resp.status == 200:
                discorde = time.monotonic()
                discordms = (discorde - discords) * 1000
                pings.append(discordms)
            else:
                discordms = 0

        latencyms = self.bot.latency * 1000
        pings.append(latencyms)

        pend = time.perf_counter()
        psqlms = (pend - start) * 1000
        pings.append(psqlms)

        end = time.perf_counter()
        messagems = (end - start) * 1000
        pings.append(messagems)

        ping = 0
        for x in pings:
            ping += x

        average = ping / len(pings)

        msg = (
            f"\n🌐 | Socket: `{round(latencyms, 3)} ms`"
            f"\n<a:typingstatus:393836741272010752> | Typing: `{round(typingms, 3)} ms`"
            f"\n💬 | Message: `{round(messagems, 3)} ms`"
            f"\n<:psql:895425590973321247> | Database `{round(psqlms, 3)} ms`"
            f"\n<:discord:314003252830011395> | Discord `{round(discordms, 3)} ms`"
            f"\n♾️ | Average `{round(average, 3)} ms`"
        )
        
        await ctx.send(embed=discord.Embed(title='Pong 🏓', description=msg))

    @commands.command(help="Shows information about the bot's status.", aliases=['shards', 'shard'])
    async def status(self, ctx):
        await ctx.send('https://www.dapanda.xyz/status')

    @commands.command()
    async def news(self, ctx):
        """
        Shows the latest changes of the bot.
        """
        embed = discord.Embed().add_field(name='<:news:658522693058166804> **Latest News - <t:1635375068:d> (<t:1635375068:R>)**:', value=news)
        
        await ctx.send(embed=embed) 

    @commands.command()
    async def credits(self, ctx):
        """
        Shows the latest changes of the bot.
        """
        embed = discord.Embed(color=ctx.me.color)
        embed.add_field(name="💳 Credits - Everyone that helped in the development process)",
        value=f"\u200b"
        f"\n> <:rooFat:744345098531242125> **DaPandaOfficial🐼#5684**"
        f"\n> `Creator of the bot`"
        f"\n"
        f"\n> <a:rooLove:744346239075877518> **LeoCx1000#9999 **"
        f"\n> `Helped with a lot of commands and bug fixes`"
        f"\n"
        f"\n> <a:rooLove:744346239075877518> **Ender2K89#9999 **"
        f"\n> `Helped with a lot of commands`"
        f"\n"
        f"\n> <a:rooLove:744346239075877518> **『P』『a』『r』『i』#9137**"
        f"\n> `Helped with the music module`")
        await ctx.send(embed=embed)