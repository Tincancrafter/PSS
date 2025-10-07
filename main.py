import csv
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import time

# Note: needs member intent enabled!
Channel_to_track=1181015018578382858
times = {}
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
    data = [["ID", "Total Time", "Longest Session"]]
    for member in guild.members:
        data.append([member.id, 0, 0])
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
def format_time(seconds):
    """Convert seconds to a readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"
##############################################################################
def update_user_time(user_id, session_duration):
    # Read the existing CSV
    data = []
    with open("data.csv", mode="r", newline="") as file:
        reader = csv.reader(file)
        data = list(reader)
    
    found = False
    for row in data[1:]:  # Skip header row
        if int(row[0]) == user_id:
            row[1] = float(row[1]) + session_duration  # Add to total time
            row[2] = max(float(row[2]), session_duration)  # Update longest session if needed
            found = True
            break
    
    if not found:
        data.append([user_id, session_duration, session_duration])
    
    with open("data.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(data)
    
    print(f"Updated CSV for user {user_id}")

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
    if after.channel and after.channel.id == Channel_to_track:
        times[member.id] = time.time()
        print(f"{member.name} ({member.id}) has joined the call")
    
    # User left the tracked channel
    if before.channel and before.channel.id == Channel_to_track and (not after.channel or after.channel.id != Channel_to_track):
        if member.id in times:
            session = time.time() - times[member.id]
            print(f"{member.name} was in call for {session} seconds")
            update_user_time(member.id, session)
            del times[member.id]

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
bot.run(token)