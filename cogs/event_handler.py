import logging
import discord
import helpers.paginator as paginator
import helpers.helper as helper
from discord.ext import commands
from .utils import time


def setup(bot):
    bot.add_cog(Event_Handler(bot))


class Event_Handler(commands.Cog):
    """Handles them events 👀"""

    def __init__(self, bot):
        self.client = bot
        self.log_channel = 890080860349530123
    
    @commands.Cog.listener('on_autopost_success')
    async def on_auto_post(self):
        logging.info(f'Posted server count ({self.client._topgg.guild_count}), shard count ({self.client.shard_count})')

    @commands.Cog.listener('on_dbl_vote')
    async def on_topgg_vote(self, data):
        """An event that is called whenever someone votes for the bot on Top.gg."""
        channel = self.client.get_channel(905982411966390342)
        user = await self.client.fetch_user(data["user"])

        if data["isWeekend"]:
            amount = 600
        else:
            amount = 1200

        embed = discord.Embed(title='Received vote', color=discord.Color.green())
        if user.avatar:
            embed.set_thumbnail(url=user.avatar)
        embed.description = f"{user.mention if user in channel.guild.members else user} just voted on top.gg and earned themselves **{amount}** <:bamboo:911241395434565652>"

        view=helper.Url(url=self.client.vote_url,
                        emoji='<:top_gg:895376601112514581>',
                        label='Top.gg')
        await channel.send(embed=embed, view=view)

        await self.client.db.execute(
                "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                int(data["user"]), self.client.bal(int(data["user"])) + amount)

        self.client.bamboos[int(data["user"])] = self.client.bal(int(data["user"])) + amount

    @commands.Cog.listener('on_message')
    async def on_afk_user_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.bot:
            return
        if message.author.id in self.client.afk_users:
            try:
                if self.client.auto_un_afk[message.author.id] is False:
                    return
            except KeyError:
                pass
            self.client.afk_users.pop(message.author.id)
            ctx: commands.Context = await self.client.get_context(message)

            await self.client.db.execute('INSERT INTO afk (user_id, start_time, reason) VALUES ($1, null, null) '
                                      'ON CONFLICT (user_id) DO UPDATE SET start_time = null, reason = null', message.author.id)
            embed = discord.Embed(title=f'Status Changed <:online2:464520569975603200>',description=f'{message.author.mention} is no longer AFK',color=discord.Color.green())
            await ctx.send(embed=embed)
    
    @commands.Cog.listener('on_message')
    async def on_afk_user_mention(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if message.author == self.client.user:
            return
        if message.mentions:
            user_data = []
            pinged_afk_user_ids = list(set([u.id for u in message.mentions]).intersection(self.client.afk_users))
            for user_id in pinged_afk_user_ids:
                member = message.guild.get_member(user_id)
                if member and member.id != message.author.id:
                    info = await self.client.db.fetchrow('SELECT * FROM afk WHERE user_id = $1', user_id)
                    user_data.append(f'{member.mention} has been afk for `{time.human_timedelta(info["start_time"], accuracy=2, suffix=False)}`, with reason: {info["reason"]}\n')
            if len(user_data) > 0:
                ctx: commands.Context = await self.client.get_context(message)
                source = paginator.AfkMenuPageSource(data=user_data)
                menu = paginator.ViewPaginator(source=source, ctx=ctx)
                await menu.start()

    @commands.Cog.listener('on_guild_join')
    async def on_guild_join(self, guild):
        try:
            log = (await guild.audit_logs(limit = 1, action = discord.AuditLogAction.bot_add).flatten())[0]
            user = log.user.name
        except (discord.Forbidden, discord.HTTPException):
            user = 'Unknown'

        log_channel = self.client.get_channel(self.log_channel)
        guild_data = (
            f"\n```yml"
            f"\nInviter: {user}"
            f"\nGuild: Name: {guild.name}"
            f"\nGuild ID: {guild.id}"
            f"\nGuild Owner: {guild.owner.display_name} ({guild.owner.name}#{guild.owner.discriminator})"
            f"\n```"
                    )
        embed=discord.Embed(title='Joined a guild',description=guild_data,color=discord.Color.green())
        await log_channel.send(embed=embed)

    @commands.Cog.listener('on_guild_remove')
    async def on_guild_remove(self, guild):
        log_channel = self.client.get_channel(self.log_channel)
        guild_data = (
            f"\n```yml"
            f"\nGuild: Name: {guild.name}"
            f"\nGuild ID: {guild.id}"
            f"\nGuild Owner: {guild.owner.display_name} ({guild.owner.name}#{guild.owner.discriminator})"
            f"\n```"
                    )
        embed=discord.Embed(title='Removed from a guild',description=guild_data,color=discord.Color.red())
        await log_channel.send(embed=embed)
    