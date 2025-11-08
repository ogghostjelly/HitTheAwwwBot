import random
from typing import List
import discord, datetime

## Handles an OWW voice prediction.
class PredictionHandler:
    async def handle(self, user: discord.User, predictions: dict):
        print("Unimplemented: handle")
    
    def get_models(self) -> List[str]:
        print("Unimplemented: get_models")

## Handles an OWW voice prediction with debounce prevention.
## Calls `activate` when the phrase is detected, subclasses should override this method.
class VoiceActivated(PredictionHandler):
    def __init__(self, model: str) -> None:
        self.last_time = datetime.datetime.min
        self.model = model

        self.cooldown_secs = 1.0
        self.min_score = 0.5
    
    def get_models(self) -> List[str]:
        return [self.model]

    async def handle(self, user: discord.User, predictions: dict):
        current_time = datetime.datetime.now()
        delta = current_time - self.last_time

        if predictions[self.model] > self.min_score and delta.total_seconds() > self.cooldown_secs:
            print(f"Wake word detected from {user.name}: '{self.model}': {predictions[self.model]}")
            self.last_time = current_time
            await self.activate(user)
    
    async def activate(self, user: discord.User):
        print("unimplemented: activate")

## Fires a callback on voice activation.
class VoiceActivatedCallback(VoiceActivated):
    def __init__(self, model: str, cb) -> None:
        super().__init__(model)
        self.cb = cb
    
    async def activate(self, user: discord.User):
        self.cb(user)

## Plays a soundboard on voice activation.
class VoiceActivatedSoundboard(VoiceActivated):
    def __init__(self, model: str, interaction: discord.Interaction, soundboard_id: int) -> None:
        super().__init__(model)
        self.channel = interaction.user.voice.channel
        self.soundboard = interaction.guild.get_soundboard_sound(soundboard_id)

    async def activate(self, user: discord.User):
        await self.channel.send_sound(self.soundboard)

## Plays audio on voice activation.
class VoiceActivatedAudio(VoiceActivated):
    def __init__(self, model: str, voice_client: discord.VoiceClient, audio_path: str) -> None:
        super().__init__(model)
        self.voice_client = voice_client
        self.audio_path = audio_path
    
    async def activate(self, user: discord.User):
        self.voice_client.play(discord.FFmpegPCMAudio(self.audio_path))

class ManyVoiceActivated(PredictionHandler):
    def __init__(self, handlers: List[PredictionHandler]) -> None:
        super().__init__()
        self.handlers = handlers
    
    async def handle(self, user: discord.User, predictions: dict):
        for handler in self.handlers:
            await handler.handle(user, predictions)

    def get_models(self) -> List[str]:
        handlers = []
        for handler in self.handlers:
            handlers.extend(handler.get_models())
        return handlers

## Turns the `is_enabled` flag on or off depending on the phrase.
class VoiceActivatedSwitch(PredictionHandler):
    def __init__(self, on_model: str, off_model: str) -> None:
        super().__init__()
        self.is_enabled = False
        self.on_model = VoiceActivatedCallback(on_model, lambda user: self.on())
        self.off_model = VoiceActivatedCallback(off_model, lambda user: self.off())
    
    def get_models(self) -> List[str]:
        return [*self.on_model.get_models(), *self.off_model.get_models()]

    def on(self):
        self.is_enabled = True
    def off(self):
        self.is_enabled = False

    async def handle(self, user: discord.User, predictions: dict):
        await self.on_model.handle(user, predictions)
        await self.off_model.handle(user, predictions)

class VoiceActivatedIncessantAudio(VoiceActivatedSwitch):
    def __init__(self, on_model: str, off_model: str, voice_client: discord.VoiceClient, audio_path: str) -> None:
        super().__init__(on_model, off_model)
        self.voice_client = voice_client
        self.audio_path = audio_path
    
    async def handle(self, user: discord.User, predictions: dict):
        if self.is_enabled and random.random() < 0.001:
            self.voice_client.play(discord.FFmpegPCMAudio(self.audio_path))

        return await super().handle(user, predictions)