import discord
from discord.ext import commands
import os
import apikey

intents = discord.Intents.all()

client = commands.Bot(command_prefix= '!', intents = intents)

testServerID = 893822110185689149


@client.tree.command(name="hi", description="My first application Command", guild=discord.Object(id=testServerID))
async def first_command(interaction):
    await interaction.response.send_message("Hello!")


@client.event
async def on_ready():
    await client.tree.sync(guild=discord.Object(id=testServerID))
    initial_extensions = []

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            initial_extensions.append(f"cogs." + filename[:-3])

    if __name__ == '__main__':
        for extension in initial_extensions:
            await client.load_extension(extension)

    print("The bot is now ready for use!")
    print("-----------------------------")




client.run(apikey.BOTTOKEN)
