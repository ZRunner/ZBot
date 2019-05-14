import discord, importlib, typing, datetime
from discord.ext import commands

from fcts import args
importlib.reload(args)

class UsersCog(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.file = 'users'
        self.table = 'timed'
        try:
            self.translate = bot.cogs['LangCog'].tr
        except:
            pass

    @commands.Cog.listener()
    async def on_ready(self):
        self.translate = self.bot.cogs['LangCog'].tr

    @commands.group(name='profile')
    async def profile_main(self,ctx):
        """Get and change info about yourself"""
        pass
    
    @profile_main.command(name='card')
    async def profile_card(self,ctx,style:typing.Optional[args.cardStyle]=None):
        """Change your xp card style"""
        if style==None and len(ctx.view.buffer.split(' '))>2:
            return await ctx.send(str(await self.translate(ctx.channel,'users','invalid-card')).format(', '.join(await ctx.bot.cogs['UtilitiesCog'].allowed_card_styles(ctx.author))))
        elif style==None:
            if ctx.channel.permissions_for(ctx.me).attach_files:
                style = await self.bot.cogs['UtilitiesCog'].get_xp_style(ctx.author)
                txts = [await self.translate(ctx.channel,'xp','card-level'), await self.translate(ctx.channel,'xp','card-rank')]
                desc = await self.translate(ctx.channel,'users','card-desc')
                await ctx.send(desc,file=await self.bot.cogs['XPCog'].create_card(ctx.author,style,25,[1,0],txts,force_static=True))
            else:
                await ctx.send(await self.translate(ctx.channel,'users','missing-attach-files'))
        else:
            if await ctx.bot.cogs['UtilitiesCog'].change_db_userinfo(ctx.author.id,'xp_style',style):
                if style=='rainbow' and datetime.datetime.today().day==1:
                    await ctx.bot.cogs['UtilitiesCog'].change_db_userinfo(ctx.author.id,'unlocked_rainbow',True)
                await ctx.send(str(await self.translate(ctx.channel,'users','changed-0')).format(style))
            else:
                await ctx.send(await self.translate(ctx.channel,'users','changed-1'))



def setup(bot):
    bot.add_cog(UsersCog(bot))