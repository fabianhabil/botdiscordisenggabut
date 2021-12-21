from nextcord.ext import commands
from nextcord import File
import nextcord
import json
import os

# stuff that constant 
botintents = nextcord.Intents.default()
botintents.presences = True
botintents.members = True
botactivity = nextcord.Game(name="@fabianhabil")
bot = commands.Bot(command_prefix='!',
                   intents=botintents,
                   activity=botactivity)
bot.remove_command("help")
levelgokil = ["Barong", "Certified Barong", "OG Barong"]
levelberapa = [2, 5, 15]
membercount = str(os.path.dirname(os.path.realpath(__file__))) + '/server.json'