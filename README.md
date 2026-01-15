# WoW Raid Stats PowerPoint Automation

Automated weekly PowerPoint generation for guild raid statistics using WarcraftLogs, Raider.IO, and other APIs.

## Features

- Fetches raid data from WarcraftLogs API
- Stores historical data in SQLite database
- Generates professional PowerPoint presentations
- Posts to Discord automatically
- Runs on GitHub Actions (free tier)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
npm install -g pptxgenjs playwright
playwright install chromium
```

### 2. Configure API Keys

Create a `.env` file:

```env
# WarcraftLogs API (get from https://www.warcraftlogs.com/api/clients/)
WARCRAFTLOGS_CLIENT_ID=your_client_id
WARCRAFTLOGS_CLIENT_SECRET=your_client_secret

# Raider.IO (optional - public API, no key needed for basic data)
# RAIDERIO_API_KEY=your_key

# Discord Bot (get from https://discord.com/developers/applications)
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=your_channel_id

# Your Guild Info
GUILD_NAME=YourGuildName
GUILD_REALM=YourRealm
GUILD_REGION=us  # us, eu, kr, tw, cn
```

### 3. Run Locally

```bash
# Fetch latest raid data and generate PowerPoint
python main.py

# Post to Discord
python discord_bot.py
```

### 4. Setup GitHub Actions (Optional)

1. Fork this repo
2. Add secrets in repo settings (Settings → Secrets → Actions):
   - `WARCRAFTLOGS_CLIENT_ID`
   - `WARCRAFTLOGS_CLIENT_SECRET`
   - `DISCORD_BOT_TOKEN`
   - `DISCORD_CHANNEL_ID`
3. Edit `.github/workflows/weekly-stats.yml` to set your guild info
4. The workflow runs every Monday at 6 PM (configurable)

## Project Structure

```
wow-raid-stats-automation/
├── main.py                 # Main orchestration script
├── fetch_data.py          # API data fetching
├── database.py            # SQLite database operations
├── generate_pptx.py       # PowerPoint generation
├── discord_bot.py         # Discord posting
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── raid_stats.db          # SQLite database (auto-created)
├── slides/                # Generated HTML slides (temp)
├── output/                # Generated PowerPoint files
└── .github/workflows/     # GitHub Actions config
```

## Customization

### Slide Templates

Edit `generate_pptx.py` to customize:
- Color scheme (CSS variables)
- Slide layouts
- Data visualizations
- Statistics displayed

### Data Sources

Currently supports:
- **WarcraftLogs**: Boss kills, wipes, DPS/HPS rankings, parse percentiles
- **Raider.IO**: Mythic+ scores (can be added)

To add more sources, extend `fetch_data.py`.

## Example Output

The generated PowerPoint includes:
1. **Title Slide**: Guild name, raid week dates
2. **Week Summary**: Total bosses killed, wipes, raid time
3. **Boss Breakdown**: Kill times, attempt counts per boss
4. **Top Performers**: DPS, HPS, and top parsers
5. **Improvement Areas**: Deaths, mechanics failures

## Troubleshooting

**"No data found"**: Check your guild name/realm are correct and you have recent raid logs
**API errors**: Verify your WarcraftLogs API credentials
**Discord bot issues**: Ensure bot has "Send Messages" and "Attach Files" permissions

## Contributing

PRs welcome! Especially for:
- Additional API integrations (WipeFest, Archon)
- More chart types and visualizations
- Better error handling
