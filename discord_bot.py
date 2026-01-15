"""Discord bot to post the weekly raid stats PowerPoint."""
import os
import discord
from discord.ext import commands
import config

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Bot startup event."""
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='raidstats')
async def post_raid_stats(ctx):
    """Post the latest raid stats presentation."""
    # Find the most recent PowerPoint file
    output_dir = config.OUTPUT_DIR
    
    if not os.path.exists(output_dir):
        await ctx.send("No raid stats found. Please generate the presentation first.")
        return
    
    files = [f for f in os.listdir(output_dir) if f.endswith('.pptx')]
    
    if not files:
        await ctx.send("No raid stats found. Please generate the presentation first.")
        return
    
    # Get most recent file
    latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(output_dir, f)))
    filepath = os.path.join(output_dir, latest_file)
    
    # Send the file
    await ctx.send(
        f"📊 **{config.GUILD_NAME} Weekly Raid Stats**\n"
        f"Here's this week's performance breakdown!",
        file=discord.File(filepath)
    )

async def post_to_channel(filepath=None):
    """Post raid stats to configured channel."""
    if not config.DISCORD_BOT_TOKEN or not config.DISCORD_CHANNEL_ID:
        print("Discord configuration missing. Skipping Discord post.")
        return
    
    # Get the most recent file if not specified
    if filepath is None:
        output_dir = config.OUTPUT_DIR
        files = [f for f in os.listdir(output_dir) if f.endswith('.pptx')]
        if not files:
            print("No presentation files found.")
            return
        latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(output_dir, f)))
        filepath = os.path.join(output_dir, latest_file)
    
    # Connect to Discord
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        channel = client.get_channel(int(config.DISCORD_CHANNEL_ID))
        if channel:
            await channel.send(
                f"📊 **{config.GUILD_NAME} Weekly Raid Stats**\n"
                f"This week's performance breakdown is ready!",
                file=discord.File(filepath)
            )
            print(f"Posted raid stats to Discord channel {config.DISCORD_CHANNEL_ID}")
        else:
            print(f"Could not find channel {config.DISCORD_CHANNEL_ID}")
        
        await client.close()
    
    await client.start(config.DISCORD_BOT_TOKEN)

if __name__ == '__main__':
    import sys
    import asyncio
    
    if len(sys.argv) > 1 and sys.argv[1] == 'post':
        # Direct posting mode
        asyncio.run(post_to_channel())
    else:
        # Bot mode (for interactive use)
        bot.run(config.DISCORD_BOT_TOKEN)
