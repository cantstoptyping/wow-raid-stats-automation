"""Main orchestration script for WoW raid stats automation."""
import sys
import config
import database
import fetch_data
import generate_pptx


def apply_inline_css():
    """Apply inline CSS to all slides for standalone viewing."""
    import os
    import re
    
    inline_css = """
<style>
* { 
  margin: 0; 
  padding: 0; 
  box-sizing: border-box; 
}

body {
  font-family: Arial, sans-serif !important;
  background-color: #1a1a1a !important;
  color: #f5f5f5 !important;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

.col {
  display: flex;
  flex-direction: column;
}

.row {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.fill-height { flex: 1; }
.fit { flex: none; }
.text-center { text-align: center; }

/* Background colors */
.bg-surface { background-color: #1a1a1a !important; }
.bg-primary { background-color: #32CD32 !important; }
.bg-secondary { background-color: #D4AF37 !important; }
.bg-muted { background-color: #2d2d2d !important; }
.bg-accent { background-color: #2C1810 !important; }
.bg-border { background-color: #404040 !important; }

/* Text colors */
.text-primary { color: #32CD32 !important; }
.text-secondary { color: #D4AF37 !important; }
.text-surface-foreground { color: #f5f5f5 !important; }
.text-muted-foreground { color: #a0a0a0 !important; }
.text-accent-foreground { color: #ffffff !important; }
.text-primary-foreground { color: #ffffff !important; }
.text-secondary-foreground { color: #1d1d1d !important; }

/* Font sizes */
.text-xs { font-size: 12px; }
.text-sm { font-size: 14px; }
.text-base { font-size: 16px; }
.text-lg { font-size: 18px; }
.text-xl { font-size: 20px; }
.text-2xl { font-size: 24px; }
.text-3xl { font-size: 30px; }
.text-4xl { font-size: 36px; }
.text-5xl { font-size: 48px; }
.text-6xl { font-size: 60px; }
.text-7xl { font-size: 72px; }
.text-8xl { font-size: 96px; }
</style>
<script>const whTooltips = {colorLinks: true, iconizeLinks: true, renameLinks: true};</script>
<script src="https://wow.zamimg.com/js/tooltips.js"></script>
"""
    
    slides_dir = config.SLIDES_DIR
    for filename in os.listdir(slides_dir):
        if filename.endswith('.html') and filename.startswith('slide'):
            filepath = os.path.join(slides_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(filepath, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            # Fix encoding issues
            content = content.replace('–', '-')
            content = content.replace('—', '-')
            content = content.replace('\x96', '-')
            content = content.replace('\x97', '-')
            content = content.replace('�', '-')
            
            # Remove any existing style tags and scripts
            content = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL)
            content = re.sub(r'<script.*?tooltips\.js.*?</script>', '', content, flags=re.DOTALL)
            
            # Add inline CSS and Wowhead script
            if '<head>' in content:
                content = content.replace('</head>', f'{inline_css}\n</head>')
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    print("✓ Applied CSS styling and Wowhead tooltips to slides")


def main():
    """Main execution flow."""
    print("=" * 60)
    print("WoW Raid Stats PowerPoint Generator")
    print("=" * 60)
    
    # Validate configuration
    try:
        config.validate_config()
        print("✓ Configuration validated")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease create a .env file with required variables.")
        print("See README.md for setup instructions.")
        return 1
    
    # Initialize database
    print("\nInitializing database...")
    database.init_database()
    print("✓ Database ready")
    
    # Fetch raid data
    print("\nFetching raid data from WarcraftLogs...")
    try:
        data = fetch_data.fetch_weekly_data()
        print(f"✓ Fetched {len(data['raids'])} raids")
        print(f"✓ Fetched {len(data['encounters'])} encounters")
        print(f"✓ Fetched {len(data['players'])} player records")
    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        return 1
    
    # Store data in database
    print("\nStoring data in database...")
    try:
        import sqlite3
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Delete existing data for these raid_ids to prevent duplicates
        raid_ids = [raid['raid_id'] for raid in data['raids']]
        if raid_ids:
            placeholders = ','.join('?' * len(raid_ids))
            print(f"  Cleaning existing data for {len(raid_ids)} raid(s)...")
            
            cursor.execute(f'DELETE FROM deaths WHERE raid_id IN ({placeholders})', raid_ids)
            cursor.execute(f'DELETE FROM player_performance WHERE raid_id IN ({placeholders})', raid_ids)
            cursor.execute(f'DELETE FROM encounters WHERE raid_id IN ({placeholders})', raid_ids)
            cursor.execute(f'DELETE FROM raids WHERE raid_id IN ({placeholders})', raid_ids)
            
            conn.commit()
        
        conn.close()
        
        # Store raids first
        for raid in data['raids']:
            database.store_raid(raid)
        
        # Store encounters and create encounter_id map
        encounter_map = {}  # (raid_id, boss_name, fight_id) -> encounter_id
        for encounter in data['encounters']:
            encounter_id = database.store_encounter(encounter)
            key = (encounter['raid_id'], encounter['boss_name'], encounter.get('fight_id'))
            encounter_map[key] = encounter_id
        
        # Store player performance with encounter_id
        for player in data['players']:
            key = (player['raid_id'], player['boss_name'], player.get('fight_id'))
            player['encounter_id'] = encounter_map.get(key)
            database.store_player_performance(player)
        
        # Store deaths
        print(f"  Storing {len(data['deaths'])} deaths...")
        for death in data['deaths']:
            try:
                database.store_death(death)
            except Exception as e:
                print(f"    Error storing death: {e}")
                print(f"    Death data: {death}")
                break  # Stop after first error to see it

 
        
        print("✓ Data stored successfully")
        print(f"  - {len(data['raids'])} raids")
        print(f"  - {len(data['encounters'])} encounters")
        print(f"  - {len(data['players'])} player records")
        print(f"  - {len(data['deaths'])} death events")
    except Exception as e:
        print(f"✗ Error storing data: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Generate PowerPoint
    print("\nGenerating PowerPoint presentation...")
    try:
        generate_pptx.generate_presentation()
        print("✓ PowerPoint generation prepared")
    except Exception as e:
        print(f"✗ Error generating presentation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    apply_inline_css()

    print("\n" + "=" * 60)
    print("Next steps:")
    print("1. View slides: explorer slides")
    print("2. Convert to PowerPoint (when ready)")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())