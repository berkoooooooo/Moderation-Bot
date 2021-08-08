import datetime
import discord
import os
import random
from discord.ext import commands, tasks
from discord import DMChannel
from discord.utils import get
import asyncio
import aiofiles
from discord_components import DiscordComponents, Button, ButtonStyle, InteractionType, component
import aiohttp
import json

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=['u!', 'U!'], intents=intents)
bot.ticket_configs = {}
bot.warnings = {}
bot.remove_command('help')
bot.reaction_roles = []
ddb = DiscordComponents(bot)


@bot.event
async def on_ready():
    for file in ["ticket_configs.txt"]:
        async with aiofiles.open(file, mode="a") as temp:
            pass

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        lines = await file.readlines()
        for line in lines:
            data = line.split(" ")
            bot.ticket_configs[int(data[0])] = [int(data[1]), int(data[2]), int(data[3])]

    for guild in bot.guilds:
        bot.warnings[guild.id] = {}

        async with aiofiles.open(f"{guild.id}.txt", mode="a") as temp:
            pass

        async with aiofiles.open(f"{guild.id}.txt", mode="r") as file:
            lines = await file.readlines()

            for line in lines:
                data = line.split(" ")
                member_id = int(data[0])
                admin_id = int(data[1])
                reason = " ".join(data[2:]).strip("\n")

                try:
                    bot.warnings[guild.id][member_id][0] += 1
                    bot.warnings[guild.id][member_id][1].append((admin_id, reason))

                except KeyError:
                    bot.warnings[guild.id][member_id] = [1, [(admin_id, reason)]]

    await bot.change_presence(status=discord.Status.online, activity=discord.Game('u!help || v.1.5'))
    await asyncio.sleep(10)
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('u!invite for invite!'))
    await asyncio.sleep(10)
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('Made by unrexIstIq#0001'))
    print('Bot is ready.')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.id != bot.user.id and str(payload.emoji) == u"\U0001F3AB":
        msg_id, channel_id, category_id = bot.ticket_configs[payload.guild_id]

        if payload.message_id == msg_id:
            guild = bot.get_guild(payload.guild_id)

            for category in guild.categories:
                if category.id == category_id:
                    break

            channel = guild.get_channel(channel_id)

            ticket_channel = await category.create_text_channel(f"ticket-{payload.member.display_name}",
                                                                topic=f"A ticket for {payload.member.display_name}.",
                                                                permission_synced=True)

            await ticket_channel.set_permissions(payload.member, read_messages=True, send_messages=True)

            message = await channel.fetch_message(msg_id)
            await message.remove_reaction(payload.emoji, payload.member)

            embed= discord.Embed(title="Ticket Created.", description=f"Hello, thank you for creating a Ticket. A Staff Member will be with you soon. To close the Ticket just write 'u!close'!", timestamp=datetime.datetime.utcnow(), color=discord.Colour.green())
            embed.set_footer(text="Ticket")
            await ticket_channel.send(embed=embed)

            try:
                await bot.wait_for("message", check=lambda
                    m: m.channel == ticket_channel and m.author == payload.member and m.content == "u!close",
                                   timeout=3600)

            except asyncio.TimeoutError:
                await ticket_channel.delete()

            else:
                await ticket_channel.delete()

@bot.command()
@commands.has_permissions(administrator=True, manage_roles=True)
async def reactrole(ctx, emoji, role: discord.Role, *, message):

    emb = discord.Embed(description=message, color=discord.Colour.blue())
    msg = await ctx.channel.send(embed=emb)
    await msg.add_reaction(emoji)

    with open('reactrole.json') as json_file:
        data = json.load(json_file)

        new_react_role = {
        'role_id': role.id,
        'emoji': emoji,
        'message_id': msg.id}

        data.append(new_react_role)

    with open('reactrole.json', 'w') as f:
        json.dump(data, f, indent=4)

@bot.listen("on_raw_reaction_add")
async def on_raw_reaction_add_two(payload):

    if payload.member.bot:
        pass

    else:
        with open('reactrole.json') as react_file:
            data = json.load(react_file)
            for x in data:
                if x['emoji'] == payload.emoji.name:
                    role = discord.utils.get(bot.get_guild(
                        payload.guild_id).roles, id=x['role_id'])

                    await payload.member.add_roles(role)




@bot.event
async def on_raw_reaction_remove(payload):
    with open('reactrole.json') as react_file:
        data = json.load(react_file)
        for x in data:
            if x['emoji'] == payload.emoji.name:
                role = discord.utils.get(bot.get_guild(
                    payload.guild_id).roles, id=x['role_id'])

                await bot.get_guild(payload.guild_id).get_member(payload.user_id).remove_roles(role)

@bot.command(pass_context=True)
async def help(ctx):
    embed = discord.Embed(title='A User requested the Help command!', timestamp=datetime.datetime.utcnow(),
                          color=discord.Colour.green())
    embed2 = discord.Embed(title="Moderation Help", timestamp=datetime.datetime.utcnow(), color=discord.Colour.green())
    embed2.add_field(name="u!kick", value="Kicks a specific User.", inline=False)
    embed2.add_field(name="u!ban", value="Bans a specific User.", inline=False)
    embed2.add_field(name="u!unban", value="Unbans a specific User", inline=False)
    embed2.add_field(name="u!warn", value="Warns a specific User", inline=False)
    embed2.add_field(name="u!warnings", value="Shows the warnings of a specific User.", inline=False)
    embed2.add_field(name="u!mute", value="Mutes a specific User.", inline=False)
    embed2.add_field(name="u!unmute", value="Unmutes a specific User.", inline=False)
    embed2.add_field(name="u!clear", value="Clears a specific Amount out of the Chat.", inline=False)
    embed2.set_footer(text="Moderation Help")

    embed3 = discord.Embed(title="Fun Help", timestamp=datetime.datetime.utcnow(), color=discord.Colour.orange())
    embed3.add_field(name="u!userinfo", value="Gives the Infomartions of a User.", inline=False)
    embed3.add_field(name="u!serverinfo", value="Gives the Informations of the Server.", inline=False)
    embed3.add_field(name="More Coming Soon", value="", inline=False)
    embed3.set_footer(text="Fun Help")

    embed.add_field(name='Moderation', value='Press the Button down below for more informations!', inline=False)
    embed.add_field(name='Fun', value='Coming Soon', inline=False)
    embed.set_footer(text='Help'),
    component=[
        [Button(style=ButtonStyle.green, label="Moderation", custom_id= "1"),
         Button(style=ButtonStyle.red, label="Fun"),
         Button(style=ButtonStyle.URL, label="Website", url="https://www.moderation-bot.ml")]
        ]
    await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158>")
    await ctx.send(embed=embed, components=component)
    res = await bot.wait_for("button_click")
    if res.component.custom_id == 1:
        if res.channel == ctx.message.channel:
            await res.respond(
            type=InteractionType.ChannelMessageWithSource,
            embed=embed2
        )
    else:
          if res.channel == ctx.message.channel:
              await res.respond(
                  type=InteractionType.ChannelMessageWithSource,
                  embed=embed3
                )


@bot.command()
@commands.has_permissions(administrator=True)
async def claim(ctx):
    embed = discord.Embed(title=f'Ticket has been claimed.',
                          description=f'The Ticket has been claimed by a Staff Member.', color=discord.Colour.green())
    await ctx.channel.purge(limit=1)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def addrole(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158>")
    embed = discord.Embed(title="Role added!",
                          description=f"The role {role} has been add to the Member {member}!",
                          color=discord.Colour.green())
    await ctx.send(embed=embed)


@bot.command()
async def invite(ctx):
    await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158")
    embed = discord.Embed(title='Bot Invite', timestamp=datetime.datetime.utcnow(),
                          color=discord.Colour.green())

    embed.add_field(name='Invite', value='Press the Button to invite our Bot!', inline=False)
    embed.set_footer(text="Invite"),
    component = [
         Button(style=ButtonStyle.URL, label="Website", url="https://top.gg/bot/863118090619584533")
    ]
    await ctx.send(embed=embed, components=component)

@bot.command()
@commands.has_permissions(administrator=True)
async def removerole(ctx, member: discord.Member, role: discord.Role):
    lst = [871329649219764234]
    if member.id not in lst:
        await ctx.send("Test")

    if member.id in lst:
        await member.remove_roles(role)
        await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158")
        embed = discord.Embed(title="Role removed!", description=f"The role {role} has been removed from the Member {member}!", color=discord.Colour.green())
        await ctx.send(embed=embed)

@bot.command(pass_context=True)
async def meme(ctx):
    embed = discord.Embed(title="> **Your Meme**", description="", timestamp=datetime.datetime.utcnow(), color=discord.Color.blue())
    embed.set_footer(text="Meme")
    async with aiohttp.ClientSession() as cs:
        async with cs.get('https://www.reddit.com/r/dankmemes/new.json?sort=hot') as r:
            res = await r.json()
            embed.set_image(url=res['data']['children'] [random.randint(0, 25)]['data']['url'])
            await ctx.message.delete()
            await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def gcreate(ctx, time=None, *, prize=None):
    if time == None:
        return await ctx.send("Please give us a Time for the Giveway")
    elif prize == None:
        return await ctx.send("Please describe a Price")
    embed = discord.Embed(
        title=f"{prize}",
        description=f"React with :gift: to enter the Giveway!\n Ends in: {time}\n Created by: {ctx.author.mention}",
        color=discord.Colour.blue()
    )
    time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    gawtime = int(time[0]) * time_convert[time[-1]]
    gaw_msg = await ctx.send(embed=embed)
    await gaw_msg.add_reaction('🎁')
    await asyncio.sleep(gawtime)
    new_gaw_msg = await ctx.channel.fetch_message(gaw_msg.id)
    users = await new_gaw_msg.reactions[0].users().flatten()
    users.pop(users.index(bot.user))
    if len(users) <= 0:
        emptyEmbed = discord.Embed(title=f'{prize}',
                                   description=f"👑 │ Winner: `- :(`\n"
                                               f"👤 │ Created by: {ctx.author.mention}", color=0xc12e2e)
        emptyEmbed.set_footer(text='Giveway has ended')
        await gaw_msg.edit("**⛔⛔ GIVEWAY HAS ENDED! ⛔⛔**", embed=emptyEmbed)
        return
    if len(users) > 0:
        winner = random.choice(users)
        winnerEmbed = discord.Embed(title=f'{prize}',
                                    description=f"👑 │ Winner: {winner.mention}\n"
                                                f"👤 │ Created by: {ctx.author.mention}", color=0xc12e2e)
        winnerEmbed.set_footer(text='Giveway ended')
        await gaw_msg.edit(content=f'**⛔⛔ GIVEWAY HAS ENDED! ⛔⛔**', embed=winnerEmbed)
        await ctx.channel.send(f'Good one, {winner.mention}! You have won **{prize}**!')
        return

@bot.command(name="afk")
async def afk(ctx, *, args: str = 'No Reason'):
    embed = discord.Embed(title=f"{ctx.author.name} went AFK",description=f'AFK Reason: {args}', colour=0x0ad4b7)
    await ctx.send(embed=embed)

@bot.command()
async def say(ctx, *, message:str):
    embed = discord.Embed(title=ctx.author.display_name, color=discord.Color.blue())
    embed.add_field(name="Says:", value=message)
    await ctx.send(embed=embed)

@bot.command()
async def kill(ctx, *, member):
    author_name = ctx.message.author.name
    await ctx.send (f'{author_name} has killed {member} <a:kill_him:849361271576985631> \n https://tenor.com/view/duck-mad-angry-i-will-kill-you-gif-17283481')

@bot.command()
async def hug(ctx, *, member):
    author_name = ctx.message.author.name
    await ctx.send (f'{author_name} hugged {member} <a:hug:849361400379605012> \n https://tenor.com/view/marriage-marry-up-kiss-gif-4360989')

@bot.command()
async def covid(ctx):
    List = ["Positive", "Negative💉"]
    test = random.choice(List)
    embedVar = discord.Embed(title=":mask: Corona Test Result: ", description="Do you have Corona?", color=discord.Color.blue())
    embedVar.add_field(name=f"{ctx.message.author}", value=f"has a {test} Corona Test!")
    await ctx.send(embed=embedVar)

@bot.command()
async def gay(ctx):
    zeroto100 = random.randint(0, 100)
    embedVar = discord.Embed(title=":rainbow_flag: Gay Rate: ", description="Your gayness", color=discord.Color.blue())
    embedVar.add_field(name=f"{ctx.message.author}", value=f"is {zeroto100} % gay ! :rainbow_flag:")
    await ctx.send(embed=embedVar)

@bot.command()
async def cool(ctx):
    zeroto100 = random.randint(0, 100)
    embedVar = discord.Embed(title="How cool are you?", color=discord.Color.blue())
    embedVar.add_field(name=f"{ctx.message.author}", value=f"is {zeroto100} % cool")
    await ctx.send(embed=embedVar)

@bot.command()
async def number(ctx):
    zeroto100 = random.randint(0, 100)
    embedVar = discord.Embed(title="Random Number", color=discord.Color.blue())
    embedVar.add_field(name=f"Your number is:", value=f" {zeroto100}")
    await ctx.send(embed=embedVar)

@bot.command()
async def qtrue(ctx, *, args):
    responses4 = [
        'Yes', 'No', 'Of Course', 'Maybe', "I don't care...",
        'Try again later.'
    ]
    if args:
        embed = discord.Embed(
            title="🔮 True or not? 🔮",
            description=
            f"\nI am trying to answer your question `{args}` \n ",
            colour=discord.Colour(0x0ad4b7),
            timestamp=ctx.message.created_at)
        embed.set_footer(text="Wait Time » 2s")
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed1 = discord.Embed(
            title="🔮 True or not? 🔮",
            description=f"\nI am trying to reach something...\n ",
            colour=discord.Colour(0x0ad4b7),
            timestamp=ctx.message.created_at)
        embed1.set_footer(text="Wait Time » 2s")
        embed1.set_thumbnail(url=ctx.author.avatar_url)
        embed2 = discord.Embed(
            title="🔮 True or not? 🔮",
            description=
            f"\nThe answer to your question `{args}` is: `{random.choice(responses4)}`\n ",
            colour=discord.Colour(0x0ad4b7),
            timestamp=ctx.message.created_at)
        embed2.set_footer(text="Wait Time » 2s")
        embed2.set_thumbnail(url=ctx.author.avatar_url)
        mess = await ctx.send(embed=embed)
        await asyncio.sleep(2)
        await mess.edit(embed=embed1)
        await asyncio.sleep(2)
        await mess.edit(embed=embed2)

@bot.command()
async def dumbness(ctx, target: discord.Member):
    responses7 = [
        '0,1%', '57%', '60%', '77%', '97%', '55%', '65%', '39%', '24%', '91%',
        '75%', '4%', '58%', '79%', '35%', '10%', '47%', '43%', '34%', '90%',
        '37%', '44%', '81%', '4%', '31%', '97%', '45%', '49%', '44%', '79%',
        '24%', '43%', '73%', '33%', '88%', '23%', '83%', '82%', '87%', '27%',
        '1%', '1000%', '51%', '60%', '25%'
    ]
    if target:
        embed = discord.Embed(
            title="Dumbness",
            description=f"I am trying to find the User {target.mention}!",
            colour=discord.Colour(0x0ad4b7),
            timestamp=ctx.message.created_at)
        embed.set_footer(text="Wait Time » 2s")
        embed.set_thumbnail(url=target.avatar_url)
        embed1 = discord.Embed(
            title="Dumbness",
            description=
            f"The User {target.mention} is {random.choice(responses7)} dumb!",
            colour=discord.Colour(0x0ad4b7),
            timestamp=ctx.message.created_at)
        embed1.set_footer(text="Wartezeit » 2s")
        embed1.set_thumbnail(url=target.avatar_url)
        mess = await ctx.send(embed=embed)
        await asyncio.sleep(2)
        await mess.edit(embed=embed1)


@bot.event
async def on_guild_join(guild):
    bot.warnings[guild.id] = {}


@bot.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member = None, *, reason=None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")

    if reason is None:
        return await ctx.send("Please provide a reason for warning this user.")

    try:
        first_warning = False
        bot.warnings[ctx.guild.id][member.id][0] += 1
        bot.warnings[ctx.guild.id][member.id][1].append((ctx.author.id, reason))

    except KeyError:
        first_warning = True
        bot.warnings[ctx.guild.id][member.id] = [1, [(ctx.author.id, reason)]]

    count = bot.warnings[ctx.guild.id][member.id][0]

    async with aiofiles.open(f"{ctx.guild.id}.txt", mode="a") as file:
        await file.write(f"{member.id} {ctx.author.id} {reason}\n")

    await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158")
    embed = discord.Embed(title=f'Warn successful!', description=f'{member.mention} has received {count} warning/s!',
                          timestamp=datetime.datetime.utcnow(), color=discord.Colour.green())
    embed.set_footer(text='Warn successful!')
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def warnings(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")

    await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158")
    embed = discord.Embed(title=f"Displaying Warnings for {member.name}", description="", colour=discord.Colour.red())
    try:
        i = 1
        for admin_id, reason in bot.warnings[ctx.guild.id][member.id][1]:
            admin = ctx.guild.get_member(admin_id)
            embed.description += f"**Warning {i}** given by: {admin.mention} for: *'{reason}'*.\n"
            i += 1

        await ctx.send(embed=embed)

    except KeyError:  # no warnings
        await ctx.send("This user has no warnings.")


@bot.command()
async def configure_ticket(ctx, msg: discord.Message = None, category: discord.CategoryChannel = None):
    if msg is None or category is None:
        await ctx.channel.send("Failed to configure the ticket as an argument was not given or was invalid.")
        return

    bot.ticket_configs[ctx.guild.id] = [msg.id, msg.channel.id, category.id]  # this resets the configuration

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        data = await file.readlines()

    async with aiofiles.open("ticket_configs.txt", mode="w") as file:
        await file.write(f"{ctx.guild.id} {msg.id} {msg.channel.id} {category.id}\n")

        for line in data:
            if int(line.split(" ")[0]) != ctx.guild.id:
                await file.write(line)

    await msg.add_reaction(u"\U0001F3AB")
    await ctx.channel.send("Succesfully configured the ticket system.")

@bot.command()
@commands.has_permissions(administrator=True)
async def mute(ctx, member: discord.Member = None, reason=None):
    guild = ctx.guild
    rolecreate = await guild.create_role(name="Muted")
    if not member:
        await ctx.send('Please specify a member!')
        return
    if reason == None:
        embed = discord.Embed(title=f'Error', description=f'An Argument is missing. (Reason)!',
                              color=discord.Colour.red())
        await ctx.send(embed=embed)
        return
    await member.add_roles(rolecreate)
    await rolecreate.edit(send_messages=False)
    await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158")
    embed = discord.Embed(title=f"Mute successful!",
                          description=f"I have successfully muted {member.mention}!", color=discord.Colour.green())
    await ctx.send(embed=embed)

@bot.command()
async def servers(ctx):
    await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158")
    activeservers = bot.guilds
    for guild in activeservers:
        await ctx.send(guild.name)


@bot.command()
@commands.has_permissions(administrator=True)
async def unmute(ctx, member: discord.Member = None, reason=None):
    role = discord.utils.get(ctx.guild.roles, name='Muted')
    role2 = discord.utils.get(ctx.guild.roles, name="Member")
    if not member:
        await ctx.send('Please specify a member!')
        return
    await member.remove_roles(role)
    await member.add_roles(role2)
    await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158")
    embed = discord.Embed(title=f"Unmute successful!",
                          description=f"I have successfully unmuted {member.mention}!", color=discord.Colour.green())
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount=0):
    if (ctx.message.author.permissions_in(ctx.message.channel).manage_messages):
        await ctx.channel.purge(limit=amount + 1)
    embed = discord.Embed(title=f"Chat cleared", description=f"The Chat has been cleared with the amount of {amount}!",
                          color=discord.Colour.green())
    await ctx.send(embed=embed)
    await asyncio.sleep(10)
    await ctx.channel.purge(limit=1)


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158")
    embed = discord.Embed(title=f"Successfully kicked {member.mention}",
                          description=f"I have successfully kicked a user for you, thanks for holding our Discord "
                                      f"clean!",
                          color=discord.Colour.red())
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158")
    embed = discord.Embed(title="Successfully kicked {member.mention}",
                          description=f"I have successfully kicked a user for you, "
                                      f"thanks for holding our Discord clean!",
                          color=discord.Colour.red())
    await ctx.send(embed=embed)

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = ctx.author if not member else member
    roles = [role for role in member.roles]

    embed = discord.Embed(colour=member.color, timestamp=ctx.message.created_at)

    embed.set_author(name=f"User Info - {member}")
    embed.set_thumbnail(url=member.avatar_url)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)

    embed.add_field(name="ID:",value=member.id, inline=True)
    embed.add_field(name="Guild Name:", value=member.display_name, inline=True)

    embed.add_field(name="Created at:", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline=True)
    embed.add_field(name="Joined at:", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"), inline=True)

    embed.add_field(name=f"Roles ({len(roles)})", value=" ".join([role.mention for role in roles]), inline=True)
    embed.add_field(name="Top role:", value=member.top_role.mention, inline=True)

    embed.add_field(name="Bot?", value=member.bot, inline=True)

    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    name = str(ctx.guild.name)
    description = str(ctx.guild.description)

    owner = str(ctx.guild.owner)
    id = str(ctx.guild.id)
    region = str(ctx.guild.region)
    membercount = str(ctx.guild.member_count)

    icon = str(ctx.guild.icon_url)

    embed = discord.Embed(
        title = name + "Server Information",
        description=description,
        color = discord.Colour.green()
    )
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Owner", value=owner, inline=True)
    embed.add_field(name="Server ID", value=id, inline=True)
    embed.add_field(name="Region", value=region, inline=True)
    embed.add_field(name="Member Count", value=membercount, inline=True)

    await ctx.send(embed=embed)



@bot.event
async def on_member_join(member):
    embed = discord.Embed(title=f'Thank you for joining our Server!',
                          description=f'Hey, you! Please read the Rules and check the checkmark to'
                                      f' gain access to the rest of the Server! Have a good day.',
                          timestamp=datetime.datetime.utcnow(), color=discord.Colour.green())
    embed.set_footer(text='Server Join')
    await member.send(embed=embed)


@bot.event
async def on_member_remove(member):
    embed = discord.Embed(title=f'Server Leave',
                          description=f'Hey, you! Pretty sad that you left our Server! '
                                      f'We would really appreciate it if you would join the Server again! '
                                      f'Have a good day.',
                          timestamp=datetime.datetime.utcnow(), color=discord.Colour.red())
    embed.set_footer(text='Server Leave')
    await member.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158")
            embed = discord.Embed(title=f"Successfully unbanned a user!",
                                  description=f"I have successfully unbanned a user for you!")
            await ctx.send(embed=embed)
            return


@bot.command()
async def ping(ctx):
    await ctx.message.add_reaction("<a:5845_tickgreen:871325490844164158")
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')


@bot.command()
async def ticket_config(ctx):
    try:
        msg_id, channel_id, category_id = bot.ticket_configs[ctx.guild.id]

    except KeyError:
        await ctx.channel.send("You have not configured the ticket system yet.")

    else:
        embed = discord.Embed(title="Ticket System Configurations", color=discord.Color.green())
        embed.description = f"**Reaction Message ID** : {msg_id}\n"
        embed.description += f"**Ticket Category ID** : {category_id}\n\n"

        await ctx.channel.send(embed=embed)


bot.run('ODYzMTE4MDkwNjE5NTg0NTMz.YOiPXA.H9f6pTpXOrkgJu19j1yqoBx62uQ')
