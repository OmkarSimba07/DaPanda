import datetime
import inspect
import re
import io
import typing
import traceback
import discord
import asyncio
import os
import textwrap

from contextlib import redirect_stdout

from inspect import Parameter

from jishaku.codeblocks import codeblock_converter
from jishaku.features.baseclass import Feature

from discord import errors
from discord.ext import commands

import helpers.paginator as paginator
from helpers.context import CustomContext as Context

class dev(commands.Cog, command_attrs=dict(slash_command=False)):
    def __init__(self, client):
        self.client = client
        self._last_result = None
    
    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @commands.command()
    @commands.is_owner()
    async def steal(self, ctx: commands.Context, server_emoji: typing.Optional[typing.Union[discord.Embed, discord.PartialEmoji]], index: int = 1):
        """
        Clones an emoji into the `DaPanda Support Server`.
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
        guild = self.client.get_guild(875005644594372638)
        try:
            server_emoji = await guild.create_custom_emoji(name=server_emoji.name, image=file, reason=f"Stolen emoji, requested by {ctx.author}")
            embed = discord.Embed(color = discord.Color.blurple(),description = f"Successfully stolen {server_emoji}")
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(color = discord.Color.red(),description = f"Failed stealing {server_emoji}")
            await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def debugpermissions(self, ctx, guild_id: int, author_id: int = None):
        """Shows permission resolution for a channel and an optional author."""

        guild = self.client.get_guild(guild_id)
        if guild is None:
            return await ctx.send('Guild not found?')

        if author_id is None:
            member = guild.me
        else:
            member = guild.get_member(author_id)

        if member is None:
            return await ctx.send('Member not found?')

        await self.say_permissions(ctx, member)

    @commands.command(rest_is_raw=True, hidden=True)
    @commands.is_owner()
    async def echo(self, ctx, channelID: int, *, content):
        channel = self.client.get_channel(channelID)
        if channel is None:
            embed = discord.Embed(color = 0xFF0000)
            embed.description = "Could not find the channel."
            return await ctx.send(embed=embed)
        try:
            await channel.send(content)
            embed = discord.Embed(color = 0x5865f2)
            embed.description = f"Successfully sent your message in {channel.mention}."
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(color = 0xFF0000)
            embed.description = f"Something went wrong while sending your message."
            await ctx.send(embed=embed)
    
    @commands.command(help="Reloads all extensions", aliases=['relall', 'rall'], usage="[silent|channel]")
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def reloadall(self, ctx, argument: typing.Optional[str]):
        self.client.last_rall = datetime.datetime.utcnow()
        cogs_list = ""
        to_send = ""
        err = False
        first_reload_failed_extensions = []
        if argument == 'silent' or argument == 's':
            silent = True
        else:
            silent = False
        if argument == 'channel' or argument == 'c':
            channel = True
        else:
            channel = False

        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                cogs_list = f"{cogs_list} \n<a:windows_loading:636549313492680706> {filename[:-3]}"

        embed = discord.Embed(color=ctx.me.color, description=cogs_list)
        message = await ctx.send(embed=embed)

        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    self.client.reload_extension("cogs.{}".format(filename[:-3]))
                    to_send = f"{to_send} \n<a:Yes:889079191566422027> {filename[:-3]}"
                except Exception:
                    first_reload_failed_extensions.append(filename)

        for filename in first_reload_failed_extensions:
            try:
                self.client.reload_extension("cogs.{}".format(filename[:-3]))
                to_send = f"{to_send} \n<a:Yes:889079191566422027> {filename[:-3]}"

            except discord.ext.commands.ExtensionNotLoaded:
                to_send = f"{to_send} \n<a:No:889079913498415134> {filename[:-3]} - Not loaded"
            except discord.ext.commands.ExtensionNotFound:
                to_send = f"{to_send} \n<a:No:889079913498415134> {filename[:-3]} - Not found"
            except discord.ext.commands.NoEntryPointError:
                to_send = f"{to_send} \n<a:No:889079913498415134> {filename[:-3]} - No setup func"
            except discord.ext.commands.ExtensionFailed as e:
                traceback_string = "".join(traceback.format_exception(etype=None, value=e, tb=e.__traceback__))
                to_send = f"{to_send} \n<a:No:889079913498415134> {filename[:-3]} - Execution error"
                embed_error = f"\n<a:No:889079913498415134> {filename[:-3]} Execution error - Traceback" \
                              f"\n```py\n{traceback_string}\n```"
                if not silent:
                    target = ctx if channel else ctx.author
                    if len(embed_error) > 2000:
                        await target.send(file=io.StringIO(embed_error))
                    else:
                        await target.send(embed_error)

                err = True

        await asyncio.sleep(0.4)
        if err:
            if not silent:
                if not channel:
                    to_send = f"{to_send} \n\n📬 {ctx.author.mention}, I sent you all the tracebacks."
                else:
                    to_send = f"{to_send} \n\n📬 Sent all tracebacks here."
            if silent:
                to_send = f"{to_send} \n\n📭 silent, no tracebacks sent."
            embed = discord.Embed( title='Reloaded some extensions', description=to_send, color=ctx.color)
            await message.edit(embed=embed)
        else:
            embed = discord.Embed(title='Reloaded all extensions', description=to_send, color=ctx.color)
            await message.edit(embed=embed)

    @commands.command(pass_context=True, hidden=True, aliases=['e'])
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def eval(self, ctx, *, body: str):
        """Evaluates a code"""

        env = {
            'bot': self.client,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction(ctx.tick(True))
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command()
    @commands.is_owner()
    async def servers(self, ctx):
        """
        Shows the bots servers info.
        """
        source = paginator.ServerInfoPageSource(guilds=self.client.guilds, ctx=ctx)
        menu = paginator.ViewPaginator(source=source, ctx=ctx)
        await menu.start()
    
    @commands.is_owner()
    @commands.command(aliases=['push'])
    async def git_push(self, ctx, *, message: str):
        """Attempts to push changes to GitHub"""
        command = self.client.get_command('jsk git')
        await ctx.invoke(command, argument=codeblock_converter(f'add .\ngit commit -m "{message}"\ngit push'))

    @commands.is_owner()
    @commands.group(invoke_without_command=True)
    async def logs(self, ctx:Context) -> discord.Message:
        """This command represents a console"""
        await ctx.send_help(ctx.command)
    
    @commands.is_owner()
    @logs.command(name="info")
    async def logs_info(self, ctx: commands.Context):
        command = self.client.get_command('jsk cat')
        await ctx.invoke(command, argument='system-logs/client/info.log')

    @commands.is_owner()
    @logs.command(name="warnings")
    async def logs_warning(self, ctx: commands.Context):
        file = open("system-logs/client/warnings.log", "r")
        lines = [line.strip("\n") for line in file if line != "\n"]

        
        if len(lines) != 0:
            command = self.client.get_command('jsk cat')
            await ctx.invoke(command, argument='system-logs/client/warnings.log')
        else:
            await ctx.send(embed=discord.Embed(title='Something went wrong...', description='No warnings found in the logs', color=discord.Color.red()))

    @commands.is_owner()
    @logs.command(name="errors")
    async def logs_errors(self, ctx: commands.Context):
        file = open("system-logs/client/errors.log", "r")
        lines = [line.strip("\n") for line in file if line != "\n"]

        
        if len(lines) != 0:
            command = self.client.get_command('jsk cat')
            await ctx.invoke(command, argument='system-logs/client/errors.log')
        else:
            await ctx.send(embed=discord.Embed(title='Something went wrong...', description='No errors found in the logs', color=discord.Color.red()))

    @commands.is_owner()
    @logs.command(name="criticals")
    async def logs_errors(self, ctx: commands.Context):
        file = open("system-logs/client/criticals.log", "r")
        lines = [line.strip("\n") for line in file if line != "\n"]

        
        if len(lines) != 0:
            command = self.client.get_command('jsk cat')
            await ctx.invoke(command, argument='system-logs/client/criticals.log')
        else:
            await ctx.send(embed=discord.Embed(title='Something went wrong...', description='No criticals found in the logs', color=discord.Color.red()))

    @commands.command()
    @commands.is_owner()
    async def reboot(self, ctx:Context) -> discord.Message:
        """Reboots the bot"""
        embed=discord.Embed(title='Please confirm your actions', description='This action cannot be undone and there is \n possibility that the bot, can fail to boot')
        confirm = await ctx.confirm(embed)
        
        if confirm:
            f = open("system-logs/last-reboot.log", "w")
            f.write(str(ctx.channel.id))

            await asyncio.sleep(1.5)
            os.system("systemctl restart bot")
        else:
            return

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def blacklist(self, ctx: commands.Context) -> discord.Message:
        """ Blacklist management commands """
        await ctx.send_help(ctx.command)
    
    @blacklist.command(name="add")
    @commands.is_owner()
    async def blacklist_add(self, ctx: commands.Context,
                            user: discord.User,
                            *,
                            reason: str) -> discord.Message:
        """
        Adds a user to the bot blacklist
        """
        if user.id == ctx.me.id:
            return await ctx.send(embed=discord.Embed(title='Error Occured',description=f'You\'t blacklist me <:rooFat:744345098531242125>',color=discord.Color.red()))
        if user.id not in self.client.blacklist or not self.client.blacklist[user.id]:
            self.client.blacklist[user.id] = True
            await self.client.db.execute(
            "INSERT INTO blacklist(user_id, is_blacklisted, reason) VALUES ($1, $2, $3) "
            "ON CONFLICT (user_id) DO UPDATE SET is_blacklisted = $2",
            user.id, True, reason)
            return await ctx.send(embed=discord.Embed(title='User added to the blacklist',description=f'Successfully added {user.mention} to the blacklist with reason: {reason}'))
        else:
            return await ctx.send(embed=discord.Embed(title='Error Occured',description=f'Could not add {user.mention} to the blacklist, because {user.mention} is already in the blacklist',color=discord.Color.red()))

    @blacklist.command(name="remove")
    @commands.is_owner()
    async def blacklist_remove(self, ctx: commands.Context,
                                     user: discord.User) -> discord.Message:
        """
        Removes a user from the bot blacklist
        """
        if user.id in self.client.blacklist and self.client.blacklist[user.id]:
            self.client.blacklist[user.id] = False
            await self.client.db.execute(
                "DELETE FROM blacklist where user_id = $1",
                user.id)
            return await ctx.send(embed=discord.Embed(title='User removed from the blacklist',description=f'Successfully removed {user.mention} from the blacklist'))
        else:
            return await ctx.send(embed=discord.Embed(title='Error Occured',description=f'Could not remove {user.mention} to the blacklist, because {user.mention} is not in the blacklist',color=discord.Color.red()))

    @blacklist.command(name='check')
    @commands.is_owner()
    async def blacklist_check(self, ctx: commands.Context, user: discord.User):
        """
        Checks a user's blacklist status
        """
        try:
            status = self.client.blacklist[user.id]
        except KeyError:
            status = False
        
        if status:
            return await ctx.send(embed=discord.Embed(title='User Blacklisted',description=f"{user.mention} is blacklisted"))
        else:
            return await ctx.send(embed=discord.Embed(title='User Not Blacklisted',description=f"{user.mention} is not blacklisted"))

    @blacklist.command(name="list")
    @commands.is_owner()
    async def blacklist_list(self, ctx: commands.Context) -> discord.Message:
        """
        Adds a user to the bot blacklist
        """
        table = await self.client.db.fetch('TABLE blacklist')
        user_list = []
        for x in table:
            try:
                user = await commands.UserConverter().convert(ctx, str(x["user_id"]))
            except discord.ext.commands.UserNotFound:
                user = '@Unknown'

            user_list.append(f'{user} - {x["reason"]}')
        source = paginator.BlackListMenuPageSource(data=user_list)
        menu = paginator.ViewPaginator(source=source, ctx=ctx)
        await menu.start()

def setup(client):
    client.add_cog(dev(client))
