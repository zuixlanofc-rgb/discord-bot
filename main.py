import discord
from discord.ext import commands
import json
import os
import random
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

CONFIG_FILE = 'bot_config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# WELCOME SYSTEM
@bot.event
async def on_member_join(member):
    config = load_config()
    guild_id = str(member.guild.id)
    
    if guild_id not in config or 'welcome_channel' not in config[guild_id]:
        return
    
    channel_id = config[guild_id]['welcome_channel']
    channel = bot.get_channel(channel_id)
    
    if not channel:
        return
    
    members = [m for m in member.guild.members if not m.bot]
    random_members = random.sample(members, min(5, len(members)))
    mentions = ' '.join([m.mention for m in random_members])
    
    embed = discord.Embed(
        title=f"Bem-vindo, {member.name}!",
        description=f"Olá {member.mention}, bem-vindo ao servidor!\n\nMembros para conhecer: {mentions}",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.set_footer(text=f"ID: {member.id}")
    
    msg = await channel.send(embed=embed)
    await msg.delete(delay=120)

# SETUP COMMANDS
@bot.command(name='setupDA')
@commands.has_permissions(administrator=True)
async def setupDA(ctx):
    config = load_config()
    guild_id = str(ctx.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    config[guild_id]['welcome_channel'] = ctx.channel.id
    save_config(config)
    
    embed = discord.Embed(
        title="Canal de Boas-vindas Configurado",
        description=f"Mensagens de boas-vindas serão enviadas em {ctx.channel.mention}",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='removecanal')
@commands.has_permissions(administrator=True)
async def removecanal(ctx):
    config = load_config()
    guild_id = str(ctx.guild.id)
    
    if guild_id in config and 'welcome_channel' in config[guild_id]:
        del config[guild_id]['welcome_channel']
        save_config(config)
        embed = discord.Embed(
            title="Canal Removido",
            description="O canal de boas-vindas foi removido.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("Nenhum canal configurado.")

@bot.command(name='statusDA')
async def statusDA(ctx):
    config = load_config()
    guild_id = str(ctx.guild.id)
    
    embed = discord.Embed(
        title="Status do Bot",
        description="Bot está online e funcionando!",
        color=discord.Color.green()
    )
    embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)}ms", inline=False)
    embed.add_field(name="Servidores", value=len(bot.guilds), inline=False)
    
    if guild_id in config and 'welcome_channel' in config[guild_id]:
        channel = bot.get_channel(config[guild_id]['welcome_channel'])
        embed.add_field(name="Canal de Boas-vindas", value=channel.mention if channel else "Canal não encontrado", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='bothelp')
async def bothelp(ctx):
    embed = discord.Embed(
        title="Comandos do Bot",
        description="Lista de todos os comandos disponíveis",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🎉 Boas-vindas",
        value="```!setupDA - Configurar canal de boas-vindas\n!removecanal - Remover canal de boas-vindas\n!statusDA - Status do bot\n!bothelp - Este comando```",
        inline=False
    )

    await ctx.send(embed=embed)

# BOT EVENTS
@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="!bothelp"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Permissão Negada",
            description="Você não tem permissão para usar este comando.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Argumento Faltando",
            description=f"Uso correto: `{ctx.command.qualified_name} {ctx.command.signature}`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        print(f"Erro: {error}")

bot.run(TOKEN)
