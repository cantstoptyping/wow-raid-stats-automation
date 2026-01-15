"""SQLite database operations for raid statistics."""
import sqlite3
from datetime import datetime
import json
import config

def init_database():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Raids table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raid_id TEXT UNIQUE NOT NULL,
            raid_name TEXT NOT NULL,
            start_time INTEGER NOT NULL,
            end_time INTEGER NOT NULL,
            zone_name TEXT,
            difficulty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Boss encounters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS encounters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raid_id TEXT NOT NULL,
            fight_id INTEGER,
            boss_name TEXT NOT NULL,
            kill_time INTEGER,
            wipe_count INTEGER DEFAULT 0,
            kill_duration_ms INTEGER,
            is_kill BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (raid_id) REFERENCES raids(raid_id)
        )
    ''')
    
    # Player performance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raid_id TEXT NOT NULL,
            encounter_id INTEGER,
            boss_name TEXT,
            player_name TEXT NOT NULL,
            player_class TEXT,
            spec TEXT,
            role TEXT,
            dps REAL,
            hps REAL,
            parse_percentile INTEGER,
            deaths INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (raid_id) REFERENCES raids(raid_id),
            FOREIGN KEY (encounter_id) REFERENCES encounters(id)
        )
    ''')
    
    # Weekly summaries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start TEXT NOT NULL UNIQUE,
            week_end TEXT NOT NULL,
            total_raids INTEGER,
            total_bosses_killed INTEGER,
            total_wipes INTEGER,
            total_raid_time_hours REAL,
            summary_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Deaths table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deaths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raid_id TEXT NOT NULL,
            fight_id INTEGER,
            boss_name TEXT,
            player_name TEXT NOT NULL,
            ability_name TEXT,
            ability_id INTEGER,
            timestamp INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (raid_id) REFERENCES raids(raid_id)
        )
    ''')




    conn.commit()
    conn.close()

def store_raid(raid_data):
    """Store raid information in database."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO raids 
        (raid_id, raid_name, start_time, end_time, zone_name, difficulty)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        raid_data['raid_id'],
        raid_data['raid_name'],
        raid_data['start_time'],
        raid_data['end_time'],
        raid_data.get('zone_name'),
        raid_data.get('difficulty')
    ))
    
    conn.commit()
    conn.close()

def store_encounter(encounter_data):
    """Store boss encounter data."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO encounters 
        (raid_id, fight_id, boss_name, kill_time, wipe_count, kill_duration_ms, is_kill)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        encounter_data['raid_id'],
        encounter_data.get('fight_id'),
        encounter_data['boss_name'],
        encounter_data.get('kill_time'),
        encounter_data.get('wipe_count', 0),
        encounter_data.get('kill_duration_ms'),
        encounter_data.get('is_kill', False)
    ))
    
    encounter_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return encounter_id

def store_player_performance(performance_data):
    """Store player performance data."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO player_performance 
        (raid_id, encounter_id, boss_name, player_name, player_class, spec, role, dps, hps, parse_percentile, deaths)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        performance_data['raid_id'],
        performance_data.get('encounter_id'),
        performance_data.get('boss_name'),
        performance_data['player_name'],
        performance_data.get('player_class'),
        performance_data.get('spec'),
        performance_data.get('role'),
        performance_data.get('dps'),
        performance_data.get('hps'),
        performance_data.get('parse_percentile'),
        performance_data.get('deaths', 0)
    ))
    
    conn.commit()
    conn.close()

def get_weekly_summary(week_start, week_end):
    """Get summary statistics for a given week."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get raids in date range
    cursor.execute('''
        SELECT COUNT(*), SUM(end_time - start_time) as total_time
        FROM raids
        WHERE start_time >= ? AND start_time <= ?
    ''', (week_start, week_end))
    
    raid_stats = cursor.fetchone()
    total_raids = raid_stats[0] or 0
    total_time_ms = raid_stats[1] or 0
    
    # Get boss kills and wipes
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN is_kill = 1 THEN 1 ELSE 0 END) as kills,
            SUM(wipe_count) as wipes
        FROM encounters e
        JOIN raids r ON e.raid_id = r.raid_id
        WHERE r.start_time >= ? AND r.start_time <= ?
    ''', (week_start, week_end))
    
    encounter_stats = cursor.fetchone()
    total_kills = encounter_stats[0] or 0
    total_wipes = encounter_stats[1] or 0
    
    conn.close()
    
    return {
        'total_raids': total_raids,
        'total_bosses_killed': total_kills,
        'total_wipes': total_wipes,
        'total_raid_time_hours': total_time_ms / (1000 * 60 * 60) if total_time_ms else 0
    }

def get_top_performers(week_start, week_end, metric='dps', limit=5):
    """Get top performers for a given metric."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    order_column = metric if metric in ['dps', 'hps', 'parse_percentile'] else 'dps'
    
    cursor.execute(f'''
        SELECT 
            player_name,
            player_class,
            role,
            AVG({order_column}) as avg_performance,
            MAX({order_column}) as max_performance
        FROM player_performance p
        JOIN raids r ON p.raid_id = r.raid_id
        WHERE r.start_time >= ? AND r.start_time <= ?
        AND {order_column} IS NOT NULL
        GROUP BY player_name, player_class, role
        ORDER BY avg_performance DESC
        LIMIT ?
    ''', (week_start, week_end, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'name': row[0],
            'class': row[1],
            'role': row[2],
            'avg': row[3],
            'max': row[4]
        }
        for row in results
    ]

def get_boss_statistics(week_start, week_end):
    """Get statistics per boss for the week."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            boss_name,
            SUM(CASE WHEN is_kill = 1 THEN 1 ELSE 0 END) as kills,
            SUM(wipe_count) as wipes,
            AVG(CASE WHEN is_kill = 1 THEN kill_duration_ms END) / 1000 as avg_kill_time_sec
        FROM encounters e
        JOIN raids r ON e.raid_id = r.raid_id
        WHERE r.start_time >= ? AND r.start_time <= ?
        GROUP BY boss_name
        ORDER BY boss_name
    ''', (week_start, week_end))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'boss': row[0],
            'kills': row[1],
            'wipes': row[2],
            'avg_kill_time': row[3]
        }
        for row in results
    ]

def store_death(death_data):
    """Store death event data."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO deaths 
        (raid_id, fight_id, boss_name, player_name, ability_name, ability_id, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        death_data['raid_id'],
        death_data.get('fight_id'),
        death_data.get('boss_name'),
        death_data['player_name'],
        death_data.get('ability_name'),
        death_data.get('ability_id'),
        death_data.get('timestamp')
    ))
    
    conn.commit()
    conn.close()

def get_top_death_causes(week_start, week_end, limit=10):
    """Get the top causes of death with boss information."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            ability_name,
            COUNT(*) as death_count,
            COUNT(DISTINCT player_name) as players_affected,
            boss_name,
            ability_id
        FROM deaths d
        JOIN raids r ON d.raid_id = r.raid_id
        WHERE r.start_time >= ? AND r.start_time <= ?
        AND ability_name IS NOT NULL
        AND ability_name != 'Unknown'
        GROUP BY ability_name, boss_name, ability_id
        ORDER BY death_count DESC
        LIMIT ?
    ''', (week_start, week_end, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'ability': row[0],
            'deaths': row[1],
            'players_affected': row[2],
            'boss': row[3],
            'ability_id': row[4]
        }
        for row in results
    ]

def get_player_death_count(week_start, week_end):
    """Get death counts per player."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            player_name,
            COUNT(*) as death_count
        FROM deaths d
        JOIN raids r ON d.raid_id = r.raid_id
        WHERE r.start_time >= ? AND r.start_time <= ?
        GROUP BY player_name
        ORDER BY death_count DESC
    ''', (week_start, week_end))
    
    results = cursor.fetchall()
    conn.close()
    
    return [{'player': row[0], 'deaths': row[1]} for row in results]



