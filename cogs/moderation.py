import typing
import helpers.context as Context
import discord

from discord.ext import commands, menus
from discord.ext.menus.views import ViewMenuPages



class BansMenu(menus.ListPageSource):
    """Player queue paginator class."""
    def __init__(self, data, ctx):
        self.data = data
        self.ctx = ctx
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = discord.Embed(title=f'Showing total of {len(self.data)} bans',colour=self.ctx.color)
        for i, v in enumerate(entries, start=offset):
            embed.add_field(name='\u200b',value=f'`{i+1}.` {v}',inline=False)
        return embed
    def is_paginating(self):
        if len(self.data) > self.per_page:
            return True
        else:
            return False

class Moderation(commands.Cog):
    """
        🔨 Commands to facilitate server moderation, and all utilities for admins and mods.
    """
    def __init__(self, client):
        self.client = client


    def can_execute_action(self, ctx, user, target):
        if isinstance(target, discord.Member):
            return user == ctx.guild.owner or \
                (user.top_role > target.top_role and
                    target != ctx.guild.owner)
        elif isinstance(target, discord.User):
            return True
        raise TypeError(f'argument \'target\' expected discord.User, received {type(target)} instead')

    @commands.command()
    async def cleanup(self, ctx: commands.Context, amount: int = 25):
        """
        Cleans up the bots messages.
        """
        if amount > 25:
            if not ctx.channel.permissions_for(ctx.author).manage_messages:
                await ctx.send("You must have `manage_messages` permission to perform a search greater than 25")
                return
            if not ctx.channel.permissions_for(ctx.me).manage_messages:
                await ctx.send("I need the `manage_messages` permission to perform a search greater than 25")
                return

        async with ctx.typing():
            if ctx.channel.permissions_for(ctx.me).manage_messages:

                def check(msg):
                    return msg.author == ctx.me or msg.content.startswith('panda.')

                deleted = await ctx.channel.purge(limit=amount, check=check, before=ctx.message.created_at)
            else:
                def check(msg):
                    return msg.author == ctx.me

                deleted = await ctx.channel.purge(limit=amount, check=check, bulk=False, before=ctx.message.created_at)
            spammers = typing.Counter(m.author for m in deleted)
            deleted = len(deleted)
            messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
            if deleted:
                messages.append('')
                spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
                messages.extend(f'**{name.mention}**: {count}' for name, count in spammers)

            to_send = '\n'.join(messages)
            if len(to_send) > 2000:
                await ctx.send(f'Successfully removed {deleted} messages.', delete_after=10)
            else:
                await ctx.send(to_send, delete_after=10)

    @commands.command(help="Gets the current guild's list of bans")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True, ban_members=True)
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def bans(self, ctx: commands.Context) -> discord.Message:
        bans = await ctx.guild.bans()
        if not bans:
            return await ctx.send(embed=discord.Embed(title="There are no banned users in this server"))
        desc = []
        for ban_entry in bans:
            desc.append(f"Discord username: `{ban_entry.user}` | Reason: `{ban_entry.reason}`")
        pages = ViewMenuPages(source=BansMenu(sorted(desc), ctx), clear_reactions_after=True)
        await pages.start(ctx)

    @commands.group(invoke_without_command=True)
    async def prefixes(self, ctx: commands.Context) -> discord.Message:
        """ Lists all the bots prefixes. """
        prefixes = await self.client.get_pre(self.client, ctx.message, raw_prefix=True)
        embed = discord.Embed(title="Here are my prefixes:",
                              description='`@DaPanda`')
        for prefix in prefixes:
            embed.description += f', `{prefix}`'
        embed.add_field(name="Available prefix commands:", value=f"```fix"
                                                                 f"\n{ctx.clean_prefix}{ctx.command} add"
                                                                 f"\n{ctx.clean_prefix}{ctx.command} remove"
                                                                 f"\n{ctx.clean_prefix}{ctx.command} reset"
                                                                 f"\n```")
        return await ctx.send(embed=embed)

    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    @prefixes.command(name="add")
    async def prefixes_add(self, ctx: commands.Context, new: str) -> discord.Message:
        """Adds a prefix to the bots prefixes.\nuse quotes to add spaces: %PRE%prefix \"(NEW PREFIX) \" """

        old = list(await self.client.get_pre(self.client, ctx.message, raw_prefix=True))

        if len(new) > 50:
            return await ctx.send("Prefixes can only be up to 50 characters!")

        if len(old) > 30:
            return await ctx.send("You can only have up to 20 prefixes!")

        if new not in old:
            old.append(new)
            await self.client.db.execute(
                "INSERT INTO guilds(guild_id, prefix) VALUES ($1, $2) "
                "ON CONFLICT (guild_id) DO UPDATE SET prefix = $2",
                ctx.guild.id, old)

            self.client.prefixes[ctx.guild.id] = old

            return await ctx.send(embed=discord.Embed(title='Prefix Added',description=f'Successfully added `{new}` to the prefix list'))
        else:
            return await ctx.send(embed=discord.Embed(title='Error Occured',description=f'Could not add `{new}` to the prefix list, because `{new}` is already in the prefix list',color=discord.Color.red()))

    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    @prefixes.command(name="remove", aliases=['delete'])
    async def prefixes_remove(self, ctx: commands.Context, prefix: str):
        """Removes a prefix from the bots prefixes.\nuse quotes to add spaces: %PRE%prefix \"PREFIX \" """

        old = list(await self.client.get_pre(self.client, ctx.message, raw_prefix=True))

        if prefix in old:
            old.remove(prefix)
            await self.client.db.execute(
                "INSERT INTO guilds(guild_id, prefix) VALUES ($1, $2) "
                "ON CONFLICT (guild_id) DO UPDATE SET prefix = $2",
                ctx.guild.id, old)

            self.client.prefixes[ctx.guild.id] = old

            return await ctx.send(embed=discord.Embed(title='Prefix Removed',description=f'Successfully removed `{prefix}` from the prefix list'))
        else:
            return await ctx.send(embed=discord.Embed(title='Error Occured',description=f'Could not remove `{prefix}` from the prefix list, because `{prefix}` is not in the prefix list',color=discord.Color.red()))

    @commands.check_any(commands.has_permissions(manage_guild=True), commands.is_owner())
    @prefixes.command(name="reset", aliases=['deleteall','delall'])
    async def prefixes_clear(self, ctx):
        """ Clears the bots prefixes, resetting it to default. """
        await self.client.db.execute(
            "INSERT INTO guilds(guild_id, prefix) VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO UPDATE SET prefix = $2",
            ctx.guild.id, None)
        self.client.prefixes[ctx.guild.id] = self.client.PRE
        return await ctx.send(embed=discord.Embed(title='Prefixes Cleared',description=f'All of my custom prefixes associated with this server has been cleared'))
    
    @commands.has_permissions(manage_messages=True)
    @commands.command()
    async def purge(self, ctx:Context, *, amount:int):
        if amount < 2000:
            purged = await ctx.channel.purge(limit=amount)
            await ctx.send(embed=discord.Embed(title='Purge Completed', description='{} messages has been deleted'.format(len(purged))))
        
        else:
            return await ctx.send(embed=discord.Embed(title='Can\'t do that', description='I can\'t purge more than 2000 message per use'))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True, ban_members=True)
    async def ban(self, ctx: Context, member:discord.Member, delete_days: typing.Optional[int] = 1, *, reason: str = 'Not specified'):
        """Bans a member from the server"""
        if delete_days and not 8 > delete_days > -1:
            raise commands.BadArgument("**delete_days** must be between 0 and 7 days")

        if member.id == self.client.user.id:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='You may not ban me <:rooSad:901660365773996084>'))
        
        if member.guild_permissions.administrator:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='You may not ban an adminstator'))

        if member.id == ctx.guild.owner.id:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='You may not ban the owner of the guild'))
        
        if ctx.author.top_role < member.top_role:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='You may not ban members that have higher tier roles than you'))

        try:
            await member.send(embed=discord.Embed(title='Banned'.format(ctx.guild.name),
            description='You were banned from `{}` by `{}` with reason: {}'.format(ctx.guild.name, ctx.author, reason),
            color=discord.Color.red()))

            dm = True
        except discord.HTTPException or discord.Forbidden:
            dm = False
            pass
        
        await ctx.guild.ban(member, reason=f"Banned by {ctx.author} with reason: {reason}", delete_message_days=delete_days)
        embed=discord.Embed(title='Member banned')
        embed.description='{} was banned from moderator {} with reason: {}'.format(member.mention, ctx.author.mention, reason)
        embed.set_footer(text="DM sent: {}".format(dm))

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True, ban_members=True)
    @commands.cooldown(1, 3.0, commands.BucketType.user)
    async def unban(self, ctx: Context, user: discord.User):
        """Unbans a member from the server"""
        try:
            await ctx.guild.unban(user)
        except discord.NotFound:
            raise commands.BadArgument(f'**{discord.utils.escape_markdown(str(user))}** is not banned on this server!')
        
        return await ctx.send(f"Unbanned **{discord.utils.escape_markdown(str(user))}**")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True, kick_members=True)
    async def kick(self, ctx: Context, member:discord.Member, *, reason: str = 'Not specified'):
        """Kicks a member from the server"""
        if member.id == self.client.user.id:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='You may not kick me <:rooSad:901660365773996084>'))
        
        if member.guild_permissions.administrator:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='You may not kick an adminstator'))

        if member.id == ctx.guild.owner.id:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='You may not kick the owner of the guild'))
        
        if ctx.author.top_role < member.top_role:
            return await ctx.send(embed=discord.Embed(title='Something went wrong...', description='You may not kick members that have higher tier roles than you'))

        try:
            await member.send(embed=discord.Embed(title='Kicked'.format(ctx.guild.name),
            description='You were kicked from `{}` by `{}` with reason: {}'.format(ctx.guild.name, ctx.author, reason),
            color=discord.Color.red()))

            dm = True
        except discord.HTTPException or discord.Forbidden:
            dm = False
        
        await ctx.guild.kick(member, reason=f"Kicked by {ctx.author} with reason: {reason}")
        
        embed=discord.Embed(title='Member kicked')
        embed.description='{} was kicked by moderator {} with reason: {}'.format(member.mention, ctx.author.mention, reason)
        embed.set_footer(text="DM sent: {}".format(dm))

        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(Moderation(client))
