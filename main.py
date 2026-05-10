import discord
from discord.ext import commands
import json
import os
import random
from datetime import datetime
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
WARNINGS_FILE = 'warnings.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_warnings():
    if os.path.exists(WARNINGS_FILE):
        with open(WARNINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_warnings(warnings):
    with open(WARNINGS_FILE, 'w') as f:
        json.dump(warnings, f, indent=2)

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

# MODERATION COMMANDS
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sem motivo"):
    if member == ctx.author:
        await ctx.send("❌ Você não pode expulsar a si mesmo!")
        return
    
    await member.kick(reason=reason)
    embed = discord.Embed(
        title="Membro Expulso",
        description=f"{member.mention} foi expulso.\n**Motivo:** {reason}",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Sem motivo"):
    if member == ctx.author:
        await ctx.send("❌ Você não pode banir a si mesmo!")
        return
    
    await member.ban(reason=reason)
    embed = discord.Embed(
        title="Membro Banido",
        description=f"{member.mention} foi banido permanentemente.\n**Motivo:** {reason}",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@bot.command(name='warn')
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="Sem motivo"):
    warnings = load_warnings()
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
    
    if guild_id not in warnings:
        warnings[guild_id] = {}
    if user_id not in warnings[guild_id]:
        warnings[guild_id][user_id] = []
    
    warnings[guild_id][user_id].append({
        'reason': reason,
        'date': datetime.now().isoformat(),
        'moderator': str(ctx.author)
    })
    
    warn_count = len(warnings[guild_id][user_id])
    save_warnings(warnings)
    
    embed = discord.Embed(
        title="Aviso Registrado",
        description=f"{member.mention} recebeu um aviso.\n**Motivo:** {reason}\n**Total de avisos:** {warn_count}/3",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)
    
    if warn_count >= 3:
        await member.ban(reason="Banido automaticamente após 3 avisos")
        embed = discord.Embed(
            title="Banimento Automático",
            description=f"{member.mention} foi banido automaticamente após 3 avisos.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command(name='limpar')
@commands.has_permissions(manage_messages=True)
async def limpar(ctx, amount: int = 10):
    if amount < 1 or amount > 100:
        await ctx.send("❌ Digite um número entre 1 e 100!")
        return
    
    deleted = await ctx.channel.purge(limit=amount)
    embed = discord.Embed(
        title="Mensagens Deletadas",
        description=f"{len(deleted)} mensagens foram deletadas.",
        color=discord.Color.blue()
    )
    msg = await ctx.send(embed=embed)
    await msg.delete(delay=5)

@bot.command(name='avisos')
async def avisos(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    warnings = load_warnings()
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
    
    if guild_id not in warnings or user_id not in warnings[guild_id]:
        await ctx.send(f"{member.mention} não possui avisos.")
        return
    
    user_warnings = warnings[guild_id][user_id]
    embed = discord.Embed(
        title=f"Avisos de {member.name}",
        description=f"Total: {len(user_warnings)}/3",
        color=discord.Color.orange()
    )
    
    for i, warn in enumerate(user_warnings, 1):
        embed.add_field(
            name=f"Aviso #{i}",
            value=f"**Motivo:** {warn['reason']}\n**Moderador:** {warn['moderator']}\n**Data:** {warn['date']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='limparavisos')
@commands.has_permissions(administrator=True)
async def limparavisos(ctx, member: discord.Member):
    warnings = load_warnings()
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
    
    if guild_id in warnings and user_id in warnings[guild_id]:
        del warnings[guild_id][user_id]
        save_warnings(warnings)
        embed = discord.Embed(
            title="Avisos Limpos",
            description=f"Avisos de {member.mention} foram removidos.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{member.mention} não possui avisos.")

@bot.command(name='autorizar')
@commands.has_permissions(administrator=True)
async def autorizar(ctx, role: discord.Role):
    config = load_config()
    guild_id = str(ctx.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    if 'mod_roles' not in config[guild_id]:
        config[guild_id]['mod_roles'] = []
    
    if role.id not in config[guild_id]['mod_roles']:
        config[guild_id]['mod_roles'].append(role.id)
        save_config(config)
        embed = discord.Embed(
            title="Role Autorizada",
            description=f"{role.mention} foi autorizada para moderação.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{role.mention} já está autorizada.")

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

# UTILITY COMMANDS
@bot.command(name='userinfo')
async def userinfo(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    embed = discord.Embed(
        title=f"Informações de {member.name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(name="Conta criada em", value=member.created_at.strftime("%d/%m/%Y"), inline=False)
    embed.add_field(name="Entrou no servidor em", value=member.joined_at.strftime("%d/%m/%Y"), inline=False)
    embed.add_field(name="Roles", value=', '.join([r.mention for r in member.roles[1:]]) or "Nenhuma", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='serverinfo')
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"Informações de {guild.name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="ID", value=guild.id, inline=False)
    embed.add_field(name="Dono", value=guild.owner.mention, inline=False)
    embed.add_field(name="Membros", value=guild.member_count, inline=False)
    embed.add_field(name="Canais", value=len(guild.channels), inline=False)
    embed.add_field(name="Roles", value=len(guild.roles), inline=False)
    embed.add_field(name="Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
    
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
        value="```!setupDA - Configurar canal de boas-vindas\n!removecanal - Remover canal\n!statusDA - Status do bot```",
        inline=False
    )
    
    embed.add_field(
        name="⚔️ Moderação",
        value="```!kick @user [motivo] - Expulsar membro\n!ban @user [motivo] - Banir membro\n!warn @user [motivo] - Avisar membro\n!limpar [quantidade] - Deletar mensagens\n!avisos @user - Ver avisos\n!limparavisos @user - Limpar avisos (Admin)\n!autorizar @role - Autorizar role (Admin)```",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Utilidade",
        value="```!userinfo [@user] - Info do membro\n!serverinfo - Info do servidor\n!bothelp - Este comando```",
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
