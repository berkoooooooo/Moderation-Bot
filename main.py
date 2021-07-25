import discord
import os
import random
from discord.ext import commands, tasks
from discord import DMChannel
from discord.utils import get
import asyncio
import traceback
import sys
import aiofiles
import time
import json
import keep_alive

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='m!', intents=intents)
bot.ticket_configs = {}
bot.warnings = {}
bot.remove_command('help')


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

    await bot.change_presence(status=discord.Status.online, activity=discord.Game('.help || v.1 (Out of Beta!)'))
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

            ticket_num = 1 if len(category.channels) == 0 else int(category.channels[-1].name.split("-")[1]) + 1
            ticket_channel = await category.create_text_channel(f"ticket {ticket_num}",
                                                                topic=f"A channel for a ticket number {ticket_num}.",
                                                                permissions_synced=True)

            await ticket_channel.set_permissions(payload.member, read_messages=True, send_messages=True)

            message = await channel.fetch_message(msg_id)
            await message.remove_reaction(payload.emoji, payload.member)

            embed = discord.Embed(title=f"Thank you for creating a ticket!",
                                  description=f"Hello! Thank you for creating a ticket. A Staff Member will be with you soon! Do you want to close this ticket? No Problem! Use **-close** to close this ticket!",
                                  color=discord.Colour.red())
            await ticket_channel.send(embed=embed)

            try:
                await bot.wait_for("message", check=lambda
                    m: m.channel == ticket_channel and m.author == payload.member and m.content == "-close",
                                   timeout=3600)

            except asyncio.TimeoutError:
                await ticket_channel.delete()

            else:
                await ticket_channel.delete()


@bot.command(pass_context=True)
async def help(ctx):
    embed = discord.Embed(title='A User requested the Help command!', color=discord.Colour.red())

    embed.add_field(name='m!help', value='Shows this Message.', inline=False)
    embed.add_field(name='m!warn', value='Warns a specific User.', inline=False)
    embed.add_field(name='m!warnings', value='Shows Warnings of a specific User.', inline=False)
    embed.add_field(name='m!mute', value='Mutes a specific User.', inline=False)
    embed.add_field(name='m!unmute', value='Unmutes a specific User.', inline=False)
    embed.add_field(name='m!clear', value='Clears messages.', inline=False)
    embed.add_field(name='m!kick', value='Kicks a specific User.', inline=False)
    embed.add_field(name='m!ban', value='Bans a specific User.', inline=False)
    embed.add_field(name='m!unban', value='Unbans a specific User.', inline=False)
    embed.add_field(name='m!ping', value='Returns Pong!', inline=False)

    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def claim(ctx):
    embed = discord.Embed(title=f'Ticket has been claimed.',
                          description=f'The Ticket has been claimed by a Staff Member.', color=discord.Colour.red())
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def addrole(ctx, role: discord.Role, member: discord.Member):
    await member.add_roles(role)
    embed = discord.Embed(title=f'Successfully given a role.',
                          description=f'I have successfully added {member.mention} the role {role.mention}.',
                          color=discord.Colour.red())
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def removerole(ctx, role: discord.Role, member: discord.Member):
    await member.remove_roles(role)
    embed = discord.Embed(title=f'Successfully removed a role.',
                          description=f'I have successfully removed {member.mention} the role {role.mention}.',
                          color=discord.Colour.red())
    await ctx.send(embed=embed)


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

    await ctx.send(f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}.")


@bot.command()
@commands.has_permissions(administrator=True)
async def warnings(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")

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
@commands.has_permissions(administrator=True)
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
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')


@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')

@warnings.error
async def warnings_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title=f"Oh no! An error occured!", description=f"Sorry, but you do not have permission to use this command!", color=discord.Colour.red())
        await ctx.send(embed=embed)

@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title=f"Oh no! An error occured!", description=f"Sorry, but you do not have permission to use this command!", color=discord.Colour.red())
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def mute(ctx, member: discord.Member = None):
    role = discord.utils.get(ctx.guild.roles, name='Muted')
    if not member:
        await ctx.send('Please specify a member!')
        return
    await member.add_roles(role)
    embed = discord.Embed(title=f"Successfully muted {member.mention}",
                          description=f"I have successfully muted {member.mention}!", color=discord.Colour.red())
    await ctx.send(embed=embed)

@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title=f"Oh no! An error occured!", description=f"Sorry, but you do not have permission to use this command!", color=discord.Colour.red())
        await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def unmute(ctx, member: discord.Member = None):
    role = discord.utils.get(ctx.guild.roles, name='Muted')
    if not member:
        await ctx.send('Please specify a member!')
        return
    await member.remove_roles(role)
    embed = discord.Embed(title=f"Successfully unmuted {member.mention}",
                          description=f"I have successfully unmuted {member.mention}!", color=discord.Colour.red())
    await ctx.send(embed=embed)

@unmute.error
async def unmute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title=f"Oh no! An error occured!", description=f"Sorry, but you do not have permission to use this command!", color=discord.Colour.red())
        await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount=0):
    if (ctx.message.author.permissions_in(ctx.message.channel).manage_messages):
        await ctx.channel.purge(limit=amount + 1)


@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title=f"Oh no! An Error occured!",
                              description=f"Sorry, but you do not have permissions to use this command!",
                              color=discord.Colour.red())
        await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    embed = discord.Embed(title=f"Successfully kicked {member.mention}",
                          description=f"I have successfully kicked a user for you, thanks for holding our Discord clean!",
                          color=discord.Colour.red())
    await ctx.send(embed=embed)


@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title=f"Oh no! An Error occured!",
                              description=f"Sorry, but you do not have permissions to use this command!",
                              color=discord.Colour.red())
        await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    embed = discord.Embed(title="Successfully kicked {member.mention}",
                          description=f"I have successfully kicked a user for you, thanks for holding our Discord clean!",
                          color=discord.Colour.red())
    await ctx.send(embed=embed)


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title=f"Oh no! An Error occured!",
                              description=f"Sorry, but you do not have permissions to use this command!",
                              color=discord.Colour.red())
        await ctx.send(embed=embed)

@bot.event
async def on_member_join(member):
    await bot.get_channel(800995020265881604).send(f"Hey, {member.mention}! Please read the rules carefully and check the checkmark to gain access to the rest of the Server!")

@bot.event
async def on_member_remove(member):
    await bot.get_channel(800995020265881604).send(f"{member.mention} has left our Server! :(")


@bot.command()
@commands.has_permissions(administrator=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            embed = discord.Embed(title=f"Successfully unbanned a user!",
                                  description=f"I have successfully unbanned a user for you!")
            await ctx.send(embed=embed)
            return


@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title=f"Oh no! An Error occured!",
                              description=f"Sorry, but you do not have permissions to use this command!",
                              color=discord.Colour.red())


@bot.command()
async def ping(ctx):
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

keep_alive.keep_alive()
token = os.environ['bot_token']
bot.run(token)