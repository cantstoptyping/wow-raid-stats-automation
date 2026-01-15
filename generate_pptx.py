"""Generate PowerPoint presentations from raid statistics."""
import os
import json
from datetime import datetime, timedelta
import database
import config

def get_logo_html():
    """Get HTML for guild logo."""
    # Check if logo exists
    import os
    logo_path = 'guild-logo.webp'
    if os.path.exists(logo_path):
        return '<img src="../guild-logo.webp" style="width: 80px; height: 80px; object-fit: contain;">'
    return ''

def get_week_range():
    """Get the start and end timestamps for the previous week."""
    today = datetime.now()
    week_start = today - timedelta(days=7)
    
    return int(week_start.timestamp() * 1000), int(today.timestamp() * 1000)

def format_duration(milliseconds):
    """Format milliseconds into MM:SS."""
    seconds = int(milliseconds / 1000)
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

def create_shared_css():
    """Create shared CSS file with WoW-themed design system."""
    css_content = """
:root {
  /* WoW-inspired color palette - Horde red and gold theme */
  --color-primary: #32CD32;  /* Deep red */
  --color-primary-foreground: #ffffff;
  --color-secondary: #D4AF37;  /* Gold */
  --color-secondary-foreground: #1d1d1d;
  --color-accent: #2C1810;  /* Dark brown */
  --color-accent-foreground: #ffffff;
  --color-surface: #1a1a1a;  /* Dark background */
  --color-surface-foreground: #f5f5f5;
  --color-muted: #2d2d2d;
  --color-muted-foreground: #a0a0a0;
  --color-border: #404040;
  
  /* Typography - Bold and impactful */
  --font-family-display: 'Arial Black', Arial, sans-serif;
  --font-weight-display: 900;
  --font-family-content: Arial, sans-serif;
  --font-weight-content: 400;
  --font-size-content: 14px;
  
  /* Spacing */
  --gap: 12px;
  --radius: 4px;
}
"""
    
    os.makedirs(config.SLIDES_DIR, exist_ok=True)
    with open(os.path.join(config.SLIDES_DIR, 'shared.css'), 'w') as f:
        f.write(css_content)

def create_title_slide(week_start, week_end):
    """Create the title slide."""
    start_date = datetime.fromtimestamp(week_start / 1000).strftime('%B %d')
    end_date = datetime.fromtimestamp(week_end / 1000).strftime('%B %d, %Y')
    
    logo_html = get_logo_html()

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body class="col bg-surface center" style="width: 960px; height: 540px; position: relative;">
    <!-- Logo in top right -->
    <div style="position: absolute; top: 20px; right: 20px;">
        {logo_html}
    </div>
    
    <div class="text-center">
        <h1 class="text-8xl text-primary" style="margin: 0 0 20px 0; letter-spacing: 2px; text-transform: uppercase;">
            {config.GUILD_NAME}
        </h1>
        <div class="text-4xl text-secondary" style="margin: 0 0 16px 0; font-weight: bold;">
            Weekly Raid Report
        </div>
        <div class="text-2xl text-surface-foreground" style="margin: 0;">
            {start_date} - {end_date}
        </div>
    </div>
    <div style="position: absolute; bottom: 20px; left: 20px; right: 20px;">
        <div class="text-xs text-muted-foreground text-center">
            Prepared by Raid Leadership - Data from WarcraftLogs
        </div>
    </div>
</body>
</html>"""
    
    with open(os.path.join(config.SLIDES_DIR, 'slide1.html'), 'w') as f:
        f.write(html)

def create_summary_slide(summary):
    """Create weekly summary slide."""
    logo_html = get_logo_html()
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body class="col bg-surface" style="width: 960px; height: 540px; position: relative;">
    <!-- Logo in top right -->
    <div style="position: absolute; top: 20px; right: 20px; z-index: 100;">
        {logo_html}
    </div>
    <div style="width: 920px; margin: 0 20px; padding-top: 20px;" class="fit">
        <h1 class="text-5xl text-primary" style="margin: 0; font-weight: bold;">WEEK OVERVIEW</h1>
    </div>
    
    <div class="fill-height row" style="margin: 0 32px; gap: 16px; align-items: stretch;">
        <div class="bg-muted" style="flex: 1; padding: 24px; border-left: 8px solid var(--color-primary); display: flex; flex-direction: column; justify-content: center;">
            <div class="text-6xl text-primary" style="font-weight: bold; margin: 0 0 8px 0;">
                {summary['total_raids']}
            </div>
            <div class="text-lg text-surface-foreground" style="margin: 0;">
                Raid Sessions
            </div>
        </div>
        
        <div class="bg-muted" style="flex: 1; padding: 24px; border-left: 8px solid var(--color-secondary); display: flex; flex-direction: column; justify-content: center;">
            <div class="text-6xl text-secondary" style="font-weight: bold; margin: 0 0 8px 0;">
                {summary['total_bosses_killed']}
            </div>
            <div class="text-lg text-surface-foreground" style="margin: 0;">
                Bosses Killed
            </div>
        </div>
        
        <div class="bg-muted" style="flex: 1; padding: 24px; border-left: 8px solid var(--color-accent); display: flex; flex-direction: column; justify-content: center;">
            <div class="text-6xl text-accent-foreground" style="font-weight: bold; margin: 0 0 8px 0;">
                {summary['total_wipes']}
            </div>
            <div class="text-lg text-surface-foreground" style="margin: 0;">
                Total Wipes
            </div>
        </div>
    </div>
    
    <div class="bg-primary" style="margin: 0 32px; padding: 16px;">
        <div class="text-2xl text-primary-foreground text-center" style="margin: 0; font-weight: bold;">
            {summary['total_raid_time_hours']:.1f} Hours of Raiding
        </div>
    </div>
    
    <div style="position: absolute; bottom: 20px; left: 20px; right: 20px;">
        <div class="text-xs text-muted-foreground">
            Data compiled from guild raid logs - Updated: {datetime.now().strftime('%Y-%m-%d')}
        </div>
    </div>
</body>
</html>"""
    
    with open(os.path.join(config.SLIDES_DIR, 'slide2.html'), 'w') as f:
        f.write(html)

def create_boss_breakdown_slide(boss_stats):
    """Create slide with boss kill/wipe breakdown."""

    boss_rows = ""
    logo_html = get_logo_html()
    for boss in boss_stats[:8]:  # Limit to top 8 bosses
        kill_time = format_duration(boss['avg_kill_time'] * 1000) if boss['avg_kill_time'] else 'N/A'
        boss_rows += f"""
        <div class="row bg-muted" style="padding: 12px 16px; margin: 0 0 8px 0; align-items: center;">
            <div class="text-base text-surface-foreground" style="flex: 2; font-weight: bold; margin: 0;">
                {boss['boss']}
            </div>
            <div class="text-sm text-secondary" style="flex: 1; text-align: center; margin: 0;">
                {boss['kills']} Kill{"s" if boss['kills'] != 1 else ""}
            </div>
            <div class="text-sm text-muted-foreground" style="flex: 1; text-align: center; margin: 0;">
                {boss['wipes']} Wipe{"s" if boss['wipes'] != 1 else ""}
            </div>
            <div class="text-sm text-surface-foreground" style="flex: 1; text-align: center; margin: 0;">
                {kill_time}
            </div>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body class="col bg-surface" style="width: 960px; height: 540px; position: relative;">
    <!-- Logo in top right -->
    <div style="position: absolute; top: 20px; right: 20px; z-index: 100;">
        {logo_html}
    </div>
    <div style="width: 920px; margin: 0 20px; padding-top: 20px;" class="fit">
        <h1 class="text-5xl text-primary" style="margin: 0; font-weight: bold;">BOSS BREAKDOWN</h1>
    </div>
    
    <div style="margin: 0 32px;">
        <div class="row bg-accent" style="padding: 10px 16px; margin: 0 0 12px 0; align-items: center;">
            <div class="text-sm text-accent-foreground" style="flex: 2; font-weight: bold; margin: 0;">BOSS</div>
            <div class="text-sm text-accent-foreground" style="flex: 1; text-align: center; margin: 0;">KILLS</div>
            <div class="text-sm text-accent-foreground" style="flex: 1; text-align: center; margin: 0;">WIPES</div>
            <div class="text-sm text-accent-foreground" style="flex: 1; text-align: center; margin: 0;">AVG TIME</div>
        </div>
        
        {boss_rows}
    </div>
    
    <div style="position: absolute; bottom: 20px; left: 20px; right: 20px;">
        <div class="text-xs text-muted-foreground">
            Kill time shown as MM:SS - Data from WarcraftLogs
        </div>
    </div>
</body>
</html>"""
    
    with open(os.path.join(config.SLIDES_DIR, 'slide3.html'), 'w') as f:
        f.write(html)

def create_top_performers_slide(dps_top, hps_top):
    """Create slide with top DPS and HPS performers."""
    dps_rows = ""
    for i, player in enumerate(dps_top[:5], 1):
        dps_rows += f"""
        <div class="row bg-muted" style="padding: 10px 14px; margin: 0 0 6px 0; align-items: center;">
            <div class="text-lg text-secondary" style="width: 30px; font-weight: bold; margin: 0;">#{i}</div>
            <div class="text-base text-surface-foreground" style="flex: 1; margin: 0;">{player['name']}</div>
            <div class="text-base text-primary" style="width: 100px; text-align: right; font-weight: bold; margin: 0;">
                {player['avg']:,.0f}
            </div>
        </div>
        """
    
    hps_rows = ""
    for i, player in enumerate(hps_top[:5], 1):
        hps_rows += f"""
        <div class="row bg-muted" style="padding: 10px 14px; margin: 0 0 6px 0; align-items: center;">
            <div class="text-lg text-secondary" style="width: 30px; font-weight: bold; margin: 0;">#{i}</div>
            <div class="text-base text-surface-foreground" style="flex: 1; margin: 0;">{player['name']}</div>
            <div class="text-base text-primary" style="width: 100px; text-align: right; font-weight: bold; margin: 0;">
                {player['avg']:,.0f}
            </div>
        </div>
        """
    logo_html = get_logo_html()
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body class="col bg-surface" style="width: 960px; height: 540px; position: relative;">
    <!-- Logo in top right -->
    <div style="position: absolute; top: 20px; right: 20px; z-index: 100;">
        {logo_html}
    </div>
    <div style="width: 920px; margin: 0 20px; padding-top: 20px;" class="fit">
        <h1 class="text-5xl text-primary" style="margin: 0; font-weight: bold;">PUMPERS OF THE WEEK</h1>
    </div>
    
    <div class="row fill-height" style="margin: 0 32px; gap: 20px; align-items: stretch;">
        <div style="flex: 1;">
            <div class="text-2xl text-secondary" style="margin: 0 0 12px 0; font-weight: bold;">
                DPS RANKINGS
            </div>
            {dps_rows}
        </div>
        
        <div style="flex: 1;">
            <div class="text-2xl text-secondary" style="margin: 0 0 12px 0; font-weight: bold;">
                HPS RANKINGS
            </div>
            {hps_rows}
        </div>
    </div>
    
    <div style="position: absolute; bottom: 20px; left: 20px; right: 20px;">
        <div class="text-xs text-muted-foreground">
            Average performance across all encounters this week
        </div>
    </div>
</body>
</html>"""
    
    with open(os.path.join(config.SLIDES_DIR, 'slide4.html'), 'w') as f:
        f.write(html)

def create_closing_slide():
    """Create closing slide."""
    logo_html = get_logo_html()
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body class="col bg-surface center" style="width: 960px; height: 540px;">
    <!-- Logo in top right -->
    <div style="position: absolute; top: 20px; right: 20px; z-index: 100;">
        {logo_html}
    </div>
    <div class="text-center">
        <h1 class="text-7xl text-primary" style="margin: 0 0 24px 0; font-weight: bold;">
            GREAT WORK THIS WEEK!
        </h1>
        <div class="text-3xl text-surface-foreground" style="margin: 0 0 32px 0;">
            Let's keep pushing forward
        </div>
        <div class="bg-secondary" style="padding: 16px 32px; display: inline-block;">
            <div class="text-2xl text-secondary-foreground" style="margin: 0; font-weight: bold;">
                See you at raid time!
            </div>
        </div>
    </div>
</body>
</html>"""
    
    with open(os.path.join(config.SLIDES_DIR, 'slide7.html'), 'w') as f:
        f.write(html)

def create_top_dps_overall_slide(week_start, week_end):
    """Create slide with top 5 DPS overall across all fights."""
    # Get overall DPS rankings
    logo_html = get_logo_html()
    conn = database.sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            player_name,
            player_class,
            spec,
            AVG(dps) as avg_dps,
            MAX(dps) as max_dps,
            COUNT(DISTINCT boss_name) as bosses_fought
        FROM player_performance p
        JOIN raids r ON p.raid_id = r.raid_id
        WHERE r.start_time >= ? AND r.start_time <= ?
        AND dps IS NOT NULL
        AND dps > 0
        AND role = 'DPS'
        GROUP BY player_name
        ORDER BY avg_dps DESC
        LIMIT 5
    ''', (week_start, week_end))
    
    top_dps = cursor.fetchall()
    conn.close()
    
    dps_rows = ""
    for i, (name, pclass, spec, avg_dps, max_dps, bosses) in enumerate(top_dps, 1):
        dps_rows += f"""
        <div class="row bg-muted" style="padding: 14px 16px; margin: 0 0 8px 0; align-items: center; border-left: 4px solid var(--color-secondary);">
            <div class="text-2xl text-secondary" style="width: 40px; font-weight: bold; margin: 0;">#{i}</div>
            <div style="flex: 1;">
                <div class="text-lg text-surface-foreground" style="margin: 0 0 4px 0; font-weight: bold;">{name}</div>
                <div class="text-sm text-muted-foreground" style="margin: 0;">{spec} {pclass} - {bosses} bosses</div>
            </div>
            <div style="text-align: right;">
                <div class="text-2xl text-primary" style="margin: 0; font-weight: bold;">{avg_dps:,.0f}</div>
                <div class="text-sm text-muted-foreground" style="margin: 0;">Avg DPS</div>
            </div>
            <div style="text-align: right; margin-left: 20px;">
                <div class="text-xl text-surface-foreground" style="margin: 0; font-weight: bold;">{max_dps:,.0f}</div>
                <div class="text-sm text-muted-foreground" style="margin: 0;">Peak</div>
            </div>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body class="col bg-surface" style="width: 960px; height: 540px; position: relative;">
    <!-- Logo in top right -->
    <div style="position: absolute; top: 20px; right: 20px; z-index: 100;">
        {logo_html}
    </div>
    <div style="width: 920px; margin: 0 20px; padding-top: 20px;" class="fit">
        <h1 class="text-5xl text-primary" style="margin: 0; font-weight: bold;">TOP 5 DPS - OVERALL</h1>
    </div>
    
    <div style="margin: 0 32px;">
        {dps_rows}
    </div>
    
    <div style="position: absolute; bottom: 20px; left: 20px; right: 20px;">
        <div class="text-xs text-muted-foreground">
            Average DPS across all boss encounters this week - Peak shows highest single-fight DPS
        </div>
    </div>
</body>
</html>"""
    
    with open(os.path.join(config.SLIDES_DIR, 'slide5.html'), 'w') as f:
        f.write(html)

def create_death_causes_slide(week_start, week_end):
    """Create slide with top 10 death causes with Wowhead links."""
    logo_html = get_logo_html()
    death_causes = database.get_top_death_causes(week_start, week_end, 10)
    
    if not death_causes:
        return
    
    col1_deaths = death_causes[:5]
    col2_deaths = death_causes[5:10]
    
    def make_death_rows(deaths, start_index=1):
        rows = ""
        for i, death in enumerate(deaths, start_index):
            ability_display = death['ability'][:30] + "..." if len(death['ability']) > 30 else death['ability']
            boss_name = death.get('boss', 'Multiple Bosses')
            boss_display = boss_name[:20] if boss_name else ''
            ability_id = death.get('ability_id', 0)
            
            # Create Wowhead link if we have an ability ID
            # In create_death_causes_slide function
            if ability_id and ability_id > 0:
                ability_link = f'<a href="https://www.wowhead.com/spell={ability_id}" data-wowhead="spell={ability_id}" style="color: #32CD32; text-decoration: none;">{ability_display}</a>'
            else:
                ability_link = ability_display
            
            rows += f"""
            <div class="bg-muted" style="padding: 10px 14px; margin: 0 0 6px 0;">
                <div class="row" style="align-items: center; margin: 0 0 4px 0;">
                    <div class="text-lg text-primary" style="width: 30px; font-weight: bold; margin: 0;">#{i}</div>
                    <div style="flex: 1;">
                        <div class="text-base text-surface-foreground" style="margin: 0;">{ability_link}</div>
                    </div>
                    <div class="text-base text-secondary" style="width: 60px; text-align: right; font-weight: bold; margin: 0;">
                        {death['deaths']}×
                    </div>
                </div>
                <div class="text-xs text-muted-foreground" style="margin: 0 0 0 30px;">
                    {boss_display}
                </div>
            </div>
            """
        return rows
    
    col1_html = make_death_rows(col1_deaths, 1)
    col2_html = make_death_rows(col2_deaths, 6) if col2_deaths else ""
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body class="col bg-surface" style="width: 960px; height: 540px; position: relative;">
    <!-- Logo in top right -->
    <div style="position: absolute; top: 20px; right: 20px; z-index: 100;">
        {logo_html}
    </div>
    <div style="width: 920px; margin: 0 20px; padding-top: 20px;" class="fit">
        <h1 class="text-5xl text-primary" style="margin: 0; font-weight: bold;">TOP 10 KILLERS</h1>
    </div>
    
    <div class="row fill-height" style="margin: 0 32px; gap: 20px; align-items: stretch;">
        <div style="flex: 1;">
            {col1_html}
        </div>
        
        <div style="flex: 1;">
            {col2_html}
        </div>
    </div>
    
    <div style="position: absolute; bottom: 20px; left: 20px; right: 20px;">
        <div class="text-xs text-muted-foreground">
            Most common causes of death - Click ability names for Wowhead details
        </div>
    </div>
</body>
</html>"""
    
    with open(os.path.join(config.SLIDES_DIR, 'slide6.html'), 'w') as f:
        f.write(html)


def create_conversion_script():
    """Create Node.js script to convert HTML slides to PowerPoint."""
    script = """const pptxgen = require("pptxgenjs");
const { html2pptx } = require("./html2pptx");

async function main() {
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_16x9";
  
  // Add slides
  await html2pptx("slides/slide1.html", pptx);  // Title
  await html2pptx("slides/slide2.html", pptx);  // Overview
  await html2pptx("slides/slide3.html", pptx);  // Boss breakdown
  await html2pptx("slides/slide4.html", pptx);  // Top performers (DPS/HPS split)
  await html2pptx("slides/slide5.html", pptx);  // Top 5 DPS overall
  
  // Death causes slide (may not exist if no death data)
  const fs = require('fs');
  if (fs.existsSync("slides/slide6.html")) {
    await html2pptx("slides/slide6.html", pptx);  // Top 10 death causes
  }
  


  await html2pptx("slides/slide7.html", pptx);  // Closing
  
  // Save presentation
  const filename = `output/raid-stats-${Date.now()}.pptx`;
  await pptx.writeFile(filename);
  console.log(`Presentation created: ${filename}`);
}

main().catch(console.error);
"""
    
    with open('convert.js', 'w') as f:
        f.write(script)

def generate_presentation():
    """Main function to generate the PowerPoint presentation."""
    print("Generating PowerPoint presentation...")
    
    # Get week range
    week_start, week_end = get_week_range()
    
    # Get data from database
    summary = database.get_weekly_summary(week_start, week_end)
    boss_stats = database.get_boss_statistics(week_start, week_end)
    dps_top = database.get_top_performers(week_start, week_end, 'dps', 5)
    hps_top = database.get_top_performers(week_start, week_end, 'hps', 5)
    
    print(f"Summary: {summary}")
    print(f"Boss stats: {len(boss_stats)} bosses")
    print(f"Top DPS: {len(dps_top)} players")
    print(f"Top HPS: {len(hps_top)} players")
    
    # Create output directory
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # Create CSS
    create_shared_css()
    
    # Create slides
    create_title_slide(week_start, week_end)
    create_summary_slide(summary)
    create_boss_breakdown_slide(boss_stats)
    create_top_performers_slide(dps_top, hps_top)
    create_top_dps_overall_slide(week_start, week_end)
    create_death_causes_slide(week_start, week_end)

    create_closing_slide()
    
    # Create conversion script
    create_conversion_script()
    
    print("HTML slides created successfully!")
    print("Run the conversion with: NODE_PATH=\"$(npm root -g)\" node convert.js")

if __name__ == '__main__':
    generate_presentation()
