from nextcord.ext import commands
from nextcord import File
from keep_alive import keep_alive
from easy_pil import Editor, Canvas, load_image_async, Font
import json
import nextcord
import os
import asyncio
import random
import math

# -----------------------------------------------------------------------------------------------------#
# stuff that constant 
botintents = nextcord.Intents.default()
botintents.presences = True
botintents.members = True
botactivity = nextcord.Game(name="@fabianhabil")
bot = commands.Bot(command_prefix='!',
                   intents=botintents,
                   activity=botactivity)
levelgokil = ["Barong", "Certified Barong", "OG Barong"]
levelberapa = [2, 5, 15]
# -----------------------------------------------------------------------------------------------------#

# on ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

# -----------------------------------------------------------------------------------------------------#
# Role System (reaction role)
# command for showing the text for the reaction and assigning to json
@bot.command(name="selfrole")
async def self_role(ctx):
    await ctx.send("1 menit")

    questions = [
        "isi pesan ", "emoji?(berurutan sama role + jangan pake spasi) ",
        "role (gapake @ langsung ketik nama, berurutan) ", "channel mana?"
    ]
    answers = []

    def check(user):
        return user.author == ctx.author and user.channel == ctx.channel

    for question in questions:
        await ctx.send(question)

        try:
            msg = await bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("yang cepet gera goblogh")
            return
        else:
            answers.append(msg.content)

    emojis = answers[1].split(" ")
    roles = answers[2].split(" ")
    c_id = int(answers[3][2:-1])
    channel = bot.get_channel(c_id)

    bot_msg = await channel.send(answers[0])

    with open("selfrole.json", "r") as f:
        self_roles = json.load(f)

    self_roles[str(bot_msg.id)] = {}
    self_roles[str(bot_msg.id)]["emojis"] = emojis
    self_roles[str(bot_msg.id)]["roles"] = roles

    with open("selfrole.json", "w") as f:
        json.dump(self_roles, f, indent=4)

    for emoji in emojis:
        await bot_msg.add_reaction(emoji)

# when someone givng reaction to the message that stored in the !selfrole json file
@bot.event
async def on_raw_reaction_add(payload):
    msg_id = payload.message_id

    with open("selfrole.json", "r") as f:
        self_roles = json.load(f)

    if payload.member.bot:
        return

    if str(msg_id) in self_roles:
        emojis = []
        roles = []

        for emoji in self_roles[str(msg_id)]['emojis']:
            emojis.append(emoji)

        for role in self_roles[str(msg_id)]['roles']:
            roles.append(role)

        guild = bot.get_guild(payload.guild_id)

        for i in range(len(emojis)):
            choosed_emoji = str(payload.emoji)
            if choosed_emoji == emojis[i]:
                selected_role = roles[i]

                role = nextcord.utils.get(guild.roles, name=selected_role)

                await payload.member.add_roles(role)
                # await payload.member.send(f"You get the {selected_role} cok")

# when someone givng reaction to the message that stored in the !selfrole json file (remove)
@bot.event
async def on_raw_reaction_remove(payload):
    msg_id = payload.message_id

    with open("selfrole.json", "r") as f:
        self_roles = json.load(f)

    if str(msg_id) in self_roles:
        emojis = []
        roles = []

        for emoji in self_roles[str(msg_id)]['emojis']:
            emojis.append(emoji)

        for role in self_roles[str(msg_id)]['roles']:
            roles.append(role)

        guild = bot.get_guild(payload.guild_id)

        for i in range(len(emojis)):
            choosed_emoji = str(payload.emoji)
            if choosed_emoji == emojis[i]:
                selected_role = roles[i]

                role = nextcord.utils.get(guild.roles, name=selected_role)

                member = await (guild.fetch_member(payload.user_id))
                if member is not None:
                    await member.remove_roles(role)
# -----------------------------------------------------------------------------------------------------#

# -----------------------------------------------------------------------------------------------------#
#Levelling system
#detect when someone join the servers and update to the json
@bot.event
async def on_member_join(member):
  with open('users.json', 'r') as f:
    users = json.load(f)

  await update_data(users, member)
  
  with open('users.json', 'w') as f:
    json.dump(users, f, indent = 4)

#detect when someone chat in the text channel
#cooldown
# class SomeCog(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot
#         self._cd = commands.CooldownMapping.from_cooldown(1.0, 60.0, commands.BucketType.user) # Put your params here
#                                                         # rate, per, BucketType

#     def ratelimit_check(self, message):
#         """Returns the ratelimit left"""
#         bucket = self._cd.get_bucket(message)
#         return bucket.update_rate_limit()

#     @commands.Cog.listener()
#     async def on_message(self, message):
#         if 'check if the message contains certain words here':
#             # Getting the ratelimit that's left
#             retry_after = self.ratelimit_check(message)
#             if retry_after is None:
#                 await message.channel.send("oke")
#             else:
#                 # You're ratelimited, you can delete the message here
#                 await message.delete()
#                 await message.channel.send(f"You can't use those words for another {round(retry_after)} seconds.")

@bot.event
async def on_message(message):
  if message.author.bot == False:
    with open('users.json', 'r') as f:
      users = json.load(f)
    await update_data(users, message.author)
    await add_experience(users, message.author, random.randint(1,3))
    await level_up(users, message.author, message)
    with open('users.json', 'w') as f:
      json.dump(users, f, indent = 4)
    
  await bot.process_commands(message)
  await asyncio.sleep(20)

#updating data
async def update_data(users, user):
  if not f'{user.id}' in users:
    users[f'{user.id}'] = {}
    users[f'{user.id}']['experience'] = 0
    users[f'{user.id}']['level'] = 1

#adding experience
async def add_experience(users, user, exp):
  users[f'{user.id}']['experience'] += exp

#level up system (when level up)
async def level_up(users, user, message):
  channel = bot.get_channel(908332446813126678)
  experience = users[f'{user.id}']['experience']
  lvl_start = users[f'{user.id}']['level']
  expneeded = (50 * ((int(lvl_start) + 1) ** 2) - (50 * (int(lvl_start) + 1)))
  expnow = int(experience)
  if expnow > expneeded:
    await channel.send(f'{user.mention} leveled up to **level {lvl_start + 1}**')
    users[f'{user.id}']['level'] = lvl_start + 1
    for i in range(len(levelgokil)):
      if users[f'{user.id}']['level'] == levelberapa[i]:
        await message.author.add_roles(nextcord.utils.get(message.author.guild.roles, name = levelgokil[i]))

#what level am i?
@bot.command()
async def rank(ctx):
  id = ctx.message.author.id
  if ctx.channel.id != 909390539630194728 and ctx.channel.id != 904264059384397886: #set channel for bot
    return
  with open('users.json', 'r') as f:
    users = json.load(f)
  lvl = users[str(id)]['level']
  exp = users[str(id)]['experience']
  expneeded = (50 * (((lvl) + 1) ** 2) - (50 * ((lvl) + 1)))
  expneedeed = expneeded - exp
  a = exp - (50 * ((lvl) ** 2) - (50 * (lvl)))
  b = (50 * ((lvl + 1) ** 2) - (50 * (lvl + 1))) - (50 * ((lvl) ** 2) - (50 * (lvl)))
  persen = math.ceil(a/b*100)
  background = Editor("bg.png")
  level = Font("level.otf", size=79)
  name = Font("name.otf", size=35)
  xp = Font("xp.otf", size=17)
  foto = await load_image_async(ctx.author.avatar.url)
  profile = Editor(foto).resize((230, 230))

#level 1 digit, exp puluhan (20 / 100)
  if lvl < 10 and exp <= 100:  
    background.paste(profile.image, (35, 35))
    background.text(
        (290, 177),
        (f"{ctx.author}"),
        font=name,
        color="white"
    )

    background.text(
        (750,190),
        f"{exp} / {expneeded} EXP",
        font = xp,
        color="white"
    )

    background.text(
        (805,37),
        f"{lvl}",
        font = level,
        color="#00FA81"
    )

    background.bar(
        (299,220.999999999999995),
        max_width = 560.4786,
        height = 37.2,
        fill = "#FAC000",
        percentage = persen
    )

#level 1 digit, exp masih ribuan ( ratusan / ribuan )
  if lvl < 10 and exp < 1100 and exp > 100:  
    background.paste(profile.image, (35, 35))
    background.text(
        (290, 177),
        (f"{ctx.author}"),
        font=name,
        color="white"
    )

    background.text(
        (730,190),
        f"{exp} / {expneeded} EXP",
        font = xp,
        color="white"
    )

    background.text(
        (805,37),
        f"{lvl}",
        font = level,
        color="#00FA81"
    )

    background.bar(
        (299,220.999999999999995),
        max_width = 560.4786,
        height = 37.2,
        fill = "#FAC000",
        percentage = persen
    )

#level 1 digit, exp 2.1k sampe 10k
  elif lvl < 10 and exp >= 1100:
    background.paste(profile.image, (35, 35))
    background.text(
        (290, 177),
        (f"{ctx.author}"),
        font=name,
        color="white"
    )

    background.text(
        (730,190),
        f"{round(exp/1000, 1)}K / {round(expneeded/1000,1)}K EXP",
        font = xp,
        color="white"
    )

    background.text(
        (800,37),
        f"{lvl}",
        font = level,
        color="#00FA81"
    )

    background.bar(
        (299,220.999999999999995),
        max_width = 560.4786,
        height = 37.2,
        fill = "#FAC000",
        percentage = persen
    )

#level 2 digit, exp puluhan ribuan
  elif lvl >= 10 and exp >= 5000 and exp < 100000:
    background.paste(profile.image, (35, 35))
    background.text(
        (290, 177),
        (f"{ctx.author}"),
        font=name,
        color="white"
    )

    background.text(
        (717,190),
        f"{round(exp/1000, 1)}K / {round(expneeded/1000,1)}K EXP",
        font = xp,
        color="white"
    )

    background.text(
        (775,37),
        f"{lvl}",
        font = level,
        color="#00FA81"
    )

    background.bar(
        (299,220.999999999999995),
        max_width = 560.4786,
        height = 37.2,
        fill = "#FAC000",
        percentage = persen
    )

#level 2 digit, exp ratusan ribuan
  elif lvl >= 10 and exp >= 100000:
    background.paste(profile.image, (35, 35))
    background.text(
        (290, 177),
        (f"{ctx.author}"),
        font=name,
        color="white"
    )

    background.text(
        (700,190),
        f"{round(exp/1000, 1)}K / {round(expneeded/1000,1)}K EXP",
        font = xp,
        color="white"
    )

    background.bar(
        (299,220.999999999999995),
        max_width = 560.4786,
        height = 37.2,
        fill = "#FAC000",
        percentage = persen
    )

    background.text(
        (775,37),
        f"{lvl}",
        font = level,
        color="#00FA81"
    )

  file = File(fp=background.image_bytes, filename="card.png")
  await ctx.send(file=file)

# leaderboard? (not ready yet, still need to be fixed)
@bot.command()
async def leaderboard(ctx):
  with open('users.json', 'r') as file:
    users = json.load(file)
  rankings = users[str(id)].sort(key = lambda x : x['experience'], reverse= True)
  exp = users[str(id)]['experience']
  i = 1
  embed = nextcord.Embed(title = "Rankings")
  for x in rankings:
    try:
      temp = ctx.guild.get_member(users[str(id)])
      tempxp = x[exp]
      embed.add_field(name = f"{i} : {temp.name}", value = f"Total XP : {tempxp}", inline = False)
      i += 1
    except:
      pass
    if i == 11:
      break
  await ctx.channel.send(embed=embed)

# -----------------------------------------------------------------------------------------------------#
# # members count, not finished yet
# server members
# @bot.event
# async def on_member_join(member):
#     """ gets triggered when a new member joins a guild """
#     print(f"* {member} joined {member.guild}")
#     await update_member_count_channel_name(member.guild)


# @bot.event
# async def on_member_remove(member):
#     """ gets triggered when a new member leaves or gets removed from a guild """
#     print(f"* {member} left {member.guild}")
#     await update_member_count_channel_name(member.guild)


# @bot.command(name="update")
# async def on_update_cmd(ctx):
#     """ triggers manual update of member count channel """
#     print(f"* {ctx.author} issued update")
#     await update_member_count_channel_name(ctx.guild)


# async def update_member_count_channel_name(guild):
#     """ updates the name of the member count channel """
#     member_count_channel_id = get_guild_member_count_channel_id(guild)
#     member_count_suffix = get_guild_member_count_suffix(guild)

#     if member_count_channel_id != None and member_count_suffix != None:
#         member_count_channel = discord.utils.get(guild.channels, id=member_count_channel_id)
#         new_name = f"{get_guild_member_count(guild)} {member_count_suffix}"
#         await member_count_channel.edit(name=new_name)

#     else:
#         print(f"* could not update member count channel for {guild}, id not found in {JSON_FILE}") 


# def get_guild_member_count(guild):
#     """ returns the member count of a guild """
#     return len(guild.members)


# def get_guild_member_count_channel_id(guild):
#     """ returns the channel id for the channel that should display the member count """
#     with open("server.json") as json_file:
#         # open JSON file
#         data = json.load(json_file)
#         for data_guild in data['guilds']:
#             if int(data_guild['id']) == guild.id:
#                 return data_guild['channel_id']

#             return None


# def get_guild_member_count_suffix(guild):
#     """ returns the the suffix that should be displayed after the member count """
#     with open("server.json") as json_file:
#         # open JSON file
#         data = json.load(json_file)
#         for data_guild in data['guilds']:
#             if int(data_guild['id']) == guild.id:
#                 return data_guild['suffix']

#             return None





# -----------------------------------------------------------------------------------------------------#
#run the bot!
my_secret = os.environ['mytoken']
keep_alive()
bot.run(my_secret)