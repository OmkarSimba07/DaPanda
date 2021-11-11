from __future__ import annotations
import re
import asyncio
import typing
import discord
import helpers.consts as consts
import helpers.helper as helper
from typing import Any, Dict, Optional
from discord.ext import commands
from discord.ext.commands import Paginator as CommandPaginator
from discord.ext import menus

def color(context):
    if isinstance(context, commands.Context):
        return context.guild.me.color if context.guild.me.color != discord.Color.default() else discord.Color.blurple()
    elif isinstance(context, discord.Guild):
        return context.me.color if context.me.color != discord.Color.default() else discord.Color.blurple()
    else:
        raise TypeError('Invalid context')

class ViewPaginator(discord.ui.View):
    def __init__(
            self,
            source: menus.PageSource,
            *,
            ctx: commands.Context,
            check_embeds: bool = True,
            compact: bool = True,
    ):
        super().__init__()
        self.source: menus.PageSource = source
        self.check_embeds: bool = check_embeds
        self.ctx: commands.Context = ctx
        self.message: Optional[discord.Message] = None
        self.current_page: int = 0
        self.compact: bool = compact
        self.input_lock = asyncio.Lock()
        self.clear_items()
        self.fill_items()

    def fill_items(self) -> None:
        if not self.compact:
            self.numbered_page.row = 1
            self.stop_pages.row = 1

        if self.source.is_paginating():
            max_pages = self.source.get_max_pages()
            use_last_and_first = max_pages is not None and max_pages >= 2
            
            if use_last_and_first:
                self.add_item(self.go_to_first_page)  # type: ignore
            self.add_item(self.go_to_previous_page)  # type: ignore
            
            if not self.compact:
                self.add_item(self.go_to_current_page)  # type: ignore
            self.add_item(self.go_to_next_page)  # type: ignore
            
            if use_last_and_first:
                self.add_item(self.go_to_last_page)  # type: ignore
            
            if not self.compact:
                self.add_item(self.numbered_page)  # type: ignore
            self.add_item(self.stop_pages)  # type: ignore

    async def _get_kwargs_from_page(self, page: int) -> Dict[str, Any]:
        value = await discord.utils.maybe_coroutine(self.source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, discord.Embed):
            return {'embed': value, 'content': None}
        else:
            return {}

    async def show_page(self, interaction: discord.Interaction, page_number: int) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(page_number)
        if kwargs:
            if interaction.response.is_done():
                if self.message:
                    await self.message.edit(**kwargs, view=self)
            else:
                await interaction.response.edit_message(**kwargs, view=self)

    def _update_labels(self, page_number: int) -> None:
        self.go_to_first_page.disabled = page_number == 0
        if self.compact:
            max_pages = self.source.get_max_pages()
            self.go_to_last_page.disabled = max_pages is None or (page_number + 1) >= max_pages
            self.go_to_next_page.disabled = max_pages is not None and (page_number + 1) >= max_pages
            self.go_to_previous_page.disabled = page_number == 0
            return

        self.go_to_current_page.label = str(page_number + 1)
        self.go_to_previous_page.label = str(page_number)
        self.go_to_next_page.label = str(page_number + 2)
        self.go_to_next_page.disabled = False
        self.go_to_previous_page.disabled = False
        self.go_to_first_page.disabled = False

        max_pages = self.source.get_max_pages()
        if max_pages is not None:
            self.go_to_last_page.disabled = (page_number + 1) >= max_pages
            if (page_number + 1) >= max_pages:
                self.go_to_next_page.disabled = True
                self.go_to_next_page.label = '…'
            if page_number == 0:
                self.go_to_previous_page.disabled = True
                self.go_to_previous_page.label = '…'

    async def show_checked_page(self, interaction: discord.Interaction, page_number: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(interaction, page_number)
            elif max_pages > page_number >= 0:
                await self.show_page(interaction, page_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id in (self.ctx.bot.owner_id, self.ctx.author.id):
            return True
        await interaction.response.send_message(embed=discord.Embed(title='Error occured'
                                                ,description=f'This menu belongs to {self.ctx.author.mention}, sorry!'
                                                ,color=self.ctx.color
                                                ,ephemeral=True))
        return False

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)

    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        if interaction.response.is_done():
            await interaction.followup.send('An unknown error occurred, sorry', ephemeral=True)
        else:
            await interaction.response.send_message('An unknown error occurred, sorry', ephemeral=True)
        print(error)

    async def start(self) -> None:
        if self.check_embeds and not self.ctx.channel.permissions_for(self.ctx.me).embed_links:
            await self.ctx.send('Bot does not have embed links permission in this channel.')
            return

        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(0)
        self.message = await self.ctx.send(**kwargs, view=self)
    
    @discord.ui.button(label='≪', style=discord.ButtonStyle.grey)
    async def go_to_first_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        """go to the first page"""
        await self.show_page(interaction, 0)

    @discord.ui.button(label='◀', style=discord.ButtonStyle.blurple)
    async def go_to_previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        """go to the previous page"""
        await self.show_checked_page(interaction, self.current_page - 1)

    @discord.ui.button(label='◽', style=discord.ButtonStyle.grey, disabled=True)
    async def go_to_current_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(label='▶', style=discord.ButtonStyle.blurple)
    async def go_to_next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        """go to the next page"""
        await self.show_checked_page(interaction, self.current_page + 1)

    @discord.ui.button(label='≫', style=discord.ButtonStyle.grey)
    async def go_to_last_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        await self.show_page(interaction, self.source.get_max_pages() - 1)

    @discord.ui.button(label='Select Page', style=discord.ButtonStyle.grey, disabled=True)
    async def numbered_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        """lets you type a page number to go to"""
        if self.input_lock.locked():
            await interaction.response.send_message(embed=discord.Embed(title='Error occured!',description='Already waiting for your response...',color=0xe74c3c), ephemeral=True)
            return

        if self.message is None:
            return

        async with self.input_lock:
            channel = self.message.channel
            author_id = interaction.user and interaction.user.id
            await interaction.response.send_message(embed=discord.Embed(title=f'Available pages: {self.source._max_pages}',description='What page do you want to go to?',color=color(self.ctx)), ephemeral=True)

            def message_check(m):
                return m.author.id == author_id and channel.id == m.channel.id and m.content.isdigit()

            try:
                msg = await self.ctx.bot.wait_for('message', check=message_check, timeout=30.0)
            except asyncio.TimeoutError:
                await interaction.followup.send(embed=discord.Embed(title='Timed out!',description='Took too long.',color=0xe74c3c), ephemeral=True)
                await asyncio.sleep(5)
            else:
                page = int(msg.content)
                if page > self.source._max_pages:
                    return await interaction.followup.send(embed=discord.Embed(title='Invalid page!',description=f'Select page number from 1 to {self.source._max_pages}',color=0xe74c3c), ephemeral=True)
                try:
                    await msg.delete()
                except:
                    pass
                await self.show_checked_page(interaction, page - 1)

    @discord.ui.button(emoji='🗑️', style=discord.ButtonStyle.red)
    async def stop_pages(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Stops the pagination session."""
        await interaction.response.defer()
        await interaction.delete_original_message()
        self.stop()

class FieldPageSource(menus.ListPageSource):
    """A page source that requires (field_name, field_value) tuple items."""

    def __init__(self, entries, *, per_page=12):
        super().__init__(entries, per_page=per_page)
        self.embed = discord.Embed(colour=discord.Colour.blurple())

    async def format_page(self, menu, entries):
        self.embed.clear_fields()
        self.embed.description = discord.Embed.Empty

        for key, value in entries:
            self.embed.add_field(name=key, value=value, inline=False)

        maximum = self.get_max_pages()
        if maximum > 1:
            text = f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} entries)'
            self.embed.set_footer(text=text)

        return self.embed

class TextPageSource(menus.ListPageSource):
    def __init__(self, text, *, prefix='```', suffix='```', max_size=2000):
        pages = CommandPaginator(prefix=prefix, suffix=suffix, max_size=max_size - 200)
        for line in text.split('\n'):
            pages.add_line(line)

        super().__init__(entries=pages.pages, per_page=1)

    async def format_page(self, menu, content):
        maximum = self.get_max_pages()
        if maximum > 1:
            return f'{content}\nPage {menu.current_page + 1}/{maximum}'
        return content

class SimplePageSource(menus.ListPageSource):
    async def format_page(self, menu, entries):
        pages = []
        for index, entry in enumerate(entries, start=menu.current_page * self.per_page):
            pages.append(f'{index + 1}. {entry}')

        maximum = self.get_max_pages()
        if maximum > 1:
            footer = f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} entries)'
            menu.embed.set_footer(text=footer)

        menu.embed.description = '\n'.join(pages)
        return menu.embed

class SimplePages(ViewPaginator):
    """A simple pagination session reminiscent of the old Pages interface.

    Basically an embed with some normal formatting.
    """

    def __init__(self, entries, *, ctx: commands.Context, per_page: int = 12):
        super().__init__(SimplePageSource(entries, per_page=per_page), ctx=ctx)
        self.embed = discord.Embed(colour=discord.Colour.blurple())

class UrbanPageSource(menus.ListPageSource):
    BRACKETED = re.compile(r'(\[(.+?)\])')

    def __init__(self, data):
        super().__init__(entries=data, per_page=1)

    def cleanup_definition(self, definition, *, regex=BRACKETED):
        def repl(m):
            word = m.group(2)
            return f'[{word}](http://{word.replace(" ", "-")}.urbanup.com)'

        ret = regex.sub(repl, definition)
        if len(ret) >= 2048:
            return ret[0:2000] + ' [...]'
        return ret

    async def format_page(self, menu, entry):
        maximum = self.get_max_pages()
        title = f'{entry["word"]}: {menu.current_page + 1} out of {maximum}' if maximum else entry['word']
        embed = discord.Embed(title=title, colour=discord.Colour.blurple(), url=entry['permalink'])
        embed.set_footer(text=f'by {entry["author"]}')
        embed.description = self.cleanup_definition(entry['definition'])

        try:
            up, down = entry['thumbs_up'], entry['thumbs_down']
        except KeyError:
            pass
        else:
            embed.add_field(name='Votes', value=f'\N{THUMBS UP SIGN} {up} \N{THUMBS DOWN SIGN} {down}', inline=False)

        try:
            date = discord.utils.parse_time(entry['written_on'][0:-1])
        except (ValueError, KeyError):
            pass
        else:
            embed.timestamp = date

        return embed

class ServerEmotesEmbedPage(menus.ListPageSource):
    def __init__(self, data: list, guild: discord.Guild) -> discord.Embed:
        self.data = data
        self.guild = guild
        super().__init__(data, per_page=15)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = discord.Embed(title=f"{self.guild}'s emotes ({len(self.guild.emojis)})",
                        description="\n".join(f'{i+1}. {v}' for i, v in enumerate(entries, start=offset)))
        return embed

class QueueMenu(menus.ListPageSource):
    def __init__(self, data, ctx) -> discord.Embed:
        self.data = data
        self.ctx = ctx
        super().__init__(data, per_page=10)
        
    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        
        embed = discord.Embed(title='{} songs in the queue'.format(len(self.data)) if len(self.data) > 1 else '1 song in the queue'
                             ,colour=color(self.ctx))
        
        for i, v in enumerate(entries, start=offset):
            embed.add_field(name='\u200b',value=f'`{i+1}.` {v}',inline=False)
        
        return embed

class NodesMenu(menus.ListPageSource):
    """Nodes paginator class."""
    def __init__(self, data, ctx):
        self.data = data
        self.ctx = ctx
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = discord.Embed(title='<:rich_presence:658538493521166336> Node Stats', colour=self.ctx.color)
        
        for i, v in enumerate(entries, start=offset):
            embed.add_field(name=''.join(v.keys()),value=f'╰ {"".join(v.values())}', inline=True)
            #embed.add_field(name='Identifier',value=f'╰ {v[1]}', inline=False)
        return embed
    

class ServerInfoPageSource(menus.ListPageSource):
    def __init__(self, guilds: typing.List[discord.Guild], ctx: commands.Context):
        self.guilds = guilds
        self.context = ctx
        super().__init__(guilds, per_page=1)

    async def format_page(self, menu, guild: discord.Guild) -> discord.Embed:
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

        embed = discord.Embed(title=guild.name, color=guild.me.color)
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

        embed.add_field(name=f"<:rich_presence:658538493521166336> Channels ({len(guild.channels)})",
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

        return embed

class BlackListMenuPageSource(menus.ListPageSource):
    def __init__(self, data: list) -> discord.Embed:
        self.data = data
        super().__init__(data, per_page=15)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = discord.Embed(title="Blacklist menu",
                        description="\n".join(f'`{i+1}.` {data}\n' for i, data in enumerate(entries, start=offset)))
        return embed
    def is_paginating(self):
        if len(self.data) > self.per_page:
            return True
        else:
            return False

class AfkMenuPageSource(menus.ListPageSource):
    def __init__(self, data: list) -> discord.Embed:
        self.data = data
        super().__init__(data, per_page=5)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = discord.Embed(title="It looks like some of the users, that you've just mentioned, are AFK",
                        description="\n".join(f'`{i+1}.` {data}\n' for i, data in enumerate(entries, start=offset)))
        return embed

class LyricsPageSource(menus.ListPageSource):
    def __init__(self ,title: str ,href: str ,text: list, image: str ,ctx: commands.Context) -> discord.Embed:
        self.title = title
        self.href = href
        self.ctx = ctx
        self.text = text
        self.image = image
        super().__init__(text, per_page=2)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = discord.Embed(title=self.title,
                              url = self.href,
                              color=self.ctx.me.color,
                              description="\n".join(f'{data}' for i, data in enumerate(entries, start=offset)))
        embed.set_thumbnail(url=self.image)
        return embed

class HelpMenuPageSource(menus.ListPageSource):
    def __init__(self, data: typing.List[typing.SimpleNamespace], ctx,
                 help_class: commands.HelpCommand) -> discord.Embed:
        
        self.data = data
        self.ctx = ctx
        self.help = help_class
        super().__init__(data, per_page=1)

    async def format_page(self, menu, data):
        prefixes = await self.ctx.bot.get_pre(self.ctx.bot, self.ctx.message, raw_prefix=True)
        prefixList = self.ctx.me.mention
        for x in prefixes:
            prefixList += f', `{x}`'

        embed = discord.Embed(title="Help Menu", color=self.ctx.color,
        description=f"\n> <:rules:781581022059692043> Available prefixes: {prefixList}"
                    f"\n> 🕐 Uptime: {self.ctx.bot.uptime()}"
                    f"\n> <:slash:782701715479724063> Total Commands: {len(list(self.ctx.bot.commands))} | Usable by you (here): {len(await self.help.filter_commands(list(self.ctx.bot.commands), sort=True))} <:slash:782701715479724063>"
                    f"\n```diff"
                    f"\n+ Use panda.help [command] to get details on a command"
                    f"\n- <> = required argument"
                    f"\n- [] = optional argument"
                    f"``````css"
                    f"\n{self.ctx.clean_prefix}help [command|category|group]"
                    f"\n```"
                    f"\n")
        
        embed.add_field(name=data[0], value=data[1])
        
        embed.set_footer(text=("\n[G] - group of commands"
                               "\n(c) - regular command"))
        return embed

class GroupHelpPageSource(menus.ListPageSource):
    def __init__(self, group, cog_commands, color, *, prefix):
        super().__init__(entries=cog_commands, per_page=10)
        self.group = group
        self.prefix = prefix
        self.color = color
        
        if isinstance(group, discord.ext.commands.Group):
            self.title = f'Information about: {group.name.capitalize()}'
            if group.help:
                self.description = f"{(self.group.help).replace('%PRE%', self.prefix)}"
            else:
                self.description = discord.Embed.Empty
        
        else:
            self.title = f'Help - {group.qualified_name.capitalize()}'
            if group.description:
                self.description = self.group.description
            else:
                self.description = discord.Embed.Empty
            

    async def format_page(self, menu, cog_commands):
        embed = discord.Embed(title=self.title, description=self.description, color=self.color)

        command_signatures = [self.get_minimal_command_signature(c) for c in cog_commands]
        val = "\n".join(command_signatures)
        
        embed.add_field(name='\u200b', 
                        value=
                            f"\n```diff"
                            f"\n+ Use {self.prefix}help [command] to get details on a command"
                            f"\n- <> = required argument"
                            f"\n- [] = optional argument"
                            f"\n```"
                            f"\n__**Available commands**:__"
                            f"\n```yml"
                            f"\n{val}"
                            f"\n```"
                            )

        maximum = self.get_max_pages()
        if maximum > 1:
            embed.set_author(name=f'Page {menu.current_page + 1}/{maximum}')

        embed.set_footer(text=("\n[G] - group of commands"
                               "\n(c) - regular command"))
        return embed

    def get_minimal_command_signature(self, command):
        if isinstance(command, commands.Group):
            return '[G] %s%s %s' % (self.prefix, command.qualified_name, command.signature)
        return '(c) %s%s %s' % (self.prefix, command.qualified_name, command.signature)