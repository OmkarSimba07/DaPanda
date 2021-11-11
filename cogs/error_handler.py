import io
import itertools
import logging
import traceback
import copy
import discord
import difflib
import helpers.errors as errors
import cogs._music.errors as music_errors
from discord.ext import commands
from discord.ext.commands import BucketType


class ServerInvite(discord.ui.View):
    """ Buttons to the support server invite """
    def __init__(self ,bot):
        super().__init__()
        self.add_item(discord.ui.Button(emoji='<:partnernew:754032603081998336>', label='Support Server', url=bot.support_server))

def setup(bot):
    bot.add_cog(Handler(bot))


class Handler(commands.Cog):
    """
    🆘 Handles them errors 👀
    """

    def __init__(self, bot):
        self.bot = bot
        self.error_channel = 879286349973307392

    @commands.Cog.listener('on_command_error')
    async def error_handler(self, ctx, error):
        error = getattr(error, "original", error)
        ignored = (
            music_errors.NoPlayer,
            music_errors.FullVoiceChannel,
            music_errors.NotAuthorized,
            music_errors.IncorrectChannelError,
            music_errors.IncorrectTextChannelError,
            music_errors.AlreadyConnectedToChannel,
            music_errors.NoVoiceChannel,
            music_errors.QueueIsEmpty,
            music_errors.NoCurrentTrack,
            music_errors.NoConnection,
            music_errors.PlayerIsAlreadyPaused,
            music_errors.PlayerIsNotPaused,
            music_errors.NoMoreTracks,
            music_errors.InvalidTimeString,
            music_errors.NoPerms,
            music_errors.AfkChannel,
            music_errors.InvalidTrack,
            music_errors.InvalidPosition,
            music_errors.InvalidVolume,
            music_errors.AlreadyVoted,
            music_errors.NothingToShuffle,
            music_errors.NoLyrics,
            music_errors.LoadFailed,
            music_errors.NoMatches,
            music_errors.InvalidSeek,
            music_errors.InvalidInput,
            music_errors.LoopDisabled,
            music_errors.TrackFailed,
        )
        
        if isinstance(error, ignored):
            return

        if isinstance(error, errors.UserBlacklisted):
            info = await self.bot.db.fetchrow('SELECT * FROM blacklist WHERE user_id = $1', ctx.author.id)
            return await ctx.send(embed=discord.Embed(title='Forbidden',description=f"It seems like you've been blacklisted with reason: {info['reason']}",color=discord.Color.red()))

        if isinstance(error, errors.BotUnderMaintenance):
            return await ctx.send(embed=discord.Embed(title='Under Maintenance ⚠️', description='The bot is under maintenance, and i\'ts usage is limited' ,color=discord.Color.red()))

        if isinstance(error, commands.CommandNotFound):
            if self.bot.maintenance or ctx.author.id in self.bot.blacklist:
                return
            ignored_cogs = ('Bot Management', 'jishaku') if ctx.author.id != self.bot.owner_id else ()
            command_names = []
            for command in [c for c in self.bot.commands if c.cog_name not in ignored_cogs]:
                try:
                    if await command.can_run(ctx):
                        command_names.append([command.name] + command.aliases)
                except:
                    continue

            command_names = list(itertools.chain.from_iterable(command_names))

            matches = difflib.get_close_matches(ctx.invoked_with, command_names)

            if matches:
                embed = discord.Embed(title=f"Command not found",
                                      description=f"\n{f'Did you mean `{matches[0]}` ?' if matches else ''}")
                
                confirm = await ctx.confirm(embed, 
                                            delete_after_confirm=True, 
                                            delete_after_timeout=True,
                                            delete_after_cancel=True, buttons=(
                                            (ctx.tick(True), 'Yes', discord.ButtonStyle.green),
                                            (ctx.tick(False), 'No', discord.ButtonStyle.red)
                                        ), timeout=15)
                
                if confirm:
                    message = copy.copy(ctx.message)
                    message.content = message.content.replace(ctx.invoked_with, matches[0])
                    return await self.bot.process_commands(message)
                else:
                    return
            else:
                embed = discord.Embed(title=f"Command not found", description=f"Sorry, but the command **{ctx.invoked_with}** was not found.", color=discord.Color.red())
                return await ctx.send(embed=embed)

        if isinstance(error, discord.ext.commands.CheckAnyFailure):
            for e in error.errors:
                if not isinstance(error, commands.NotOwner):
                    error = e
                    break

        if isinstance(error, discord.ext.commands.BadUnionArgument):
            if error.errors:
                error = error.errors[0]

        if isinstance(error, commands.NotOwner):
            return await ctx.send(embed=discord.Embed(title='Error occured',description=f"You must own `{ctx.me.display_name}` to use `{ctx.command}`"))

        if isinstance(error, commands.TooManyArguments):
            return await ctx.send(embed=discord.Embed(title='Error occured',description=f"Too many arguments passed to the command!"))

        if isinstance(error, discord.ext.commands.MissingPermissions):
            missing = [(e.replace('_', ' ').replace('guild', 'server')).title() for e in error.missing_permissions]
            perms_formatted = ", ".join(missing[:-2] + [" and ".join(missing[-2:])])
            return await ctx.send(embed=discord.Embed(title='Error occured',description=f"You're missing **{perms_formatted}** permissions!"))

        if isinstance(error, discord.ext.commands.BotMissingPermissions):
            missing = [(e.replace('_', ' ').replace('guild', 'server')).title() for e in error.missing_permissions]
            perms_formatted = ", ".join(missing[:-2] + [" and ".join(missing[-2:])])
            return await ctx.send(embed=discord.Embed(title='Error occured', description=f"I'm missing **{perms_formatted}** permissions!", color=discord.Color.red()))

        if isinstance(error, discord.ext.commands.MissingRequiredArgument):
            missing = f"{error.param.name}"
            command = f"{ctx.clean_prefix}{ctx.command} {ctx.command.signature}"
            separator = (' ' * (len([item[::-1] for item in command[::-1].split(missing[::-1], 1)][::-1][0]) - 1))
            indicator = ('^' * (len(missing) + 2))
            desc = (f"```diff\n+ {command}\n- {separator}{indicator}\n- {missing} "
                                  f"is a required argument that is missing.\n```")
                    
            return await ctx.send(embed=discord.Embed(title='Missing Arguments !', description=desc, color=discord.Color.red()))

        if isinstance(error, commands.errors.PartialEmojiConversionFailure):
            return await ctx.send(f"`{error.argument}` is not a valid Custom Emoji")

        if isinstance(error, commands.errors.CommandOnCooldown):
            embed = discord.Embed(title='Error occured', color=discord.Color.red(), description=f'Please try again in {round(error.retry_after, 2)} seconds')
            embed.set_author(name='Command is on cooldown!', icon_url='https://i.imgur.com/izRBtg9.png')

            if error.type == BucketType.default:
                per = ""
            elif error.type == BucketType.user:
                per = "per user"
            elif error.type == BucketType.guild:
                per = "per server"
            elif error.type == BucketType.channel:
                per = "per channel"
            elif error.type == BucketType.member:
                per = "per member"
            elif error.type == BucketType.category:
                per = "per category"
            elif error.type == BucketType.role:
                per = "per role"
            else:
                per = ""

            embed.set_footer(text="Cooldown: {} per {}s {}".format(error.cooldown.rate, error.cooldown.per, per))
            return await ctx.send(embed=embed)

        if isinstance(error, discord.ext.commands.errors.MaxConcurrencyReached):
            embed = discord.Embed(title='Error occured', color=discord.Color.red(), description=f"Please try again once you are done running the command")
            embed.set_author(name='Command is already running!', icon_url='https://i.imgur.com/izRBtg9.png')

            if error.per == BucketType.default:
                per = ""
            elif error.per == BucketType.user:
                per = "per user"
            elif error.per == BucketType.guild:
                per = "per server"
            elif error.per == BucketType.channel:
                per = "per channel"
            elif error.per == BucketType.member:
                per = "per member"
            elif error.per == BucketType.category:
                per = "per category"
            elif error.per == BucketType.role:
                per = "per role"
            else:
                per = ""

            embed.set_footer(text="The limit is {} command(s) running {}".format(error.number, per))
            return await ctx.send(embed=embed)

        if isinstance(error, errors.NoQuotedMessage):
            return await ctx.send("<:reply:824240882488180747> Missing reply!")

        if isinstance(error, errors.MuteRoleNotFound):
            return await ctx.send("This server doesn't have a mute role, or it was deleted!"
                                  "\nAssign it with `muterole [new_role]` command, "
                                  "or can create it with the `muterole create` command")

        if isinstance(error, errors.NoEmojisFound):
            embed = discord.Embed(title='Error occured', description="I couldn't find any emojis there.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        if isinstance(error, commands.errors.MemberNotFound):
            embed = discord.Embed(title='Error occured', description="`{}` doesn't seem to be an actuall member of this server".format(error.argument), color=discord.Color.red())
            return await ctx.send(embed=embed)

        if isinstance(error, commands.errors.UserNotFound):
            embed = discord.Embed(title='Error occured', description="`{}` doesn't seem to be an actuall discord user".format(error.argument), color=discord.Color.red())
            return await ctx.send(embed=embed)

        if isinstance(error, commands.BadArgument):
            error = error or "Bad argument given!"
            
            embed = discord.Embed(title='Error occured', description=error, color=discord.Color.red())
            return await ctx.send(embed=embed)

        if isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(title='Error occured', description="This command does not work inside DMs", color=discord.Color.red())
            return await ctx.send(embed=embed)

        if isinstance(error, commands.PrivateMessageOnly):
            embed = discord.Embed(title='Error occured', description="This command only works inside DMs", color=discord.Color.red())
            return await ctx.send(embed=embed)

        if isinstance(error, commands.NSFWChannelRequired):
            embed = discord.Embed(title='Error occured', description="This commands only works in NSFW channels", color=discord.Color.red())
            return await ctx.send(embed=embed)

        else:
            error_channel = self.bot.get_channel(self.error_channel)

            nl = '\n'
            embed = discord.Embed(title="**An unexpected error ocurred! For more info, join my support server**",
                                description=f"> ```py\n> {f'{nl}> '.join(str(error).split(nl))}\n> ```",
                                color=discord.Color.red())
            await ctx.send(embed=embed, view=ServerInvite(self.bot))

            traceback_string = "".join(traceback.format_exception(
                etype=None, value=error, tb=error.__traceback__))

            if ctx.guild:
                command_data = f"Invoked By: {ctx.author.display_name} ({ctx.author.name}#{ctx.author.discriminator})" \
                            f"\nCommand Name: {ctx.message.content[0:1700]}" \
                            f"\nGuild: Name: {ctx.guild.name}" \
                            f"\nGuild ID: {ctx.guild.id}" \
                            f"\nGuild Owner: {ctx.guild.owner.display_name} ({ctx.guild.owner.name}#{ctx.guild.owner.discriminator})" \
                            f"\nChannel: {ctx.channel.name} ({ctx.channel.id})"
            else:
                command_data = f"command: {ctx.message.content[0:1700]}" \
                            f"\nCommand executed in DMs"

            to_send = f"```yaml\n{command_data}``````py\n{ctx.command} " \
                    f"command raised an error:\n{traceback_string}\n```"
            if len(to_send) < 2000:
                try:
                    sent_error = await error_channel.send(to_send)

                except (discord.Forbidden, discord.HTTPException):
                    sent_error = await error_channel.send(f"```yaml\n{command_data}``````py Command: {ctx.command}"
                                                        f"Raised the following error:\n```",
                                                        file=discord.File(io.StringIO(traceback_string),
                                                                            filename='traceback.py'))
            else:
                sent_error = await error_channel.send(f"```yaml\n{command_data}``````py Command: {ctx.command}"
                                                    f"Raised the following error:\n```",
                                                    file=discord.File(io.StringIO(traceback_string),
                                                                        filename='traceback.py'))
            try:
                await sent_error.add_reaction('🗑')
            except (discord.HTTPException, discord.Forbidden):
                pass
            raise error
            
    @commands.Cog.listener('on_raw_reaction_add')
    async def wastebasket(self, payload: discord.RawReactionActionEvent):
        if payload.channel_id == self.error_channel and await \
                self.bot.is_owner(payload.member) and str(payload.emoji == '🗑'):
            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            if not message.author == self.bot.user:
                return
            error = '```py\n' + '\n'.join(message.content.split('\n')[7:])
            await message.edit(content=f"{error}```fix\n✅ Marked as fixed by the developers.```")
            await message.clear_reactions()
        """
        if payload.channel_id == suggestions_channel and await \
                self.bot.is_owner(payload.member) and str(payload.emoji) in ('🔼', '🔽'):

            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            if not message.author.bot or not message.embeds:
                return
            embed = message.embeds[0]

            sub = {
                'Suggestion ': 'suggestion',
                'suggestion ': 'suggestion',
                'Denied ': '',
                'Approved ': ''
            }

            pattern = '|'.join(sorted(re.escape(k) for k in sub))
            title = re.sub(pattern, lambda m: sub.get(m.group(0).upper()), embed.title, flags=re.IGNORECASE)

            scheme = {
                '🔼': (0x6aed64, f'Approved suggestion {title}'),
                '🔽': (0xf25050, f'Denied suggestion {title}')
            }[str(payload.emoji)]

            embed.title = scheme[1]
            embed.colour = scheme[0]
            # noinspection PyBroadException
            try:
                user_id = int(embed.footer.text.replace("Sender ID: ", ""))
            except:
                user_id = None
            suggestion = embed.description

            if str(payload.emoji) == '🔼' and user_id:
                try:
                    user = (self.bot.get_user(user_id) or (await self.bot.fetch_user(user_id)))
                    user_embed = discord.Embed(title="🎉 Suggestion approved! 🎉",
                                               description=f"**Your suggestion has been approved! "
                                                           f"You suggested:**\n{suggestion}")
                    user_embed.set_footer(text='Reply to this DM if you want to stay in contact '
                                               'with us while we work on your suggestion!')
                    await user.send(embed=user_embed)
                    embed.set_footer(text=f"DM sent - ✅ - {user_id}")
                except (discord.Forbidden, discord.HTTPException):
                    embed.set_footer(text=f"DM sent - ❌ - {user_id}")
            else:
                embed.set_footer(text='Suggestion denied. No DM sent.')

            await message.edit(embed=embed)
            await message.clear_reactions()
        """