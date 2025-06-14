import discord
from discord.ext import commands
from discord.utils import get
import sqlite3

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# SQLite database setup
conn = sqlite3.connect('clans.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS clans (name TEXT PRIMARY KEY, owner_id INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS clan_members (clan_name TEXT, user_id INTEGER, FOREIGN KEY(clan_name) REFERENCES clans(name))''')
conn.commit()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def clan_create(ctx, *, clan_name):
    guild = ctx.guild
    category = get(guild.categories, name="Clans")
    if not category:
        category = await guild.create_category("Clans")

    c.execute("SELECT * FROM clans WHERE name = ?", (clan_name,))
    if c.fetchone():
        await ctx.send("Clan name already taken.")
        return

    c.execute("INSERT INTO clans (name, owner_id) VALUES (?, ?)", (clan_name, ctx.author.id))
    c.execute("INSERT INTO clan_members (clan_name, user_id) VALUES (?, ?)", (clan_name, ctx.author.id))
    conn.commit()

    clan_channel = await guild.create_text_channel(clan_name, category=category)
    await clan_channel.set_permissions(ctx.guild.default_role, read_messages=False)
    await clan_channel.set_permissions(ctx.author, read_messages=True, send_messages=True)

    await ctx.send(f"Clan '{clan_name}' created and channel setup complete.")

@bot.command()
async def clan_invite(ctx, member: discord.Member):
    c.execute("SELECT clan_name FROM clan_members WHERE user_id = ?", (ctx.author.id,))
    result = c.fetchone()
    if not result:
        await ctx.send("You're not in a clan.")
        return

    clan_name = result[0]
    c.execute("INSERT INTO clan_members (clan_name, user_id) VALUES (?, ?)", (clan_name, member.id))
    conn.commit()

    clan_channel = get(ctx.guild.text_channels, name=clan_name)
    if clan_channel:
        await clan_channel.set_permissions(member, read_messages=True, send_messages=True)
    await ctx.send(f"{member.mention} has been invited to clan '{clan_name}'.")

@bot.command()
async def clan_kick(ctx, member: discord.Member):
    c.execute("SELECT clan_name FROM clans WHERE owner_id = ?", (ctx.author.id,))
    result = c.fetchone()
    if not result:
        await ctx.send("You are not the owner of a clan.")
        return

    clan_name = result[0]
    c.execute("DELETE FROM clan_members WHERE clan_name = ? AND user_id = ?", (clan_name, member.id))
    conn.commit()

    clan_channel = get(ctx.guild.text_channels, name=clan_name)
    if clan_channel:
        await clan_channel.set_permissions(member, overwrite=None)

    await ctx.send(f"{member.mention} has been kicked from '{clan_name}'.")

@bot.command()
async def clan_leave(ctx):
    user_id = ctx.author.id
    c.execute("SELECT clan_name FROM clan_members WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if not result:
        await ctx.send("You're not in a clan.")
        return

    clan_name = result[0]
    c.execute("DELETE FROM clan_members WHERE user_id = ?", (user_id,))
    conn.commit()

    clan_channel = get(ctx.guild.text_channels, name=clan_name)
    if clan_channel:
        await clan_channel.set_permissions(ctx.author, overwrite=None)

    await ctx.send(f"You left the clan '{clan_name}'.")

@bot.command()
async def clan_disband(ctx):
    user_id = ctx.author.id
    c.execute("SELECT name FROM clans WHERE owner_id = ?", (user_id,))
    result = c.fetchone()
    if not result:
        await ctx.send("You're not the owner of any clan.")
        return

    clan_name = result[0]
    c.execute("DELETE FROM clans WHERE name = ?", (clan_name,))
    c.execute("DELETE FROM clan_members WHERE clan_name = ?", (clan_name,))
    conn.commit()

    clan_channel = get(ctx.guild.text_channels, name=clan_name)
    if clan_channel:
        await clan_channel.delete()

    await ctx.send(f"Clan '{clan_name}' has been disbanded.")

@bot.command()
async def clan_list(ctx):
    c.execute("SELECT name FROM clans")
    clans = c.fetchall()
    if not clans:
        await ctx.send("No clans created yet.")
        return

    clan_names = ", ".join([clan[0] for clan in clans])
    await ctx.send(f"Clans: {clan_names}")

bot.run('YOUR_BOT_TOKEN')
