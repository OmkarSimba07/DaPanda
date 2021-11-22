import asyncio
import logging
import discord
import typing
import random

from discord.ext import commands
from .utils import time as time
from helpers import helper
from helpers.context import CustomContext as Context
import helpers.paginator as paginator

class Economy(commands.Cog):
    """💰 Economy related commands"""
    def __init__(self, client):
        self.client = client
    
    class Claim(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.add_item(discord.ui.Button(label='Claim up to 1200 Bamboo', emoji='<:bamboo:911241395434565652>', style=discord.ButtonStyle.blurple))
        
    @commands.command(aliases=['bal'])
    async def balance(self, ctx: Context, member:typing.Optional[discord.Member]):
        if not member:
            member = ctx.author

        embed = discord.Embed(title="Showing balance for {}".format(member))
        embed.description = "{}'s current balance is **{:,}** <:bamboo:911241395434565652>".format(member.mention, self.client.bal(member.id))
        
        await ctx.send(embed=embed, view=self.Claim())

    @commands.command(aliases=['give'])
    async def send(self, ctx: Context, member:discord.Member, amount:int):
        author_bal = self.client.bal(ctx.author.id)
        member_bal = self.client.bal(member.id)

        if member_bal >= 9223372036854775807 - amount:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "My maximum amount of <:bamboo:911241395434565652> that you can send is **9,223,372,036,854,775,807**"
            return await ctx.send(embed=embed)

        if member == ctx.author:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "You can't give <:bamboo:911241395434565652> to yoursef"
            return await ctx.send(embed=embed)
        
        if amount < 200:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "My minimum amount of <:bamboo:911241395434565652> that you can send is **200**"
            return await ctx.send(embed=embed)

        if amount > 9223372036854775807:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "My maximum amount of <:bamboo:911241395434565652> that you can send is **9,223,372,036,854,775,807**"
            return await ctx.send(embed=embed)

        if amount > author_bal:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "You can't afford to do that !"
            return await ctx.send(embed=embed)
        
        embed=discord.Embed(title='Please confirm your actions')
        embed.description = 'Are you sure you want to send **{:,}** to `{}` ?'.format(amount, member)

        confirm = await ctx.confirm(embed)
        if confirm:
            await self.client.db.execute(
                    "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                    "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                    member.id, member_bal + amount)
            self.client.bamboos[member.id] = self.client.bal(member.id) + amount
            
            await self.client.db.execute(
                    "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                    "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                    ctx.author.id, author_bal - amount)
            self.client.bamboos[ctx.author.id] =  self.client.bal(ctx.author.id) - amount
            

            embed=discord.Embed(title='Bamboo sent')
            embed.description = 'Successfully sent send **{:,}** <:bamboo:911241395434565652> to `{}` !'.format(amount, member)
            await ctx.send(embed=embed)
        
        else:
            return

    @commands.command(aliases=['donate'])
    async def giveaway(self, ctx: Context, amount:int):
        member = random.choice(ctx.guild.members)

        author_bal = self.client.bal(ctx.author.id)
        member_bal = self.client.bal(member.id)

        if member_bal >= 9223372036854775807 - amount:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "My maximum amount of <:bamboo:911241395434565652> that you can send is **9,223,372,036,854,775,807**"
            return await ctx.send(embed=embed)

        if member == ctx.author:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "You can't give <:bamboo:911241395434565652> to yoursef"
            return await ctx.send(embed=embed)
        
        if amount < 200:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "My minimum amount of <:bamboo:911241395434565652> that you can send is **200**"
            return await ctx.send(embed=embed)

        if amount > 9223372036854775807:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "My maximum amount of <:bamboo:911241395434565652> that you can send is **9,223,372,036,854,775,807**"
            return await ctx.send(embed=embed)

        if amount > author_bal:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "You can't afford to do that !"
            return await ctx.send(embed=embed)
        
        embed=discord.Embed(title='Please confirm your actions')
        embed.description = 'Are you sure you want to send **{:,}** to a random member of {} ?'.format(amount, ctx.guild)

        confirm = await ctx.confirm(embed)
        if confirm:
            await self.client.db.execute(
                    "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                    "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                    member.id, member_bal + amount)
            self.client.bamboos[member.id] = self.client.bal(member.id) + amount

            
            await self.client.db.execute(
                    "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                    "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                    ctx.author.id, author_bal - amount)
            self.client.bamboos[ctx.author.id] =  self.client.bal(ctx.author.id) - amount
            

            embed=discord.Embed(title='Bamboo sent')
            embed.description = 'Successfully sent send **{:,}** <:bamboo:911241395434565652> to {} !'.format(amount, member)
            await ctx.send(embed=embed)
        
        else:
            return

    @commands.command(aliases=['top'])
    async def leaderboard(self, ctx: Context):
        entry = []
        list = dict(sorted(self.client.bamboos.items(), key=lambda i: i[1], reverse=True))
        
        if len(list) == 0:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "The leaderboard for {} is currently empty".format(ctx.guild)
            return await ctx.send(embed=embed)

        for id in list:
            bal = self.client.bal(id)
            
            try:
                member = await commands.MemberConverter().convert(ctx, str(id))
            except discord.ext.commands.MemberNotFound:
                continue
            
            entry.append('{} — **{:,}** <:bamboo:911241395434565652>'.format(member, bal))

        menu = paginator.ViewPaginator(paginator.Leaderboard(entry, ctx), ctx=ctx)
        await menu.start()

    @commands.command()
    async def coinflip(self, ctx:Context, amount:int, bet:str):
        """Bet chosen amount of Bamboo on either `heads` or `tails`"""
        author_bal = self.client.bal(ctx.author.id)
        options = ['heads', 'tails']

        if bet.lower() not in options:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "The available options for bet are `heads` or `tails`"
            return await ctx.send(embed=embed)

        if amount < 25:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "My minimum amount of <:bamboo:911241395434565652> that you can bet is **25**"
            return await ctx.send(embed=embed)

        if amount > author_bal:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "You don't have that much <:bamboo:911241395434565652> to bet"
            return await ctx.send(embed=embed)

        embed=discord.Embed(title='Please confirm your actions')
        embed.description = 'Are you sure you want to bet **{:,}** to `{}` ?'.format(amount, bet.lower())

        confirm = await ctx.confirm(embed)
        if confirm:
            result = random.choice(options)

            if bet.lower() != result:
                embed = discord.Embed(title="Unlucky...", color=discord.Color.red())
                embed.description = "You've picked `{}`, but it rolled out `{}`. **You've lost {:,} <:bamboo:911241395434565652>**".format(bet.lower(), result, amount)
                await ctx.send(embed=embed)

                await self.client.db.execute(
                            "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                            "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                            ctx.author.id, author_bal - amount)
                self.client.bamboos[ctx.author.id] =  self.client.bal(ctx.author.id) - amount

            else:
                embed = discord.Embed(title="You've won !", color=discord.Color.green())
                embed.description = "You've guessed right, and you've won **{:,}** <:bamboo:911241395434565652>".format(amount)
                await ctx.send(embed=embed)

                await self.client.db.execute(
                            "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                            "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                            ctx.author.id, author_bal + amount)
                self.client.bamboos[ctx.author.id] =  self.client.bal(ctx.author.id) + amount
        else:
            return

    @commands.command(aliases=['givemefreebamboo'])
    async def claim(self, ctx:Context):
        author_bal = self.client.bal(ctx.author.id)
        claimed = self.client.claimed(ctx.author.id)

        if not claimed:
            embed=discord.Embed(title='Please confirm your actions')
            embed.description = 'Are you sure you to claim **2,000** <:bamboo:911241395434565652> ?'
            embed.set_footer(text='Remember that this can be done once !')

            confirm = await ctx.confirm(embed)
            if confirm:
                await self.client.db.execute(
                    "INSERT INTO economy(user_id, amount, claimed) VALUES ($1, $2, $3) "
                    "ON CONFLICT (user_id) DO UPDATE SET amount=$2, claimed= $3",
                    ctx.author.id, author_bal + 2000, True)
                
                self.client.bamboos[ctx.author.id] = self.client.bal(ctx.author.id) + 2000
                self.client.claims[ctx.author.id] = True

                embed = discord.Embed(title="Successfuly claimed your one time", color=discord.Color.green())
                embed.description = "You've received **2,000** <:bamboo:911241395434565652>, spend it well !"
                return await ctx.send(embed=embed)
        
        else:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "You've already claimed your bonus of **2,000** <:bamboo:911241395434565652>"
            return await ctx.send(embed=embed)

    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.command()
    async def slots(self, ctx:Context, amount:int = 0):
        """Bet your bamboo on slots and multiple it by 25X times on JACKPOT !"""
        author_bal = self.client.bal(ctx.author.id)
        
        if amount < 0:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "My minimum amount of <:bamboo:911241395434565652> that you can bet is **10**"
            return await ctx.send(embed=embed)

        if  amount * 25 + author_bal> 9223372036854775807:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "My maximum amount of <:bamboo:911241395434565652> that you can have is **9,223,372,036,854,775,807**. That means that if you win this route, you will exceed this limit"
            return await ctx.send(embed=embed)

        if amount > author_bal:
            embed = discord.Embed(title="Something went wrong...", color=discord.Color.red())
            embed.description = "You can't afford to do that !"
            return await ctx.send(embed=embed)

        if amount > 0:
            embed=discord.Embed(title='Please confirm your actions')
            embed.description = 'Are you sure you want to bet **{:,}** <:bamboo:911241395434565652> ?'.format(amount)

            confirm = await ctx.confirm(embed)
            
            if not confirm:
                return

        spacer = '\u2001' * 3
        options = ['seven', 'watermelon', 'coin', 'cherries', 'gem', 'grapes', 'dollar']
        
        fruits = [f"|{spacer}:watermelon:{spacer}|",
                  f"|{spacer}:cherries:{spacer}|",
                  f"|{spacer}:grapes:{spacer}|"]

        heist = [f"|{spacer}:gem:{spacer}|",
                 f"|{spacer}:coin:{spacer}|",
                 f"|{spacer}:dollar:{spacer}|"]
        
        slots = [f"|{spacer}:{options[random.randint(0, 6)]}:{spacer}|",
                 f"|{spacer}:{options[random.randint(0, 6)]}:{spacer}|",
                 f"|{spacer}:{options[random.randint(0, 6)]}:{spacer}|"]
        
        loader = f"|{spacer}<a:wheel:912254947284881409>{spacer}|"
   
        if (slots[0] == slots[1] == slots[2]):
            color = discord.Color.fuchsia()
            if amount != 0:
                outcome = amount * 25
                await self.client.db.execute(
                                "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                                "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                                ctx.author.id, self.client.bal(ctx.author.id) + outcome)
                self.client.bamboos[ctx.author.id] =  self.client.bal(ctx.author.id) + outcome
            url = 'https://fakeimg.pl/1040x200/EB459E/000000/?retina=1&text=$$%20JACKPOT%20$$'
        
        elif len(set(slots)) != len(slots):
            color = discord.Color.green()
            if amount != 0:
                outcome = int(amount * 1.25)
                await self.client.db.execute(
                                "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                                "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                                ctx.author.id, self.client.bal(ctx.author.id) + outcome)
                self.client.bamboos[ctx.author.id] =  self.client.bal(ctx.author.id) + outcome
                url = "https://fakeimg.pl/1040x200/2ECC71/000000/?retina=1&text=You%20got%20two%20matching,%20your%20bet%20is%20multiplied%20by%201.25X%20!"
            
            else:
                url = "https://fakeimg.pl/1040x200/2ECC71/000000/?retina=1&text=You%20got%20two%20matching%20!"

        elif sorted(slots) == sorted(fruits):
            color = discord.Color.yellow()
            
            if amount != 0:
                outcome = int(amount * 5)
                await self.client.db.execute(
                                "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                                "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                                ctx.author.id, self.client.bal(ctx.author.id) + outcome)
                self.client.bamboos[ctx.author.id] =  self.client.bal(ctx.author.id) + outcome
                url = "https://fakeimg.pl/1040x200/F1C40F/000000/?retina=1&text=You%20got%20FRUIT%20COMBO,%20your%20bet%20is%20multiplied%20by%205X%20!"
            
            else:
                url = "https://fakeimg.pl/1040x200/F1C40F/000000/?retina=1&text=You%20got%20FRUIT%20COMBO%20!"

        elif sorted(slots) == sorted(heist):
            color = discord.Color.yellow()
            
            if amount != 0:
                outcome = int(amount * 5)
                await self.client.db.execute(
                                "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                                "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                                ctx.author.id, self.client.bal(ctx.author.id) + outcome)
                self.client.bamboos[ctx.author.id] =  self.client.bal(ctx.author.id) + outcome 
                url = "https://fakeimg.pl/1040x200/F1C40F/000000/?retina=1&text=You%20got%20HEIST%20COMBO,%20your%20bet%20is%20multiplied%20by%205X%20!"
            
            else:
                url = "https://fakeimg.pl/1040x200/F1C40F/000000/?retina=1&text=You%20got%20HEIST%20COMBO%20!"

        else:
            color = discord.Color.red()
            
            if amount != 0:
                outcome = amount * -1
                await self.client.db.execute(
                                "INSERT INTO economy(user_id, amount) VALUES ($1, $2) "
                                "ON CONFLICT (user_id) DO UPDATE SET amount= $2",
                                ctx.author.id, self.client.bal(ctx.author.id) + outcome)
                self.client.bamboos[ctx.author.id] =  self.client.bal(ctx.author.id) + outcome
            
            url = 'https://fakeimg.pl/1040x200/E74C3C/000000/?retina=1&text=Unfortunately%20you%20had%20no%20luck%20this%20time'
        
        embed = discord.Embed()
        embed.set_author(name='Slot Machine', icon_url='https://i.imgur.com/8oGuoyq.png')
        
        embed.add_field(name=loader, value='\u200b')
        embed.add_field(name=loader, value='\u200b')
        embed.add_field(name=loader, value='\u200b')
        
        message = await ctx.send(embed=embed)

        for i in range(0, 3):
            await asyncio.sleep(0.8)
            embed.set_field_at(i, name=slots[i], value='\u200b')
            await message.edit(embed=embed)

        embed.color = color
        embed.set_image(url=url)
        if amount != 0:
            embed.add_field(name='Your bet', value="**{:,}** <:bamboo:911241395434565652>".format(amount))
            embed.add_field(name='Your outcome', value="**{:,}** <:bamboo:911241395434565652>".format(outcome))
            embed.add_field(name='Your balance', value="**{:,}** <:bamboo:911241395434565652>".format(self.client.bal(ctx.author.id)))
        
        await message.edit(embed=embed)
        

def setup(client):
    client.add_cog(Economy(client))
