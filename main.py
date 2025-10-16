import csv
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import time

# Note: needs member intent enabled!
Channel_to_track=1181015018578382858
Rust_Channel=1216171491947843684
times = {}
rust_times = {}  # Track Rust channel sessions separately
##############################################################################
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Create your bot instance with intents
intents = discord.Intents.default()
intents.members = True  # Required to access guild.members
intents.voice_states = True  # Required for voice tracking
bot = commands.Bot(command_prefix='!', intents=intents)

##############################################################################
def buildCSV(guild):  # Changed from ctx to guild
    data = [["ID", "Total Time", "Longest Session", "Rust Total Time", "Rust Longest Session"]]
    for member in guild.members:
        data.append([member.id, 0, 0, 0, 0])
    with open("data.csv", mode="w", newline="") as file:
        write = csv.writer(file)
        write.writerows(data)
##############################################################################
def Leaderboard_Total():
    data = []
    lb = {}
    
    with open("data.csv", mode="r", newline="") as file:
        reader = csv.reader(file)
        data = list(reader)
    
    # Sort rows by total time (column 1), greatest to least
    sorted_rows = sorted(data[1:], key=lambda row: float(row[1]), reverse=True)
    
    # Build leaderboard dictionary, skipping users with 0 time
    for row in sorted_rows:
        user_id = int(row[0])
        total_time = float(row[1])
        
        if total_time > 0:  # Ignore 0 time
            lb[user_id] = total_time
    
    return lb
##############################################################################
def Leaderboard_Longest():
    data = []
    lb = {}
    
    with open("data.csv", mode="r", newline="") as file:
        reader = csv.reader(file)
        data = list(reader)
    
    sorted_rows = sorted(data[1:], key=lambda row: float(row[2]), reverse=True)
    # Build leaderboard dictionary, skipping users with 0 time
    for row in sorted_rows:
        user_id = int(row[0])
        longest_time = float(row[2])
        
        if longest_time > 0:  # Ignore 0 time
            lb[user_id] = longest_time
    
    return lb
##############################################################################
def Leaderboard_Rust_Total():
    data = []
    lb = {}
    
    with open("data.csv", mode="r", newline="") as file:
        reader = csv.reader(file)
        data = list(reader)
    
    # Sort rows by Rust total time (column 3), greatest to least
    sorted_rows = sorted(data[1:], key=lambda row: float(row[3]) if len(row) > 3 else 0, reverse=True)
    
    # Build leaderboard dictionary, skipping users with 0 time
    for row in sorted_rows:
        user_id = int(row[0])
        rust_total_time = float(row[3]) if len(row) > 3 else 0
        
        if rust_total_time > 0:  # Ignore 0 time
            lb[user_id] = rust_total_time
    
    return lb
##############################################################################
def Leaderboard_Rust_Longest():
    data = []
    lb = {}
    
    with open("data.csv", mode="r", newline="") as file:
        reader = csv.reader(file)
        data = list(reader)
    
    sorted_rows = sorted(data[1:], key=lambda row: float(row[4]) if len(row) > 4 else 0, reverse=True)
    # Build leaderboard dictionary, skipping users with 0 time
    for row in sorted_rows:
        user_id = int(row[0])
        rust_longest_time = float(row[4]) if len(row) > 4 else 0
        
        if rust_longest_time > 0:  # Ignore 0 time
            lb[user_id] = rust_longest_time
    
    return lb
##############################################################################
def format_time(seconds):
    """Convert seconds to a readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"
##############################################################################
def update_user_time(user_id, session_duration, is_rust=False):
    # Read the existing CSV
    data = []
    with open("data.csv", mode="r", newline="") as file:
        reader = csv.reader(file)
        data = list(reader)
    
    found = False
    for row in data[1:]:  # Skip header row
        if int(row[0]) == user_id:
            # Ensure row has all columns (backwards compatibility)
            while len(row) < 5:
                row.append('0')
            
            if is_rust:
                row[3] = float(row[3]) + session_duration  # Add to Rust total time
                row[4] = max(float(row[4]), session_duration)  # Update Rust longest session
            else:
                row[1] = float(row[1]) + session_duration  # Add to total time
                row[2] = max(float(row[2]), session_duration)  # Update longest session
            found = True
            break
    
    if not found:
        if is_rust:
            data.append([user_id, 0, 0, session_duration, session_duration])
        else:
            data.append([user_id, session_duration, session_duration, 0, 0])
    
    with open("data.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(data)
    
    channel_type = "Rust channel" if is_rust else "main channel"
    print(f"Updated CSV for user {user_id} in {channel_type}")

##############################################################################
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        if os.path.exists("data.csv"):
            print("File exists!")
        else:
            buildCSV(guild)
        print(f"CSV built for {guild.name}!")
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

##############################################################################
@bot.event
async def on_voice_state_update(member, before, after):
    # User joined the tracked channel
    if after.channel and after.channel.id == Channel_to_track and (before.channel is None or before.channel.id != Channel_to_track):
        times[member.id] = time.time()
        print(f"{member.name} ({member.id}) has joined the call")
    # User left the tracked channel
    if before.channel and before.channel.id == Channel_to_track and (not after.channel or after.channel.id != Channel_to_track):
        if member.id in times:
            session = time.time() - times[member.id]
            print(f"{member.name} was in call for {session} seconds")
            update_user_time(member.id, session, is_rust=False)
            del times[member.id]
    
    # User joined the Rust channel
    if after.channel and after.channel.id == Rust_Channel and (before.channel is None or before.channel.id != Rust_Channel):
        rust_times[member.id] = time.time()
        print(f"{member.name} ({member.id}) has joined the Rust channel")
    # User left the Rust channel
    if before.channel and before.channel.id == Rust_Channel and (not after.channel or after.channel.id != Rust_Channel):
        if member.id in rust_times:
            session = time.time() - rust_times[member.id]
            print(f"{member.name} was in Rust channel for {session} seconds")
            update_user_time(member.id, session, is_rust=True)
            del rust_times[member.id]
##############################################################################
# Slash command for total time leaderboard
@bot.tree.command(name="leaderboard_total", description="Show the total time leaderboard")
async def leaderboard_total(interaction: discord.Interaction):
    lb = Leaderboard_Total()
    
    if not lb:
        await interaction.response.send_message("No data available yet! No one has spent time in the tracked channel.")
        return
    
    # Create embed
    embed = discord.Embed(
        title="🏆 Total Goon Time Leaderboard",
        description="Users ranked by total time in voice channel",
        color=discord.Color.gold()
    )
    
    # Add top 10 users
    for i, (user_id, total_time) in enumerate(list(lb.items())[:10], 1):
        user = await bot.fetch_user(user_id)
        embed.add_field(
            name=f"{i}. {user.name}",
            value=f"⏱️ {format_time(total_time)}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

##############################################################################
# Slash command for longest session leaderboard
@bot.tree.command(name="leaderboard_longest", description="Show the longest session leaderboard")
async def leaderboard_longest(interaction: discord.Interaction):
    lb = Leaderboard_Longest()
    
    if not lb:
        await interaction.response.send_message("No data available yet! No one has spent time in the tracked channel.")
        return
    
    # Create embed
    embed = discord.Embed(
        title="🏆 Longest Goon Session Leaderboard",
        description="Users ranked by longest single session",
        color=discord.Color.blue()
    )
    
    # Add top 10 users
    for i, (user_id, longest_time) in enumerate(list(lb.items())[:10], 1):
        user = await bot.fetch_user(user_id)
        embed.add_field(
            name=f"{i}. {user.name}",
            value=f"⏱️ {format_time(longest_time)}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

##############################################################################
# Slash command for Rust total time leaderboard
@bot.tree.command(name="leaderboard_rust_total", description="Show the Rust channel total time leaderboard")
async def leaderboard_rust_total(interaction: discord.Interaction):
    lb = Leaderboard_Rust_Total()
    
    if not lb:
        await interaction.response.send_message("No data available yet! No one has spent time in the Rust channel.")
        return
    
    # Create embed
    embed = discord.Embed(
        title="🦀 Rust Channel Total Time Leaderboard",
        description="Users ranked by total time in Rust channel",
        color=discord.Color.orange()
    )
    
    # Add top 10 users
    for i, (user_id, total_time) in enumerate(list(lb.items())[:10], 1):
        user = await bot.fetch_user(user_id)
        embed.add_field(
            name=f"{i}. {user.name}",
            value=f"⏱️ {format_time(total_time)}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

##############################################################################
# Slash command for Rust longest session leaderboard
@bot.tree.command(name="leaderboard_rust_longest", description="Show the Rust channel longest session leaderboard")
async def leaderboard_rust_longest(interaction: discord.Interaction):
    lb = Leaderboard_Rust_Longest()
    
    if not lb:
        await interaction.response.send_message("No data available yet! No one has spent time in the Rust channel.")
        return
    
    # Create embed
    embed = discord.Embed(
        title="🦀 Rust Channel Longest Session Leaderboard",
        description="Users ranked by longest single session in Rust channel",
        color=discord.Color.red()
    )
    
    # Add top 10 users
    for i, (user_id, longest_time) in enumerate(list(lb.items())[:10], 1):
        user = await bot.fetch_user(user_id)
        embed.add_field(
            name=f"{i}. {user.name}",
            value=f"⏱️ {format_time(longest_time)}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

##############################################################################
bot.run(token)