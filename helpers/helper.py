import discord

from discord import VoiceRegion
import helpers.consts as consts

class Url(discord.ui.View):
    def __init__(self, url: str, label: str = 'Open', emoji: str = None):
        super().__init__()
        self.add_item(discord.ui.Button(label=label, emoji=emoji, url=url))

def get_staff_perms(permissions):
    perms = []
    
    if permissions.administrator:
        perms.append("Administrator")
        return ["Administrator"]
    if permissions.manage_guild:
        perms.append("Manage guild")
    if permissions.ban_members:
        perms.append("Ban members")
    if permissions.kick_members:
        perms.append("Kick members")
    if permissions.manage_channels:
        perms.append("Manage channels")
    if permissions.manage_emojis:
        perms.append("Manage custom emotes")
    if permissions.manage_messages:
        perms.append("Manage messages")
    if permissions.manage_permissions:
        perms.append("Manage permissions")
    if permissions.manage_roles:
        perms.append("Manage roles")
    if permissions.mention_everyone:
        perms.append("Mention everyone")
    if permissions.manage_emojis:
        perms.append("Manage emojis")
    if permissions.manage_webhooks:
        perms.append("Manage webhooks")
    if permissions.move_members:
        perms.append("Move members")
    if permissions.mute_members:
        perms.append("Mute members")
    if permissions.deafen_members:
        perms.append("Deafen members")
    if permissions.priority_speaker:
        perms.append("Priority speaker")
    if permissions.view_audit_log:
        perms.append("See audit log")
    if permissions.create_instant_invite:
        perms.append("Create instant invites")
    if len(perms) == 0:
        return None
    return perms

def get_perms(member:discord.Member):
    permissions = [permission for permission in member.guild_permissions]
    perms = []

    for name, value in permissions:
        if value:
            name = name.replace("_", " ").replace("guild", "server").title()
            perms.append(name)
    
    if 'Administrator' in perms:
        perms = ['Administrator']

    if len(perms) == 0:
        perms = ["None"]

    return perms

def convert_bytes(size):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0
    return size

def get_user_badges(member:discord.Member, user:discord.User):
    flags = dict(member.public_flags)
    user_flags = []

    for feature, label in consts.USER_FLAGS.items():
        try:
            if flags[feature]:
                user_flags.append(label)
        except KeyError:
            continue

    if member.display_avatar.is_animated() or\
        user.banner or\
        member.premium_since or\
        member.guild_avatar:
        
        user_flags.append('<:nitro:314068430611415041>')
    
    if member.premium_since:
        user_flags.append('<:booster:895429394376572928>')

    if member.bot:
        user_flags.append('<:DiscordBot:904026286073212978>')

    return user_flags

def get_user_statuses(member: discord.Member):
    mobile = {
        discord.Status.online: consts.statuses.ONLINE_MOBILE,
        discord.Status.idle: consts.statuses.IDLE_MOBILE,
        discord.Status.dnd: consts.statuses.DND_MOBILE,
        discord.Status.offline: consts.statuses.OFFLINE_MOBILE
    }[member.mobile_status]
    web = {
        discord.Status.online: consts.statuses.ONLINE_WEB,
        discord.Status.idle: consts.statuses.IDLE_WEB,
        discord.Status.dnd: consts.statuses.DND_WEB,
        discord.Status.offline: consts.statuses.OFFLINE_WEB
    }[member.web_status]
    desktop = {
        discord.Status.online: consts.statuses.ONLINE,
        discord.Status.idle: consts.statuses.IDLE,
        discord.Status.dnd: consts.statuses.DND,
        discord.Status.offline: consts.statuses.OFFLINE
    }[member.desktop_status]
    
    return f"\u200b{desktop}\u200b{web}\u200b{mobile}"

def get_server_region_emote(server: discord.Guild):
    region = server.region

    if region == VoiceRegion.amsterdam:
        return "🇳🇱"
    if region == VoiceRegion.brazil:
        return "🇧🇷"
    if region == VoiceRegion.dubai:
        return "🇦🇪"
    if region == VoiceRegion.eu_central:
        return "🇪🇺"
    if region == VoiceRegion.eu_west:
        return "🇪🇺"
    if region == VoiceRegion.europe:
        return "🇪🇺"
    if region == VoiceRegion.frankfurt:
        return "🇩🇪"
    if region == VoiceRegion.hongkong:
        return "🇭🇰"
    if region == VoiceRegion.india:
        return "🇮🇳"
    if region == VoiceRegion.japan:
        return "🇯🇵"
    if region == VoiceRegion.london:
        return "🇬🇧"
    if region == VoiceRegion.russia:
        return "🇷🇺"
    if region == VoiceRegion.singapore:
        return "🇸🇬"
    if region == VoiceRegion.southafrica:
        return "🇿🇦"
    if region == VoiceRegion.south_korea:
        return "🇰🇷"
    if region == VoiceRegion.sydney:
        return "🇦🇺"
    if region == VoiceRegion.us_central:
        return "🇺🇸"
    if region == VoiceRegion.us_east:
        return "🇺🇸"
    if region == VoiceRegion.us_south:
        return "🇺🇸"
    if region == VoiceRegion.us_west:
        return "🇺🇸"
    if region == VoiceRegion.vip_amsterdam:
        return "🇳🇱🌟"
    if region == VoiceRegion.vip_us_east:
        return "🇺🇸🌟"
    if region == VoiceRegion.vip_us_west:
        return "🇺🇸🌟"
    else:
        return "<:tickNo:885222934036226068>"

def get_server_region(server : discord.Guild):
    region = server.region

    if region == VoiceRegion.amsterdam:
        return "Amsterdam"
    if region == VoiceRegion.brazil:
        return "Brazil"
    if region == VoiceRegion.dubai:
        return "Dubai"
    if region == VoiceRegion.eu_central:
        return "EU central"
    if region == VoiceRegion.eu_west:
        return "EU west"
    if region == VoiceRegion.europe:
        return "Europe"
    if region == VoiceRegion.frankfurt:
        return "Frankfurt"
    if region == VoiceRegion.hongkong:
        return "Hong Kong"
    if region == VoiceRegion.india:
        return "India"
    if region == VoiceRegion.japan:
        return "Japan"
    if region == VoiceRegion.london:
        return "London"
    if region == VoiceRegion.russia:
        return "Russia"
    if region == VoiceRegion.singapore:
        return "Singapore"
    if region == VoiceRegion.southafrica:
        return "South Africa"
    if region == VoiceRegion.south_korea:
        return "South Korea"
    if region == VoiceRegion.sydney:
        return "Sydney"
    if region == VoiceRegion.us_central:
        return "US Central"
    if region == VoiceRegion.us_east:
        return "US East"
    if region == VoiceRegion.us_south:
        return "US South"
    if region == VoiceRegion.us_west:
        return "US West"
    if region == VoiceRegion.vip_amsterdam:
        return "VIP Amsterdam"
    if region == VoiceRegion.vip_us_east:
        return "VIP US East"
    if region == VoiceRegion.vip_us_west:
        return "VIP US West"
    else:
        return "Unknown region"

