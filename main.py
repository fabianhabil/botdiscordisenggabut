from nextcord.ext import commands, tasks
from nextcord import File
from keep_alive import keep_alive
from easy_pil import Editor, Canvas, load_image_async, Font
import json
import nextcord
import os
import asyncio
import random
import math
import aiosqlite
from constants import bot, levelgokil, levelberapa, membercount
from dotenv import load_dotenv
from datetime import datetime
import discord #upm package(nextcord)

# stuff that constants moved to constants.py
# on ready
load_dotenv()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

    
# events
# @bot.event
# async def on_member_join(member):
#     print("test")
#     channel = bot.get_channel(908332446813126678)
#     lengthmember = get_guild_member_count(member.guild)
#     await channel.send(f"Welcome {member.mention} as {lengthmember}")
#     await update_totals(member)
#     await bot.db.commit()
        

async def update_totals(member):
    invites = await member.guild.invites()
    c = datetime.today().strftime("%Y-%m-%d").split("-")
    c_y = int(c[0])
    c_m = int(c[1])
    c_d = int(c[2])

    async with bot.db.execute("SELECT id, uses FROM invites WHERE guild_id = ?", (member.guild.id,)) as cursor:
        async for invite_id, old_uses in cursor:
            for invite in invites:
                if invite.id == invite_id and invite.uses - old_uses > 0: 
                    await bot.db.execute("UPDATE invites SET uses = uses + 1 WHERE guild_id = ? AND id = ?", (invite.guild.id, invite.id))
                    await bot.db.execute("INSERT OR IGNORE INTO joined (guild_id, inviter_id, joiner_id) VALUES (?,?,?)", (invite.guild.id, invite.inviter.id, member.id))
                    await bot.db.execute("UPDATE totals SET normal = normal + 1 WHERE guild_id = ? AND inviter_id = ?", (invite.guild.id, invite.inviter.id))
                else:
                    await bot.db.execute("UPDATE totals SET normal = normal + 1, fake = fake + 1 WHERE guild_id = ? and inviter_id = ?", (invite.guild.id, invite.inviter.id))
                return


@bot.event
async def on_member_remove(member):
    cur = await bot.db.execute("SELECT inviter_id FROM joined WHERE guild_id = ? and joiner_id = ?", (member.guild.id, member.id))
    res = await cur.fetchone()
    if res is None:
        return
    
    inviter = res[0]
    
    await bot.db.execute("DELETE FROM joined WHERE guild_id = ? AND joiner_id = ?", (member.guild.id, member.id))
    await bot.db.execute("DELETE FROM totals WHERE guild_id = ? AND inviter_id = ?", (member.guild.id, member.id))
    await bot.db.execute("UPDATE totals SET left = left + 1 WHERE guild_id = ? AND inviter_id = ?", (member.guild.id, inviter))
    await bot.db.commit()

@bot.event
async def on_invite_create(invite):
    await bot.db.execute("INSERT OR IGNORE INTO totals (guild_id, inviter_id, normal, left, fake) VALUES (?,?,?,?,?)", (invite.guild.id, invite.inviter.id, invite.uses, 0, 0))
    await bot.db.execute("INSERT OR IGNORE INTO invites (guild_id, id, uses) VALUES (?,?,?)", (invite.guild.id, invite.id, invite.uses))
    await bot.db.commit()
    
@bot.event
async def on_invite_delete(invite):
    await bot.db.execute("DELETE FROM invites WHERE guild_id = ? AND id = ?", (invite.guild.id, invite.id))
    await bot.db.commit()

@bot.event
async def on_guild_join(guild):
    for invite in await guild.invites():
        await bot.db.execute("INSERT OR IGNORE INTO invites (guild_id, id, uses), VAlUES (?,?,?)", (guild.id, invite.id, invite.uses))
        
    await bot.db.commit()
    
@bot.event
async def on_guild_remove(guild):
    await bot.db.execute("DELETE FROM totals WHERE guild_id = ?", (guild.id,))
    await bot.db.execute("DELETE FROM invites WHERE guild_id = ?", (guild.id,))
    await bot.db.execute("DELETE FROM joined WHERE guild_id = ?", (guild.id,))

    await bot.db.commit()
    

    
async def setup():
    await bot.wait_until_ready()
    bot.db = await aiosqlite.connect("inviteData.db")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS totals (guild_id int, inviter_id int, normal int, left int, fake int, PRIMARY KEY (guild_id, inviter_id))")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS invites (guild_id int, id string, uses int, PRIMARY KEY (guild_id, id))")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS joined (guild_id int, inviter_id int, joiner_id int, PRIMARY KEY (guild_id, inviter_id, joiner_id))")
    
    for guild in bot.guilds:
        for invite in await guild.invites():
            await bot.db.execute("INSERT OR IGNORE INTO invites (guild_id, id, uses) VALUES (?,?,?)", (invite.guild.id, invite.id, invite.uses))
            await bot.db.execute("INSERT OR IGNORE INTO totals (guild_id, inviter_id, normal, left, fake) VALUES (?,?,?,?,?)", (guild.id, invite.inviter.id, 0, 0, 0))
                                 
    await bot.db.commit()
    
# commands
@bot.command()
async def invites(ctx, member: nextcord.Member=None):
    if member is None: member = ctx.author

    # get counts
    cur = await bot.db.execute("SELECT normal, left, fake FROM totals WHERE guild_id = ? AND inviter_id = ?", (ctx.guild.id, member.id))
    res = await cur.fetchone()
    if res is None:
        normal, left, fake = 0, 0, 0

    else:
        normal, left, fake = res

    total = normal - (left + fake)
    
    em = nextcord.Embed(
        title=f"Invites for {member.name}#{member.discriminator}",
        description=f"{member.mention} currently has **{total}** invites. (**{normal}** normal, **{left}** left, **{fake}** fake).",
        timestamp=datetime.now(),
        colour=nextcord.Colour.orange())

    await ctx.send(embed=em)
    
async def setup():
    await bot.wait_until_ready()
    bot.db = await aiosqlite.connect("invite.db")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS totals (guild_id int, inviter_id int, normal int, left int, fake int, PRIMARY KEY (guild_id, inviter_id))")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS invites (guild_id int, id string, uses int, PRIMARY KEY (guild_id, id))")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS joined (guild_id int, inviter_id int, joiner_id int, PRIMARY KEY (guild_id, inviter_id, joiner_id))")
    
    # fill invites if not there
    for guild in bot.guilds:
        for invite in await guild.invites(): # invites before bot was added won't be recorded, invitemanager/tracker don't do this
            await bot.db.execute("INSERT OR IGNORE INTO invites (guild_id, id, uses) VALUES (?,?,?)", (invite.guild.id, invite.id, invite.uses))
            await bot.db.execute("INSERT OR IGNORE INTO totals (guild_id, inviter_id, normal, left, fake) VALUES (?,?,?,?,?)", (guild.id, invite.inviter.id, 0, 0, 0))
                                 
    await bot.db.commit()
# -----------------------------------------------------------------------------------------------------#
# Role System (reaction role)
# command for showing the text for the reaction and assigning to json
@bot.command(name="selfrole")
async def self_role(ctx):
    #admin channel
    if ctx.channel.id != 909390539630194728 and ctx.channel.id != 904264059384397886:   
      return
    await ctx.send("Satu Menit.")

    questions = [
        "Message?", "emoji?(berurutan sama role + jangan pake spasi) ",
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
            await ctx.send("selfrole command failed.")
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
    await update_totals(member)
    await bot.db.commit()
    with open('users.json', 'w') as f:
        json.dump(users, f, indent = 4)


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
  if ctx.channel.id != 909390539630194728 and ctx.channel.id != 904264059384397886:     #set channel for bot
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
# @bot.command()
# async def leaderboard(ctx):
#   with open('users.json', 'r') as file:
#     users = json.load(file)
#   rankings = users[str(id)].sort(key = lambda x : x['experience'], reverse= True)
#   exp = users[str(id)]['experience']
#   i = 1
#   embed = nextcord.Embed(title = "Rankings")
#   for x in rankings:
#     try:
#       temp = ctx.guild.get_member(users[str(id)])
#       tempxp = x[exp]
#       embed.add_field(name = f"{i} : {temp.name}", value = f"Total XP : {tempxp}", inline = False)
#       i += 1
#     except:
#       pass
#     if i == 11:
#       break
#   await ctx.channel.send(embed=embed)
# -----------------------------------------------------------------------------------------------------#

# server members

@tasks.loop(minutes = 5.0)
async def change_channel(guild):
  print(f"changing channel members count to {get_guild_member_count(guild)}")
  await update_member_count_channel_name(guild)

@bot.command(name="startloop")
async def startcommand(ctx):
  if ctx.message.author.id != 137790236171173888:
      return
  change_channel.start(ctx.guild)

@bot.command(name="refreshmember")
async def on_update_cmd(ctx):
    if ctx.message.author.id != 137790236171173888:
      return
    print(f'changing channel members count to {get_guild_member_count(ctx.guild)} by command')
    await update_member_count_channel_name(ctx.guild)

@bot.command(name="membercount")
async def membercount(ctx):
  await ctx.send(f"{get_guild_member_count(ctx.guild)} member")

async def update_member_count_channel_name(guild):
    member_count_channel_id = get_guild_member_count_channel_id(guild)
    member_count_suffix = get_guild_member_count_suffix(guild)

    if member_count_channel_id != None and member_count_suffix != None:
        member_count_channel = nextcord.utils.get(guild.channels, id=member_count_channel_id)
        new_name = f"{get_guild_member_count(guild)} {member_count_suffix}"
        await member_count_channel.edit(name=new_name)

def get_guild_member_count(guild):
    return len(guild.members)

def get_guild_member_count_channel_id(guild):
    with open("server.json") as json_file:
        data = json.load(json_file)
        for data_guild in data['guilds']:
            if int(data_guild['id']) == guild.id:
                return data_guild['channel_id']

            return

def get_guild_member_count_suffix(guild):
    with open("server.json") as json_file:
        data = json.load(json_file)
        for data_guild in data['guilds']:
            if int(data_guild['id']) == guild.id:
                return data_guild['suffix']

            return



my_secret = os.getenv("token")
keep_alive()
bot.loop.create_task(setup())
bot.run(my_secret)
asyncio.run(bot.db.close())