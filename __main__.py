import discord, os
from discord.ext.voice_recv.voice_client import VoiceRecvClient

import openwakeword
from oww_sink import AsyncOpenWakeWordSink
from handlers import VoiceActivatedSoundboard, VoiceActivatedAudio, VoiceActivatedIncessantAudio, ManyVoiceActivated

AW_SOUNDBOARD_ID = 1363476761576210616
SMOKE_CHIRP_AUDIO = "./audio/smokechirp.mp3"
CARS_ON_FIRE_AUDIO = "./audio/cars_on_fire.mp3"

HIT_THE_AW_BUTTON = "hit_the_aw_button"
OI_FUCKWHIT = "oi_fuckwhit_v1"
CARS_ON_FIRE = "cars_on_fire"

# MCRIB, APOLGIZE

intents = discord.Intents()
intents.voice_states = True
intents.guilds = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

openwakeword.utils.download_models(model_names=["melspectrogram"])

@client.event
async def on_ready():
    await tree.sync()
    print(f"We have logged in as '{client.user}'")

@tree.command(name="join", description="Join your voice channel.")
async def join(interaction: discord.Interaction):
    if interaction.user.voice is None:
        return await interaction.response.send_message("You are not in a voice channel!", ephemeral=True)
    if interaction.user.voice.channel is None:
        return await interaction.response.send_message("Failed to join voice channel, I may not have the required permissions.", ephemeral=True)

    channel = interaction.user.voice.channel;
    try:
        voice_client = await channel.connect(cls=VoiceRecvClient)
    except Exception as e:
        return await interaction.response.send_message(f"{e}")

    handler = ManyVoiceActivated([
        VoiceActivatedSoundboard(HIT_THE_AW_BUTTON, interaction, AW_SOUNDBOARD_ID),
        VoiceActivatedAudio(CARS_ON_FIRE, voice_client, CARS_ON_FIRE_AUDIO),
        VoiceActivatedIncessantAudio(OI_FUCKWHIT, CARS_ON_FIRE, voice_client, SMOKE_CHIRP_AUDIO),
    ])
    
    async def handle_predictions(user: discord.User, predictions: dict):
        if any(score > 0.1 for score in predictions.values()):
            print(f"Possible wake word detected from {user.name}: {predictions}")

        await handler.handle(user, predictions)

    sink = AsyncOpenWakeWordSink(
        wakeword_models=[f"./models/{model}.tflite" for model in handler.get_models()],
        async_pred_cb=handle_predictions
    )
    voice_client.listen(sink)
    
    await interaction.response.send_message(f"Joined {channel.name}!")

@tree.command(name="leave", description="Leave the current voice channel.")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client is None:
        return await interaction.response.send_message("I am not in a voice channel!", ephemeral=True)
    
    channel = interaction.guild.voice_client.channel
    await interaction.guild.voice_client.disconnect()
    await interaction.response.send_message(f"Left {channel.name}.")

@tree.command(name="wtfisthis", description="Explains wtf this bot is.")
async def wtfisthis(interaction: discord.Interaction):
    return await interaction.response.send_message("Haha, definitely not government spyware :)\n\n- Go in voice chat\n- Run the `/join` command\n- Say \"hit the awww button\"\nand the bot will play the 'awww' soundboard.\n\nIt uses speech recognition stuff, it's pretty shit so you'll probably have to say it a few times... and also say it in a british accent that helps for some reason sorry not sorry.")

@tree.command(name="reload", description="Reload the bot. For developers.")
async def reload(interaction: discord.Interaction):
    await tree.sync(guild=interaction.guild)
    await interaction.response.send_message(f"Reloaded!")

token = os.getenv('TOKEN')
if token:
    client.run(token)
else:
    print("Missing environment variable 'TOKEN'")