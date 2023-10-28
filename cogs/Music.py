import discord
from pytube import YouTube
from moviepy.editor import AudioFileClip
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord import app_commands
import os
import random

testServerID = 893822110185689149

class play_control(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.client.loop.create_task(self.sync_commands())

    async def sync_commands(self):
        print("Music.cogs loaded and ready")
        await self.client.tree.sync()

    queues = {}
    loop_flag = False
    loop_playlist_flag = False
    loop_random_flag = False

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def add_to_queue(self, guild_id, song_name):
        queue = self.get_queue(guild_id)
        queue.append(song_name)

    def remove_from_queue(self, guild_id):
        queue = self.get_queue(guild_id)
        if queue:
            return queue.pop(0)
        return None

    def add_to_queue_start(self, guild_id, song_name):
        queue = self.get_queue(guild_id)
        queue.insert(0, song_name)

    def remove_list_from_url(self, url):
        # Find the index of "&list" in the url
        index = url.find("&list")

        # If "&list" is found, return the part of the url before "&list"
        if index != -1:
            return url[:index]

        # If "&list" is not found, return the original url
        return url
    def download_audio(self, youtube_url):
        # Create a YouTube object
        yt = YouTube(youtube_url)

        # Get the title of the video
        title = yt.title

        # Get the highest quality audio stream
        audio_stream = yt.streams.get_audio_only()

        # Get the directory of the main.py script
        main_script_dir = "C:\\Users\\Windows\\PycharmProjects\\youtubeBot"

        # Create the output path
        output_path = os.path.join(main_script_dir, 'song')

        # Check if the directory exists
        if not os.path.exists(output_path):
            # If not, create it
            os.makedirs(output_path)

        # Check if a file with the same title already exists
        mp3_filename = os.path.join(output_path, f'{title}.mp3')
        if os.path.exists(mp3_filename):
            print(f'A file with the title {title} already exists.')
            return title

        # Download the audio stream
        filename = audio_stream.download(output_path=output_path)

        # Convert mp4 audio to mp3
        audioclip = AudioFileClip(filename)
        audioclip.write_audiofile(mp3_filename)

        # Delete the original .mp4 file
        os.remove(filename)

        return title

    def toggle_loop(self):
        
        if False == self.loop_flag:
            self.loop_flag = True
            self.loop_playlist_flag = False
            self.loop_random_flag = False
            print("Looping is turned on.")
            return True
        else:
            self.loop_flag = False
            print("Looping is turned off.")
        return False

    def toggle_loop_playlist(self):
        if False == self.loop_playlist_flag:
            self.loop_playlist_flag = True
            self.loop_flag = False
            self.loop_random_flag = False
            print("Looping playlist is turned on.")
            return True
        else:
            self.loop_playlist_flag = False
            print("Looping playlist is turned off.")
        return False
    
    def toggle_loop_random(self):
        if False == self.loop_random_flag:
            self.loop_random_flag = True
            self.loop_playlist_flag = False
            self.loop_flag = False
            print("Looping random is turned on.")
            return True
        else:
            self.loop_random_flag = False
            print("Looping random is turned off.")
        return False
    
    async def play_random(self, interaction: discord.Interaction):
        # Specify the directory path where you want to pick a random file
        directory_path = 'C:\\Users\\Windows\\PycharmProjects\\youtubeBot\\song'

        # Get a list of all files in the directory
        all_files = os.listdir(directory_path)

        # Filter out only the files (excluding directories)
        files = [file for file in all_files if os.path.isfile(os.path.join(directory_path, file))]

        # Check if there are any files in the directory
        if files:
            # Pick a random file from the list of files
            random_file = random.choice(files)
        # Get filename without extension
        filename = os.path.splitext(random_file)[0]
        # Play the song
        await self.play_song(interaction, filename)

    async def play_next(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        voice = interaction.guild.voice_client
        queue = self.get_queue(guild_id)

        # Remove the finished song from the queue
        song_name = self.remove_from_queue(guild_id)

        if True == self.loop_playlist_flag:
            # add the song back to the queue
            self.add_to_queue(guild_id, song_name)

        if True == self.loop_flag:
            # add the song back to the queue
            self.add_to_queue_start(guild_id, song_name)

        if True == self.loop_random_flag:
            await self.play_random(interaction)
            return
        # check if the queue is emty
        if 0 == len(queue):
            await interaction.followup.send("Queue is empty. Leaving voice channel.")
            await voice.disconnect()
            return
        
        #play the next song
        if interaction.guild.id in self.queues:
            print(len(queue))
            song_name = queue[0]
            song_path = os.path.join('song', song_name + '.mp3')
            source = FFmpegPCMAudio(song_path)
            voice.play(source, after=lambda x: self.client.loop.create_task(self.play_next(interaction)))
            await interaction.followup.send(f"Now playing: {queue[0]}")

        else:
            await interaction.followup.send("Queue is empty. Leaving voice channel.")
            await voice.disconnect()
    
    #handle and add to queue
    async def handle_queue(self, interaction: discord.Interaction, song_input):
        
        if not song_input.startswith("https://"):
            #handle local file
            self.add_to_queue(interaction.guild.id, song_input)
            await interaction.followup.send(f'Added to queue {song_input}')
            return
        # Remove the "&list" part of the url if it exists
        song_input = self.remove_list_from_url(song_input)
        song_name = self.download_audio(song_input)
        self.add_to_queue(interaction.guild.id, song_name)
        # Send a follow-up message
        await interaction.followup.send(f'Added to queue {song_name}')
    #handle and play song
    async def play_song(self, interaction: discord.Interaction, song_input):
        #check if bot is in voice channel and join if not
        voice = interaction.guild.voice_client
        if voice is None:
            if interaction.user.voice is None:
                await interaction.followup.send(f"{interaction.user.name} are not in channel, please join a channel first.")
                return
            else:

                channel = interaction.user.voice.channel
                voice = await channel.connect()
       
        if voice and voice.is_playing():
           
            await self.handle_queue(interaction, song_input)
            await interaction.followup.send("Music is already playing.Added to queue.")
            return
        #play music
        voice_channel = interaction.user.voice.channel
        if not song_input.startswith("https://"):
            #handle local file
            voice = interaction.guild.voice_client
            song_path = os.path.join('song', song_input + '.mp3')
            source = FFmpegPCMAudio(song_path)
            voice.play(source, after=lambda x: self.client.loop.create_task(self.play_next(interaction)))
            #add to queue
            self.add_to_queue(interaction.guild.id, song_input)
            await interaction.followup.send('**Now playing:** {}'.format(song_input))
        else:
            # Remove the "&list" part of the url if it exists
            song_input = self.remove_list_from_url(song_input)
            #handle youtube url
            song_name = self.download_audio(song_input)
            # Get the full file path for the song in the 'song' folder
            song_path = os.path.join('song', song_name + '.mp3')
            voice = interaction.guild.voice_client
            try:
                source = FFmpegPCMAudio(song_path)
                voice.play(source, after=lambda x: self.client.loop.create_task(self.play_next(interaction)))
                # Add the song to the queue
                self.add_to_queue(interaction.guild.id, song_name)
                await interaction.followup.send('**Now playing:** {}'.format(song_name))
            except Exception as e:
                await interaction.response.send_message(f"An error occurred while playing the audio: {e}")
    
    

    @app_commands.command(name="show_queue", description="Show the queue")
    async def show_queue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        queue = self.get_queue(interaction.guild.id)
        if 0 == len(queue):
            await interaction.followup.send("Queue is empty.")
        else:
            await interaction.followup.send(f"Queue: {queue}")

    @app_commands.command(name="random", description="Play a random song")
    async def random(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.play_random(interaction)
    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        voice = interaction.guild.voice_client
        if voice and voice.is_playing():
            voice.stop()
            await interaction.followup.send("Skipped.")
        else:
            await interaction.followup.send("No audio is playing at the moment.")
    @app_commands.command(name="list", description="List all downloaded songs")
    async def list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        directory = 'C:\\Users\\Windows\\PycharmProjects\\youtubeBot\\song'

        # Get all file names in the directory
        files = os.listdir(directory)

       # Remove the ".mp3" extension from each file name
        files_without_extension = [file.replace('.mp3', '') for file in files]

        # Join all file names with a newline character
        all_files = 'List of all downloaded songs:\n' + '\n'.join(files_without_extension)
        # Send the file names in chunks of 2000 characters or less
        for i in range(0, len(all_files), 2000):
            await interaction.followup.send(all_files[i:i+2000])
    
    @app_commands.command(name="loop_random", description="Join the voice channel")
    async def loop_random(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.toggle_loop_random()
        if True == self.loop_random_flag:
            await interaction.followup.send("Now random looping mode is turn on.")
        else:
            await interaction.followup.send("Random looping mode is turned off.")

    @app_commands.command(name="loop_playlist", description="Join the voice channel")
    async def loop_playlist(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.toggle_loop_playlist()
        if True == self.loop_playlist_flag:
            await interaction.followup.send("Now looping the playlist.")
        else:
            await interaction.followup.send("Looping playlist is turned off.")

    @app_commands.command(name="loop", description="Join the voice channel")
    async def loop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.toggle_loop()
        if True == self.loop_flag:
            await interaction.followup.send("Now looping the current song.")
        else:
            await interaction.followup.send("Looping is turned off.")   

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

        voice = interaction.guild.voice_client
        if voice is not None:
            await voice.disconnect()
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
            self.loop_flag = False
            self.loop_playlist_flag = False
            self.loop_random_flag = False
            voice.stop()
        if interaction.guild.id in self.queues:
            self.queues[interaction.guild.id] = []
            await interaction.followup.send("Queue cleared.")
            await interaction.followup.send("Music stopped.")
        else:
            await interaction.followup.send("No audio is playing or paused at the moment.")


    @app_commands.command(name="play", description="PLay a song")
    async def play(self, interaction: discord.Interaction, song_input: str):
        await interaction.response.defer()
        await self.play_song(interaction, song_input)
        
    @app_commands.command(name="queue", description="Add a song to the queue")
    async def queue(self, interaction: discord.Interaction, song_input: str):
        # Defer the interaction response
        await interaction.response.defer()
        # Handle the queue
        await self.handle_queue(interaction, song_input)
        

async def setup(client):
    await client.add_cog(play_control(client))
