import datetime
import time as t
import logging
import os
import traceback
import discord
import asyncpg
import asyncpraw
import pomice
import topgg

from discord.ext import commands
from helpers.context import CustomContext
from cogs.utils import time as time_
import helpers.errors as errors

from discord.ext.commands.errors import (ExtensionAlreadyLoaded, ExtensionFailed, ExtensionNotFound, NoEntryPointError)
from discord.ext.commands.errors import ExtensionNotFound
from typing import (List, Optional)

initial_extensions = ('jishaku',)
async def create_db_pool() -> asyncpg.Pool:
    credentials = {
        "user": f"{os.getenv('PSQL_USER')}",
        "password": f"{os.getenv('PSQL_PASSWORD')}",
        "database": f"{os.getenv('PSQL_DB')}",
        "host": f"{os.getenv('PSQL_HOST')}"
    }

    return await asyncpg.create_pool(**credentials)

class Main(commands.AutoShardedBot):
    PRE: tuple = ('panda.','dapanda.',)
    def user_blacklisted(self, ctx):
        try:
            is_blacklisted = self.blacklist[ctx.author.id]
        except KeyError:
            is_blacklisted = False
        if ctx.author.id == self.owner_id:
            is_blacklisted = False

        if is_blacklisted is False:
            return True
        else:
            raise errors.UserBlacklisted

    def maintenance_mode(self, ctx):
        if not self.maintenance or ctx.author.id == self.owner_id:
            return True
        else:
            raise errors.BotUnderMaintenance
    
    def dj_only(self, guild):
        try:
            dj_only = self.dj_modes[guild.id]
        except KeyError:
            dj_only = True

        if dj_only: 
            return True
        else:
            return False

    def dj_role(self, guild):
        try:
            dj_role_id = self.dj_roles[guild.id]
        except KeyError:
            dj_role_id = False

        if dj_role_id:
            role = guild.get_role(dj_role_id)
            return role
        else:
            return False
    
    def bal(self, id):
        try:
            bal = self.bamboos[id]
        except KeyError:
            bal = 0

        return bal

    def claimed(self, id):
        try:
            claimed = self.claims[id]
        except KeyError:
            claimed = False

        return claimed

    def __init__(self) -> None:
        intents = discord.Intents.all()

        super().__init__(
            command_prefix=self.get_pre,
            slash_commands=True,
            intents=intents,
            case_insensitive=True,
            activity=discord.Activity(type=discord.ActivityType.listening, name='dapanda.xyz'),  
            status=discord.Status.online,
            shard_count=3
        )
        self.reddit = asyncpraw.Reddit(client_id=os.getenv('ASYNC_PRAW_CID'),
                                       client_secret=os.getenv('ASYNC_PRAW_CS'),
                                       user_agent=os.getenv('ASYNC_PRAW_UA'),
                                       username=os.getenv('ASYNC_PRAW_UN'),
                                       password=os.getenv('ASYNC_PRAW_PA'))
        
        self.add_check(self.user_blacklisted)
        self.add_check(self.maintenance_mode)

        self.db: asyncpg.Pool = self.loop.run_until_complete(create_db_pool())
        self._BotBase__cogs = commands.core._CaseInsensitiveDict() 
        self.start_time = datetime.datetime.utcnow()
        self.pomice = pomice.NodePool()
        self._topgg = topgg.DBLClient(self, os.getenv('TOPGG_TOKEN'), autopost=True, post_shard_count=True)
        self._topgg_webhook = topgg.WebhookManager(self).dbl_webhook('/topgg', os.getenv('TOPGG_PASSWORD'))
        
        self.fixed_color = True
        self.noprefix = False
        self.started = False
        self.maintenance = False

        self.owner_id = 383946213629624322
        self.user_id = 786550035952173107

        self.website_url ='https://www.dapanda.xyz'
        self.source_url = 'https://github.com/MiroslavRosenov/DaPanda'
        self.invite_url = 'https://discord.com/api/oauth2/authorize?client_id=786550035952173107&permissions=8&scope=bot%20applications.commands'
        self.support_server = 'https://discord.gg/Rpg7zjFYsh'
        self.top_gg = 'https://top.gg/bot/786550035952173107'
        self.vote_url = 'https://top.gg/bot/786550035952173107/vote'
        
        self.prefixes = {}
        self.blacklist = {}
        self.afk_users = {}
        self.auto_un_afk = {}
        self.dj_modes = {}
        self.dj_roles = {}
        self.bamboos = {}
        self.claims = {}
        self.dailys = {}
        self.weeklys = {}

        self.ignored_cogs = ['dev', 'Jishaku', 'error_handler', 'event_handler', 'mail']
        
        for ext in initial_extensions:
            logging.info(f"Trying to load cog: {ext}")
            try:
                self._load_extension(ext)
            except (ExtensionNotFound, ExtensionAlreadyLoaded, NoEntryPointError, ExtensionFailed):
                logging.critical("================[ ERROR ]================")
                logging.critical(f"An error occurred while loading: {ext}")
                logging.critical(' ')
            
            else:
                os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"
                self.get_command("jsk").hidden = True
                logging.info(f'Successfully loaded: {ext}')
                logging.info(' ')
        self._dynamic_cogs()
    
    def _load_extension(self, name: str) -> None:
        try:
            self.load_extension(name)
        except (ExtensionNotFound, ExtensionAlreadyLoaded, NoEntryPointError, ExtensionFailed):
            traceback.print_exc()

    def _dynamic_cogs(self) -> None:
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                cog = filename[:-3]
                try:
                    logging.info(f"Trying to load cog: {cog}")
                    self._load_extension(f'cogs.{cog}') 
                except:
                    logging.critical("================[ ERROR ]================")
                    logging.critical(f"An error occurred while loading: {cog}")
                    logging.critical(' ')
                
                else:
                    logging.info(f'Successfully loaded: {cog}')
                    logging.info(' ')
    
    async def on_ready(self) -> None:
        logging.info(' ')
        logging.info("=======[ BOT IS READY! ]=======")
        logging.info("=======[ USER: {} ]=======".format(self.user.name))
        if not self.started:
            os.system("sudo systemctl restart web")
            await self._topgg_webhook.run(5000)
            
            self.started = True
            try:
                logging.info(' ')
                logging.info('Trying to load node with identifier: {}'.format(os.getenv('LAVALINK_IDENTIFIER')))
                await self.pomice.create_node(
                    bot=self,
                    host=f"{os.getenv('LAVALINK_HOST')}",
                    port=os.getenv('LAVALINK_PORT'),
                    password=f"{os.getenv('LAVALINK_PASSWORD')}",
                    identifier=f"{os.getenv('LAVALINK_IDENTIFIER')}",
                    spotify_client_id=f"{os.getenv('SPOTIFY_ID')}",
                    spotify_client_secret=f"{os.getenv('SPOTIFY_SECRET')}"
                )
            except:
                logging.error('Failed while trying to load node with identifier: {}'.format(os.getenv('LAVALINK_IDENTIFIER')))
            else:
                logging.info('Successfully loadeded node with identifier: {}'.format(os.getenv('LAVALINK_IDENTIFIER')))

            values = await self.db.fetch("SELECT guild_id, prefix FROM guilds")
            for value in values:
                if value['prefix']:
                    self.prefixes[value['guild_id']] = (
                            (value['prefix'] if value['prefix'][0] else self.PRE) or self.PRE)

            for guild in self.guilds:
                if not guild.unavailable:
                    try:
                        self.prefixes[guild.id]
                    except KeyError:
                        self.prefixes[guild.id] = self.PRE

            values = await self.db.fetch("SELECT user_id, is_blacklisted FROM blacklist")
            for value in values:
                self.blacklist[value['user_id']] = (value['is_blacklisted'] or False)

            values = await self.db.fetch("SELECT user_id, amount FROM economy")
            for value in values:
                self.bamboos[value['user_id']] = (value['amount'] or 0)

            values = await self.db.fetch("SELECT user_id, claimed FROM economy")
            for value in values:
                self.claims[value['user_id']] = (value['claimed'] or False)

            values = await self.db.fetch("SELECT user_id, daily FROM economy")
            for value in values:
                self.dailys[value['user_id']] = (value['daily'] or datetime.datetime.utcnow())

            values = await self.db.fetch("SELECT user_id, weekly FROM economy")
            for value in values:
                self.weeklys[value['user_id']] = (value['weekly'] or datetime.datetime.utcnow())

            self.afk_users = dict([(r['user_id'], True) for r in (await self.db.fetch('SELECT user_id, start_time FROM afk')) if r['start_time']])
            self.auto_un_afk = dict([(r['user_id'], r['auto_un_afk']) for r in (await self.db.fetch('SELECT user_id, auto_un_afk FROM afk')) if r['auto_un_afk'] is not None])

            values = await self.db.fetch("SELECT guild_id, dj_only FROM music")
            for value in values:
                self.dj_modes[value['guild_id']] = (value['dj_only'] or False)

            values = await self.db.fetch("SELECT guild_id, dj_role_id FROM music")
            for value in values:
                self.dj_roles[value['guild_id']] = (value['dj_role_id'] or False)

            if os.path.exists("system-logs/last-reboot.log"):
                f = open("system-logs/last-reboot.log", "r")
                channel_id = int(f.readline())
                f.close()
                
                delay = t.time() - os.path.getctime('system-logs/last-reboot.log')

                if delay > 120:
                    return

                if delay > 60:
                    embed = discord.Embed(title='Reboot took longed that usual', 
                                        description='Took me `{}` seconds to reboot'.format(round(delay, 2)),
                                        color=discord.Color.orange())
                else:
                    embed = discord.Embed(title='Reboot successful', 
                                        description='Took me `{}` seconds to reboot'.format(round(delay, 2)),
                                        color=discord.Color.green())
                
                await self.get_channel(channel_id).send(embed=embed)

    async def get_context(self, message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)

    async def get_pre(self, bot, message: discord.Message, raw_prefix: Optional[bool] = False) -> List[str]:
        if not message:
            return commands.when_mentioned_or(*self.PRE)(bot, message) if not raw_prefix else self.PRE
        if not message.guild:
            return commands.when_mentioned_or(*self.PRE)(bot, message) if not raw_prefix else self.PRE
        try:
            prefix = self.prefixes[message.guild.id]
        except KeyError:
            prefix = (await self.db.fetchval('SELECT guilds.prefix  FROM guilds WHERE guild_id = $1',
                                             message.guild.id)) or self.PRE
            prefix = prefix if prefix[0] else self.PRE

            self.prefixes[message.guild.id] = prefix

        if await bot.is_owner(message.author) and bot.noprefix is True:
            return commands.when_mentioned_or(*prefix, "")(bot, message) if not raw_prefix else prefix
        return commands.when_mentioned_or(*prefix)(bot, message) if not raw_prefix else prefix

    async def on_message(self, message: discord.Message) -> Optional[discord.Message]:
        if message.author.bot:
            return
            
        if self.user:
            if message.content == f'<@!{self.user.id}>':  # Sets faster
                prefixes = await self.get_pre(self, message, raw_prefix=True)
                embed = discord.Embed(title="My prefixes here are:")
                embed.description='`@DaPanda`'
                for prefix in prefixes:
                    embed.description += f', `{prefix}`'
                ctx = await self.get_context(message)
                return await ctx.send(embed=embed)
        
        await self.process_commands(message)