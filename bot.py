import discord
from discord.ext import tasks
import mysql.connector
import asyncio

# Bot Configuration
intents = discord.Intents.default()
intents.guilds = True
bot = discord.Client(intents=intents)

# Discord Channel ID
announcement_channel_id = 123456789012345678  # Replace with your channel ID

# Database Configuration
db_config_auth = {
    'host': 'localhost',  # Replace with your DB host if needed
    'user': 'your_user',  # Replace with your DB username
    'password': 'your_password',  # Replace with your DB password
    'database': 'acore_auth'
}
db_config_characters = {
    'host': 'localhost',  # Replace with your DB host if needed
    'user': 'your_user',  # Replace with your DB username
    'password': 'your_password',  # Replace with your DB password
    'database': 'acore_characters'
}

# Database Connection
db_auth = mysql.connector.connect(**db_config_auth)
db_characters = mysql.connector.connect(**db_config_characters)

last_account_id = None  # Track the last processed account ID

# Update Bot Status
@tasks.loop(minutes=1)
async def update_status():
    try:
        cursor = db_characters.cursor()
        cursor.execute("SELECT COUNT(*) FROM characters WHERE online = 1;")
        result = cursor.fetchone()
        population = result[0] if result else 0
        print(f"Updating status: {population} players online.")
        await bot.change_presence(
            activity=discord.Game(name=f"{population} players online")
        )
    except Exception as e:
        print(f"Error updating status: {e}")

# Announce New Accounts
@tasks.loop(seconds=30)
async def check_new_accounts():
    global last_account_id, db_auth

    try:
        cursor = db_auth.cursor()
        cursor.execute("""
            SELECT id, username
            FROM account
            WHERE email != '' AND username NOT LIKE 'bot%'
            ORDER BY id DESC LIMIT 1;
        """)
        result = cursor.fetchone()

        print(f"Raw query result: {result}")  # Debugging

        if result:
            account_id, username = result
            if last_account_id is None or account_id > last_account_id:
                last_account_id = account_id
                channel = bot.get_channel(announcement_channel_id)
                if channel:
                    await channel.send(f"🎉 New account registered: {username} 🎉")
                    print(f"Announced new account: {username}")
                else:
                    print("Error: Channel not found.")

        # Refresh the database connection
        cursor.close()
        db_auth.close()
        db_auth = mysql.connector.connect(**db_config_auth)

    except Exception as e:
        print(f"Error checking new accounts: {e}")

# Bot Events
@bot.event
async def on_ready():
    global last_account_id
    print(f"Logged in as {bot.user}")
    try:
        cursor = db_auth.cursor()
        cursor.execute("""
            SELECT MAX(id)
            FROM account
            WHERE email != '' AND username NOT LIKE 'bot%';
        """)
        result = cursor.fetchone()
        last_account_id = result[0] if result and result[0] else 0
        print(f"Initialized last_account_id: {last_account_id}")
        check_new_accounts.start()
        update_status.start()
    except Exception as e:
        print(f"Error initializing bot: {e}")

# Run the Bot
bot.run("YOUR_BOT_TOKEN")  # Replace with your bot token
