import discord
import yt_dlp
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord import app_commands
import os

testServerID = 893822110185689149

class play_control(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.client.loop.create_task(self.sync_commands())

    async def sync_commands(self):
        print("Music.cogs loaded and ready")
        await self.client.tree.sync(guild=discord.Object(id=testServerID))

    queues = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def add_to_queue(self, guild_id, source):
        queue = self.get_queue(guild_id)
        queue.append(source)

    def remove_from_queue(self, guild_id):
        queue = self.get_queue(guild_id)
        if queue:
            return queue.pop(0)
        return None

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'song/%(title)s.%(ext)s',
    }

    def download_audio(self, url):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            song_name = info_dict.get('title', 'Unknown Song')
            song_path = os.path.join('song', song_name + '.mp3')
            # Check if the file already exists
            if os.path.exists(song_path):
                print(f"The audio file '{song_path}' already exists.")
                return song_name
            #download the song
            print(f"Downloading: {song_name}")
            os.makedirs('song', exist_ok=True)
            ydl.download([url])
            return song_name

    async def play_next(self, interaction):
        guild_id = interaction.guild.id
        voice = interaction.guild.voice_client
        queues = self.get_queue(guild_id)

        # Remove the finished song from the queue
        self.remove_from_queue(guild_id)
        # check if the queue is empty
        if not queues:
            await interaction.response.send_message("Queue is empty. Leaving voice channel.")
            await voice.disconnect()
            return
        if interaction.guild.id in self.queues:
            song_name = queues[0]
            song_path = os.path.join('song', song_name + '.mp3')
            source = FFmpegPCMAudio(song_path)
            voice.play(source, after=lambda x: self.client.loop.create_task(self.play_next(interaction)))
            await interaction.response.send_message(f"Now playing: {song_name}")

        else:
            await interaction.response.send_message("Queue is empty. Leaving voice channel.")
            await voice.disconnect()

    @app_commands.command(name="join", description="Join the voice channel")
    async def join(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if interaction.user.voice is None:
            await interaction.followup.send(f"{interaction.user.name} are not in channel, please join a channel first.")
        else:
            channel = interaction.user.voice.channel
            voice = await channel.connect()
            await interaction.followup.send(f"Joined {channel}")
            # source = FFmpegPCMAudio('Haynoidi.mp3')
            # player = voice.play(source)

    @app_commands.command(name="leave", description="Leave the voice channel")
    async def leave(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if(interaction.voice_client):
            await interaction.guild.voice_client.disconnect()
            await interaction.followup.send("I left the voice channel.")
        else:
            await interaction.followup.send("I'm not in a voice channel.")

    @app_commands.command(name="pause", description="Pause playing music")
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer()

        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice and voice.is_playing():
            voice.pause()
            await interaction.followup.send("Music paused.")
        else:
            await interaction.followup.send("No audio is playing at the moment.")

    @app_commands.command(name="resume", description="Resume playing music")
    async def resume(self, interaction: discord.Interaction):
        await interaction.response.defer()

        voice = discord.utils.get(self.client.voice_clients, guild = interaction.guild)
        if voice.is_paused():
            voice.resume()
            await interaction.followup.send("Music resumed.")
        else:
            await interaction.followup.send("No audio is paused at the moment.")

    @app_commands.command(name="stop", description="Stop playing music")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        voice = discord.utils.get(self.client.voice_clients, guild = interaction.guild)
        if voice and voice.is_playing():
            voice.stop()
        if interaction.guild.id in self.queues:
            self.queues[interaction.guild.id] = []
            await interaction.followup.send("Queue cleared.")
            await interaction.followup.send("Music stopped.")
        else:
            await interaction.followup.send("No audio is playing or paused at the moment.")

    
    @app_commands.command(name="play", description="PLay a song")
    async def play(self, interaction: discord.Interaction, song_url: str):
        await interaction.response.defer()

        #check if bot is in voice channel and join if not
        voice = interaction.guild.voice_client
        if voice is None:
            if interaction.user.voice is None:
                await interaction.followup.send(f"{interaction.user.name} are not in channel, please join a channel first.")
                return
            else:

                channel = interaction.user.voice.channel
                voice = await channel.connect()
        #play music
        voice_channel = interaction.user.voice.channel
        if not song_url.startswith("https://"):
            #handle local file
            voice = interaction.guild.voice_client
            source = FFmpegPCMAudio(song_url + '.mp3')
            voice.play(source, after=lambda x: self.client.loop.create_task(self.play_next(interaction)))
            await interaction.followup.send('**Now playing:** {}'.format(song_url))
        else:
            #handle youtube url
            song_name = self.download_audio(song_url)
            # Get the full file path for the song in the 'song' folder
            song_path = os.path.join('song', song_name + '.mp3')
            voice = interaction.guild.voice_client
            try:
                source = FFmpegPCMAudio(song_path)
                voice.play(source, after=lambda x: self.client.loop.create_task(self.play_next(interaction)))
                self.add_to_queue(interaction.guild.id, song_name)
                await interaction.followup.send('**Now playing:** {}'.format(song_name))
            except Exception as e:
                await interaction.response.send_message(f"An error occurred while playing the audio: {e}")
    
    @app_commands.command(name="queue", description="Add a song to the queue")
    async def queue(self, interaction: discord.Interaction, song_url: str):
        # Defer the interaction response
        await interaction.response.defer()
        song_name = self.download_audio(song_url)
        self.add_to_queue(interaction.guild.id, song_name)
        # Send a follow-up message
        await interaction.followup.send(f'Added to queue {song_name}')

    
async def setup(client):
    await client.add_cog(play_control(client),
                         guilds= [discord.Object(id=testServerID)])
