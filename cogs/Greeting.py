import discord
from discord.ext import commands
from discord import app_commands

guildId = 893822110185689149

class Greetings(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.client.loop.create_task(self.sync_commands())

    async def sync_commands(self):
        print("Greeting.cogs loaded and ready")
        await self.client.tree.sync()
    @app_commands.command(name="doivailoz",
                          description="Moew moew bot is a good boy")
    async def hungry(self, interaction: discord.Interaction):
        await interaction.response.send_message("**Đồ ăn tao đâu**")

    @app_commands.command(name="helu",
                          description="làm quen chứ gì")
    async def hi(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.send_message(f"Xuỳ xuỳ {user.mention}")

    @app_commands.command(name="tampit",
                          description="ờ muốn đi đâu thì đi")
    async def bye(self, interaction: discord.Interaction, user: discord.User): 
        await interaction.response.send_message(f"Don't go :(  {user.mention}")


async def setup(client):
    await client.add_cog(Greetings(client))



