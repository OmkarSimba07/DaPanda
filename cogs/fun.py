import asyncio
import random
import urllib.parse
import aiowiki
import aiohttp

import discord
import typing
from discord.ext import commands
from helpers import consts

def setup(bot):
    bot.add_cog(Fun(bot))


class Fun(commands.Cog, name='Fun'):
    """
    🤪 General entertainment commands, and all other commands that don't fit within other categories.
    """
    def __init__(self, bot):
        self.bot = bot

    async def reddit(self, subreddit: str, title: bool = False, embed_type: str = 'IMAGE') -> discord.Embed:
        subreddit = await self.bot.reddit.subreddit(subreddit)
        post = await subreddit.random()

        if embed_type == 'IMAGE':
            while 'i.redd.it' not in post.url or post.over_18:
                post = await subreddit.random()

            embed = discord.Embed(title=f"{post.title}")
            embed.set_image(url=post.url)
            return embed

        if embed_type == 'POLL':
            while not hasattr(post, 'poll_data') or not post.poll_data or post.over_18:
                post = await (await self.bot.reddit.subreddit(subreddit)).random()

            iterations: int = 1
            options = []
            emojis = []
            for option in post.poll_data.options:
                num = f"{iterations}\U0000fe0f\U000020e3"
                options.append(f"{num} {option.text}")
                emojis.append(num)
                iterations += 1
                if iterations > 9:
                    iterations = 1

            embed = discord.Embed(color=discord.Color.random(),
                                  description='\n'.join(options))
            embed.title = post.title if title is True else None
            return embed, emojis

    @commands.command(name='meme')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def _meme(self, ctx: commands.Context) -> discord.Message:
        async with aiohttp.ClientSession() as session:
            meme = await session.get('https://some-random-api.ml/meme')
            meme = await meme.json()

        embed = discord.Embed(title=meme['caption'])
        embed.set_image(url=meme['image'])
        embed.set_footer(text=f'Category: {meme["category"]}')
        await ctx.send(embed=embed)

    @commands.command(name='joke')
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def _joke(self, ctx: commands.Context) -> discord.Message:
        async with aiohttp.ClientSession() as session:
            joke = await session.get('https://some-random-api.ml/joke')
            joke = await joke.json()

        await ctx.send(joke['joke'])

    @commands.command(name='panda', help="🐼 Shows a picture of a panda and a random fact about pandas")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def _panda(self, ctx: commands.Context) -> discord.Message:
        async with aiohttp.ClientSession() as session:
            img = await session.get('https://some-random-api.ml/img/panda')
            img = await img.json()
            fact = await session.get('https://some-random-api.ml/facts/panda')
            fact = await fact.json()

        embed = discord.Embed(title="Panda 🐼")
        embed.set_image(url=img['link'])
        embed.set_footer(text=fact['fact'])
        await ctx.send(embed=embed)

    @commands.command(name='cat', help="🐱 Shows a picture of a cat and a random fact about cats")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def _cat(self, ctx: commands.Context) -> discord.Message:
        async with aiohttp.ClientSession() as session:
            img = await session.get('https://some-random-api.ml/img/cat')
            img = await img.json()
            fact = await session.get('https://some-random-api.ml/facts/cat')
            fact = await fact.json()

        embed = discord.Embed(title="Cat 🐱")
        embed.set_image(url=img['link'])
        embed.set_footer(text=fact['fact'])
        await ctx.send(embed=embed)

    @commands.command(name='dog',help="🐼 Shows a picture of a dog and a random fact about dogs")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def _dog(self, ctx: commands.Context) -> discord.Message:
        async with aiohttp.ClientSession() as session:
            img = await session.get('https://some-random-api.ml/img/dog')
            img = await img.json()
            fact = await session.get('https://some-random-api.ml/facts/dog')
            fact = await fact.json()

        embed = discord.Embed(title="Dog 🐶")
        embed.set_image(url=img['link'])
        embed.set_footer(text=fact['fact'])
        await ctx.send(embed=embed)

    @commands.command(aliases=['wiki'])
    async def wikipedia(self, ctx, *, search: str):
        """ Searches on wikipedia, and shows the best results """
        async with ctx.typing():
            async with aiowiki.Wiki.wikipedia('en') as w:
                hyperlinked_titles = [f"[{p.title}]({(await p.urls()).view})" for p in (await w.opensearch(search))]

            iterations = 1
            enumerated_titles = []
            for title_hyperlink in hyperlinked_titles:
                enumerated_titles.append(f"`{iterations}.` {title_hyperlink}\n")
                iterations += 1

            if len(enumerated_titles) > 0:
                embed = discord.Embed(description='\n'.join(enumerated_titles))
                embed.set_author(icon_url="https://upload.wikimedia.org/wikipedia/en/thumb/8/80/"
                                        "Wikipedia-logo-v2.svg/512px-Wikipedia-logo-v2.svg.png",
                                name="Here are the top Wikipedia results:",
                                url="https://en.wikipedia.org/")
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=discord.Embed(title='Couldn\'t find anything, sorry !',color=discord.Color.red()))