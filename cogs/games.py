import random

import discord
from discord.ext import commands
from games import tictactoe

def setup(bot):
    bot.add_cog(Games(bot))


class Games(commands.Cog, name='Games'):
    """
    🎮 General entertainment commands, and all other commands that don't fit within other categories.
    """
    def __init__(self, bot):
        self.bot = bot
    
    @commands.max_concurrency(1, commands.BucketType.user, wait=False)
    @commands.command(aliases=['ttt', 'tic'])
    async def tictactoe(self, ctx: commands.context):
        """Starts a tic-tac-toe game."""
        embed = discord.Embed(description=f'🔎 | {ctx.author.mention}'
                                        f'\n👀 |  A member is looking for someone to play **Tic-Tac-Toe**')
        embed.set_thumbnail(url='https://i.imgur.com/Vzso3N6.png')
        embed.set_author(name='Tic-Tac-Toe', icon_url='https://i.imgur.com/RTwo0om.png')
        player1 = ctx.author
        view = tictactoe.LookingToPlay(timeout=120)
        view.ctx = ctx
        view.message = await ctx.send(embed=embed,
                                    view=view)
        await view.wait()
        player2 = view.value
        if player2:
            starter = random.choice([player1, player2])
            ttt = tictactoe.TicTacToe(ctx, player1, player2, starter=starter)
            ttt.message = await view.message.edit(view=ttt, embed=discord.Embed(title='Tic Tac Toe',description=f'{starter.mention} goes first',color=embed.color))