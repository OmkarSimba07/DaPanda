import inspect
import discord
import os
import logging
import sys

from discord.ext import commands, ipc

class Ipc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, "ipc"):
            bot.ipc = ipc.Server(self.bot, secret_key=os.getenv('IPC'))
            bot.ipc.start()
        
        for n,f in inspect.getmembers(self):
            if n.startswith("get_"):
                bot.ipc.endpoints[n] = f.__call__

    @commands.Cog.listener()
    async def on_ipc_ready(self):
        """Called upon the IPC Server being ready"""
        logging.info("Ipc is ready.")

    @commands.Cog.listener()
    async def on_ipc_error(self, endpoint, error):
        """Called upon an error being raised within an IPC route"""
        logging.error(endpoint, "raised", error, file=sys.stderr)

    async def get_bot_stats(self, data) -> dict:
        shards = [shard for id,shard in self.bot.shards.items()]
        
        shards_ping = [round(x.latency * 1000, 2) for x in shards]
        shards_id = [x.id for x in shards]

        shards_guilds = {i: {"guilds": 0, "users": 0} for i in range(len(self.bot.shards))}
        for guild in self.bot.guilds:
            shards_guilds[guild.shard_id]["guilds"] += 1
            shards_guilds[guild.shard_id]["users"] += guild.member_count

        return {'shard_info': shards_guilds, 'shards_ping': shards_ping, 'shards_id': shards_id}

def setup(bot):
    bot.add_cog(Ipc(bot))