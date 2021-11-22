import discord
from discord.ext import commands
    
__all__ = (
    'NoPlayer',
    'FullVoiceChannel',
    'NotAuthorized',
    'IncorrectChannelError',
    'IncorrectTextChannelError',
    'AlreadyConnectedToChannel',
    'NoVoiceChannel',
    'QueueIsEmpty',
    'NoCurrentTrack',
    'NoConnection',
    'PlayerIsAlreadyPaused',
    'PlayerIsNotPaused',
    'NoMoreTracks',
    'InvalidTimeString',
    'NoPerms',
    'AfkChannel',
    'InvalidTrack',
    'InvalidPosition',
    'InvalidVolume',
    'AlreadyVoted',
    'NothingToShuffle',
    'NoLyrics',
    'LoadFailed',
    'NoMatches',
    'InvalidSeek',
    'InvalidInput',
    'LoopDisabled',
    'TrackFailed'

)
class errors(commands.CommandError):
    def __init__(self, e) -> None:
        self.custom = True
        self.embed = discord.Embed(title='Something went wrong...',
                                   description = e,
                                   color = discord.Color.red())
        super().__init__(e)

class NoPlayer(errors):
    def __init__(self) -> None:
        super().__init__(f'There isn\'t an active player in your server.')

class FullVoiceChannel(errors):
    def __init__(self, ctx : commands.Context) -> None:
        super().__init__(f'I can\'t join {ctx.author.voice.channel.mention}, because it\'s full.')

class NotAuthorized(errors):
    def __init__(self) -> None:
        super().__init__("You cannot perform this action.")

class IncorrectChannelError(errors):
    def __init__(self, ctx : commands.Context) -> None:
        player = ctx.voice_client
        super().__init__(f'{ctx.author.mention}, you must be in {player.channel.mention} for this session.')
        
class IncorrectTextChannelError(errors):
    def __init__(self, ctx : commands.Context) -> None:
        player = ctx.voice_client
        super().__init__(f'{ctx.author.mention}, you can only use commands in {player.text_channel.mention} for this session.')

class AlreadyConnectedToChannel(errors):
    def __init__(self, ctx : commands.Context) -> None:
        player = ctx.voice_client
        super().__init__(f"Already connected to {player.channel.mention}")

class NoVoiceChannel(errors):
    def __init__(self) -> None:
        super().__init__("I'm not connected to any voice channels.")

class QueueIsEmpty(errors):
    def __init__(self) -> None:
        super().__init__("There are no tracks in the queue.")

class NoCurrentTrack(errors):
    def __init__(self) -> None:
        super().__init__("There is no track currently playing.")

class PlayerIsAlreadyPaused(errors):
    def __init__(self) -> None:
        super().__init__("The current track is already paused.")

class PlayerIsNotPaused(errors):
    def __init__(self) -> None:
        super().__init__("The current track is not paused.")

class NoMoreTracks(errors):
    def __init__(self) -> None:
        super().__init__("There are no more tracks in the queue.")

class InvalidTimeString(errors):
    def __init__(self) -> None:
        super().__init__("The Time String Given is an Invalid one.")

class NoPerms(errors):
    def __init__(self, perms, channel) -> None:
        super().__init__(f"I don't have permissions to `{perms}` in {channel.mention}")

class NoConnection(errors):
    def __init__(self) -> None:
        super().__init__("You must be connected to a voice channel to use voice commands.")

class AfkChannel(errors):
    def __init__(self) -> None:
        super().__init__("I can't play music in the afk channel.")

class NotAuthorized(errors):
    def __init__(self) -> None:
        super().__init__("You cannot perform this action.")

class InvalidTrack(errors):
    def __init__(self) -> None:
        super().__init__("Can't perform action on track that is out of the queue.")

class InvalidPosition(errors):
    def __init__(self) -> None:
        super().__init__("Can't perform action with invalid position in the queue.")

class InvalidVolume(errors):
    def __init__(self) -> None:
        super().__init__('Please enter a value between 1 and 125.')

class InvalidSeek(errors):
    def __init__(self) -> None:
        super().__init__('You can\'t seek with timestamps that are shorter/longer than the track\'s length')

class AlreadyVoted(errors):
    def __init__(self) -> None:
        super().__init__('You\'ve already voted.')

class NothingToShuffle(errors):
    def __init__(self) -> None:
        super().__init__('There is nothing to shuffle.')

class NoLyrics(errors):
    def __init__(self) -> None:
        super().__init__('No lyrics found')

class ActiveVote(errors):
    def __init__(self) -> None:
        super().__init__('There is already an active vote.')

class LoadFailed(errors):
    def __init__(self) -> None:
        super().__init__('Failed loading your query.')

class NoMatches(errors):
    def __init__(self) -> None:
        super().__init__('No songs were found with that query, please try again.')

class InvalidInput(errors):
    def __init__(self) -> None:
        super().__init__('Invalid input has been detected')

class LoopDisabled(errors):
    def __init__(self) -> None:
        super().__init__('Loop mode is already `DISABLED`')

class TrackFailed(errors):
    def __init__(self, track) -> None:
        super().__init__('There was an error playing {}, skipping to next track.'.format(track.title))


