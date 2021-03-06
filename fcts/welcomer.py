import discord, datetime
from discord.ext import commands
from classes import zbot

class Welcomer(commands.Cog):
    """Cog which manages the departure and arrival of members in the servers"""
    
    def __init__(self, bot: zbot):
        self.bot = bot
        self.file = "welcomer"
        self.no_message = [392766377078816789,504269440872087564,552273019020771358]

    
    @commands.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        """Main function called when a member joins a server"""
        if self.bot.database_online:
            await self.bot.cogs["Servers"].update_memberChannel(member.guild)
            if "MEMBER_VERIFICATION_GATE_ENABLED" not in member.guild.features:
                await self.send_msg(member,"welcome")
                self.bot.loop.create_task(self.give_roles(member))
                await self.give_roles_back(member)
                await self.check_muted(member)
                if member.guild.id==356067272730607628:
                    await self.check_owner_server(member)
                    await self.check_support(member)
                    await self.check_contributor(member)
    
    @commands.Cog.listener()
    async def on_member_update(self, before:discord.Member, after:discord.Member):
        """Main function called when a member got verified in a community server"""
        if before.pending and not after.pending:
            if "MEMBER_VERIFICATION_GATE_ENABLED" in after.guild.features:
                await self.send_msg(after,"welcome")
                self.bot.loop.create_task(self.give_roles(after))
                await self.give_roles_back(after)
                await self.check_muted(after)
        
        
    @commands.Cog.listener()
    async def on_member_remove(self, member:discord.Member):
        """Fonction principale appelée lorsqu'un membre quitte un serveur"""
        if self.bot.database_online:
            await self.bot.cogs["Servers"].update_memberChannel(member.guild)
            await self.send_msg(member,"leave")
            await self.bot.cogs['Events'].check_user_left(member)


    async def send_msg(self, member:discord.Member, Type:str):
        """Envoie un message de bienvenue/départ dans le serveur"""
        if self.bot.zombie_mode:
            return
        msg = await self.bot.get_config(member.guild.id,Type)
        if await self.raid_check(member) or member.id in self.no_message:
            return
        if await self.bot.cogs['Utilities'].check_any_link(member.name) is not None:
            return
        if msg not in ['',None]:
            ch = await self.bot.get_config(member.guild.id,'welcome_channel')
            if ch is None:
                return
            ch = ch.split(';')
            msg = await self.bot.cogs['Utilities'].clear_msg(msg,ctx=None)
            for channel in ch:
                if not channel.isnumeric():
                    continue
                channel = member.guild.get_channel(int(channel))
                if channel is None:
                    continue
                botormember = await self.bot._(member.guild,"keywords",'bot' if member.bot else 'member')
                try:
                    msg = msg.format_map(self.bot.SafeDict(
                        user=member.mention if Type=='welcome' else member.name,
                        server=member.guild.name,
                        owner=member.guild.owner.name,
                        member_count=member.guild.member_count,
                        type=botormember))
                    msg = await self.bot.cogs["Utilities"].clear_msg(msg,everyone=False)
                    await channel.send(msg)
                except Exception as e:
                    await self.bot.cogs["Errors"].on_error(e,None)

    async def check_owner_server(self, member: discord.Member):
        """Vérifie si un nouvel arrivant est un propriétaire de serveur"""
        servers = [x for x in self.bot.guilds if x.owner == member and x.member_count > 10]
        if len(servers) > 0:
            role = member.guild.get_role(486905171738361876)
            if role is None:
                self.bot.log.warn('[check_owner_server] Owner role not found')
                return
            if role not in member.roles:
                await member.add_roles(role,reason="This user support me")

    async def check_support(self, member: discord.Member):
        """Vérifie si un nouvel arrivant fait partie du support"""
        if await self.bot.get_cog('Users').has_userflag(member, 'support'):
            role = member.guild.get_role(412340503229497361)
            if role is not None:
                await member.add_roles(role)
            else:
                self.bot.log.warn('[check_support] Support role not found')

    async def check_contributor(self, member: discord.Member):
        """Vérifie si un nouvel arrivant est un contributeur"""
        if await self.bot.get_cog('Users').has_userflag(member, 'contributor'):
            role = member.guild.get_role(552428810562437126)
            if role is not None:
                await member.add_roles(role)
            else:
                self.bot.log.warn('[check_contributor] Contributor role not found')

    async def give_roles_back(self, member: discord.Member):
        """Give roles rewards/muted role to new users"""
        used_xp_type = await self.bot.get_config(member.guild.id,'xp_type')
        xp = await self.bot.cogs['Xp'].bdd_get_xp(member.id, None if used_xp_type == 0 else member.guild.id)
        if xp is not None and len(xp) == 1:
            await self.bot.cogs['Xp'].give_rr(member,(await self.bot.cogs['Xp'].calc_level(xp[0]['xp'],used_xp_type))[0],await self.bot.cogs['Xp'].rr_list_role(member.guild.id))
    
    async def check_muted(self, member: discord.Member):
        """Give the muted role to that user if needed"""
        modCog = self.bot.get_cog("Moderation")
        if not modCog or not self.bot.database_online:
            return
        if await modCog.is_muted(member.guild.id, member.id):
            role = await modCog.get_muted_role(member.guild)
            if role:
                try:
                    await member.add_roles(role)
                except discord.Forbidden:
                    pass


    async def kick(self, member: discord.Member, reason: str):
        try:
            await member.guild.kick(member, reason=reason)
        except:
            pass
    
    async def ban(self, member: discord.Member, reason: str):
        try:
            await member.guild.ban(member, reason=reason)
        except:
            pass

    async def raid_check(self, member: discord.Member):
        if member.guild is None:
            return False
        level = str(await self.bot.get_config(member.guild.id,"anti_raid"))
        if not level.isnumeric() or member.guild.channels[0].permissions_for(member.guild.me).kick_members == False:
            return
        c = False
        level = int(level)
        can_ban = member.guild.get_member(self.bot.user.id).guild_permissions.ban_members
        if level == 0:
            return c
        if level >= 1:
            if await self.bot.cogs['Utilities'].check_discord_invite(member.name) is not None:
                await self.kick(member,await self.bot._(member.guild.id,"logs","d-invite"))
                c = True
        if level >= 2:
            if (datetime.datetime.utcnow() - member.created_at).seconds <= 5*60:
                await self.kick(member,await self.bot._(member.guild.id,"logs","d-young"))
                c = True
        if level >= 3 and can_ban:
            if await self.bot.cogs['Utilities'].check_discord_invite(member.name) is not None:
                await self.ban(member,await self.bot._(member.guild.id,"logs","d-invite"))
                c = True
            if (datetime.datetime.utcnow() - member.created_at).seconds <= 30*60:
                await self.kick(member,await self.bot._(member.guild.id,"logs","d-young"))
                c = True
        if level >= 4:
            if (datetime.datetime.utcnow() - member.created_at).seconds <= 30*60:
                await self.kick(member,await self.bot._(member.guild.id,"logs","d-young"))
                c = True
            if (datetime.datetime.utcnow() - member.created_at).seconds <= 120*60 and can_ban:
                await self.ban(member,await self.bot._(member.guild.id,"logs","d-young"))
                c = True
        return c


    async def give_roles(self, member: discord.Member):
        """Give new roles to new users"""
        try:
            roles = str(await self.bot.get_config(member.guild.id,"welcome_roles"))
            for r in roles.split(";"):
                if (not r.isnumeric()) or len(r) == 0:
                    continue
                role = member.guild.get_role(int(r))
                if role is not None:
                    try:
                        await member.add_roles(role,reason=await self.bot._(member.guild.id,"logs","d-welcome_roles"))
                    except discord.errors.Forbidden:
                        await self.bot.cogs['Events'].send_logs_per_server(member.guild,'error',await self.bot._(member.guild,'bvn','error-give-roles',r=role.name,u=str(member)), member.guild.me)
        except discord.errors.NotFound:
            pass
        except Exception as e:
            await self.bot.cogs["Errors"].on_error(e,None)


def setup(bot):
    bot.add_cog(Welcomer(bot))