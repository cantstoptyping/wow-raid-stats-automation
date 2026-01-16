"""Configuration management for WoW raid stats automation."""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
WARCRAFTLOGS_CLIENT_ID = os.getenv('WARCRAFTLOGS_CLIENT_ID')
WARCRAFTLOGS_CLIENT_SECRET = os.getenv('WARCRAFTLOGS_CLIENT_SECRET')
WARCRAFTLOGS_API_URL = 'https://www.warcraftlogs.com/api/v2/client'

# Guild Configuration
GUILD_NAME = os.getenv('GUILD_NAME', 'YourGuild')
GUILD_REALM = os.getenv('GUILD_REALM', 'YourRealm')
GUILD_REGION = os.getenv('GUILD_REGION', 'us')  # us, eu, kr, tw, cn

# Discord Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

# Database Configuration
DATABASE_PATH = 'raid_stats.db'

# Output Configuration
OUTPUT_DIR = 'output'
SLIDES_DIR = 'slides'

# Presentation Configuration
PRESENTATION_TITLE = f'{GUILD_NAME} Weekly Raid Stats'
PRESENTATION_SUBTITLE = 'Performance Analysis & Top Performers'

# difficulty filter to filter out any non mythic logs
DIFFICULTY_FILTER = os.getenv('DIFFICULTY_FILTER', None)
if DIFFICULTY_FILTER:
    DIFFICULTY_FILTER = int(DIFFICULTY_FILTER)

def validate_config():
    """Validate that required configuration is present."""
    required = {
        'WARCRAFTLOGS_CLIENT_ID': WARCRAFTLOGS_CLIENT_ID,
        'WARCRAFTLOGS_CLIENT_SECRET': WARCRAFTLOGS_CLIENT_SECRET,
        'GUILD_NAME': GUILD_NAME,
        'GUILD_REALM': GUILD_REALM,
    }
    
    missing = [key for key, value in required.items() if not value]
    
    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")
    
    return True
