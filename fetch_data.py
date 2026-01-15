import requests
from datetime import datetime, timedelta
import config

# Boss filter - only these bosses will be included
BOSS_FILTER = [
    "Plexus Sentinel",
    "Loom'ithar",
    "Soulbinder Naazindhri",
    "Forgeweaver Araz",
    "The Soul Hunters",
    "Fractillus",
    "Nexus-King Salhadaar",
    "Dimensius, the All-Devouring"
]

class WarcraftLogsAPI:
    """WarcraftLogs API client."""
    
    def __init__(self):
        self.client_id = config.WARCRAFTLOGS_CLIENT_ID
        self.client_secret = config.WARCRAFTLOGS_CLIENT_SECRET
        self.token = None
        self.token_expires = None
    
    def _get_access_token(self):
        """Get OAuth2 access token."""
        if self.token and self.token_expires and datetime.now() < self.token_expires:
            return self.token
        
        auth_url = 'https://www.warcraftlogs.com/oauth/token'
        
        response = requests.post(
            auth_url,
            auth=(self.client_id, self.client_secret),
            data={'grant_type': 'client_credentials'}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.text}")
        
        data = response.json()
        self.token = data['access_token']
        self.token_expires = datetime.now() + timedelta(seconds=data['expires_in'] - 60)
        
        return self.token
    
    def _graphql_query(self, query, variables=None):
        """Execute a GraphQL query against WarcraftLogs API."""
        token = self._get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        
        response = requests.post(
            config.WARCRAFTLOGS_API_URL,
            headers=headers,
            json={'query': query, 'variables': variables or {}}
        )
        
        if response.status_code != 200:
            raise Exception(f"GraphQL query failed: {response.text}")
        
        data = response.json()
        if 'errors' in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        return data['data']
    
    def get_guild_reports(self, days_back=7):
        """Get recent guild raid reports."""
        
        query = """
        query($guildName: String!, $serverSlug: String!, $serverRegion: String!) {
          reportData {
            reports(
              guildName: $guildName
              guildServerSlug: $serverSlug
              guildServerRegion: $serverRegion
              limit: 50
            ) {
              data {
                code
                title
                owner {
                  name
                }
                startTime
                endTime
                zone {
                  name
                }
                fights {
                  id
                  name
                  difficulty
                  kill
                  fightPercentage
                  startTime
                  endTime
                }
              }
            }
          }
        }
        """
        
        variables = {
            'guildName': config.GUILD_NAME,
            'serverSlug': config.GUILD_REALM.lower().replace(' ', '-'),
            'serverRegion': config.GUILD_REGION.upper()
        }
        
        result = self._graphql_query(query, variables)
        
        reports = result.get('reportData', {}).get('reports', {}).get('data', [])
        
        if hasattr(config, 'RAID_TEAM_FILTER') and config.RAID_TEAM_FILTER:
            reports = [r for r in reports if r.get('owner', {}).get('name', '').lower() == config.RAID_TEAM_FILTER.lower()]
            print(f"Filtered to {len(reports)} reports by owner '{config.RAID_TEAM_FILTER}'")
        
        # Filter to requested time range
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)
        
        filtered_reports = [
            r for r in reports 
            if start_time <= r['startTime'] <= end_time
        ]
        
        print(f"Found {len(reports)} total reports, {len(filtered_reports)} in last {days_back} days")
        
        return filtered_reports if filtered_reports else reports[:10]
    
    def get_actor_mappings(self, report_code):
        """Get actor ID to name mappings for the report."""
        query = """
        query($code: String!) {
          reportData {
            report(code: $code) {
              masterData {
                actors {
                  id
                  name
                  type
                  subType
                }
                abilities {
                  gameID
                  name
                }
              }
            }
          }
        }
        """
        
        try:
            result = self._graphql_query(query, {'code': report_code})
            master_data = result.get('reportData', {}).get('report', {}).get('masterData', {})
            
            # Create mappings
            actor_map = {actor['id']: actor['name'] for actor in master_data.get('actors', [])}
            ability_map = {ability['gameID']: ability['name'] for ability in master_data.get('abilities', [])}
            
            return actor_map, ability_map
        except Exception as e:
            print(f"  Warning: Could not fetch actor mappings: {e}")
            return {}, {}
    
    def get_fight_details(self, report_code, fight_id):
        """Get detailed fight information including DPS, HPS, and deaths."""
        query = """
        query($code: String!, $fightIDs: [Int]!) {
          reportData {
            report(code: $code) {
              table(fightIDs: $fightIDs, dataType: DamageDone)
              healingTable: table(fightIDs: $fightIDs, dataType: Healing)
              deaths: events(fightIDs: $fightIDs, dataType: Deaths, limit: 1000) {
                data
              }
            }
          }
        }
        """
        
        variables = {
            'code': report_code,
            'fightIDs': [fight_id]
        }
        
        try:
            result = self._graphql_query(query, variables)
            return result.get('reportData', {}).get('report', {})
        except Exception as e:
            print(f"  Warning: Could not fetch details for fight {fight_id}: {e}")
            return {}


def fetch_weekly_data():
    """Fetch and parse weekly raid data with detailed performance metrics."""
    api = WarcraftLogsAPI()
    
    reports = api.get_guild_reports(days_back=7)
    
    parsed_data = {
        'raids': [],
        'encounters': [],
        'players': [],
        'deaths': []
    }
    
    for report in reports:
        print(f"\nProcessing report: {report['title']}")
        
        # Get actor and ability mappings for this report
        print("  Fetching actor/ability mappings...")
        actor_map, ability_map = api.get_actor_mappings(report['code'])
        
        raid_data = {
            'raid_id': report['code'],
            'raid_name': report['title'],
            'start_time': report['startTime'],
            'end_time': report['endTime'],
            'zone_name': report.get('zone', {}).get('name') if report.get('zone') else None,
        }
        
        parsed_data['raids'].append(raid_data)
        
        for fight in report.get('fights', []):
            boss_name = fight['name']
            
            # Skip trash and non-boss fights
            if boss_name == 'Trash':
                continue
            
            # Filter by boss list if configured
            if BOSS_FILTER and boss_name not in BOSS_FILTER:
                print(f"  Skipping {boss_name} (not in boss filter)")
                continue
            
            print(f"  Processing fight: {boss_name}")
            
            encounter_data = {
                'raid_id': report['code'],
                'fight_id': fight['id'],
                'boss_name': boss_name,
                'is_kill': fight.get('kill', False),
                'kill_time': fight.get('endTime'),
                'kill_duration_ms': fight.get('endTime', 0) - fight.get('startTime', 0),
                'wipe_count': 0 if fight.get('kill') else 1
            }
            
            parsed_data['encounters'].append(encounter_data)
                      
            # MOVED INSIDE THE FIGHT LOOP - NOTICE THE INDENTATION
            fight_details = api.get_fight_details(report['code'], fight['id'])

            # Parse DPS data
            dps_table = fight_details.get('table', {})
            if dps_table and isinstance(dps_table, dict) and 'data' in dps_table:
                entries = dps_table.get('data', {}).get('entries', [])
                fight_duration = max((fight['endTime'] - fight['startTime']) / 1000, 1)
                
                for entry in entries:
                    player_name = entry.get('name', 'Unknown')
                    player_class = entry.get('type', 'Unknown')
                    spec = entry.get('icon', '').split('-')[-1] if entry.get('icon') else 'Unknown'
                    total_damage = entry.get('total', 0)
                    
                    parsed_data['players'].append({
                        'raid_id': report['code'],
                        'fight_id': fight['id'],
                        'boss_name': boss_name,
                        'player_name': player_name,
                        'player_class': player_class,
                        'spec': spec,
                        'role': 'DPS',
                        'dps': total_damage / fight_duration,
                        'total_damage': total_damage
                    })

            # Parse healing data
            heal_table = fight_details.get('healingTable', {})
            if heal_table and isinstance(heal_table, dict) and 'data' in heal_table:
                entries = heal_table.get('data', {}).get('entries', [])
                fight_duration = max((fight['endTime'] - fight['startTime']) / 1000, 1)
                
                for entry in entries:
                    player_name = entry.get('name', 'Unknown')
                    player_class = entry.get('type', 'Unknown')
                    spec = entry.get('icon', '').split('-')[-1] if entry.get('icon') else 'Unknown'
                    total_healing = entry.get('total', 0)
                    
                    parsed_data['players'].append({
                        'raid_id': report['code'],
                        'fight_id': fight['id'],
                        'boss_name': boss_name,
                        'player_name': player_name,
                        'player_class': player_class,
                        'spec': spec,
                        'role': 'Healer',
                        'hps': total_healing / fight_duration,
                        'total_healing': total_healing
                    })

            # Parse death data with proper name mapping
            death_events = fight_details.get('deaths', {}).get('data', [])
            if death_events:
                for death in death_events:
                    target_id = death.get('targetID', -1)
                    ability_id = death.get('killingAbilityGameID', 0)
                    
                    player_name = actor_map.get(target_id, f'Unknown (ID: {target_id})')
                    ability_name = ability_map.get(ability_id, f'Unknown (ID: {ability_id})')
                    
                    parsed_data['deaths'].append({
                        'raid_id': report['code'],
                        'fight_id': fight['id'],
                        'boss_name': boss_name,
                        'player_name': player_name,
                        'ability_name': ability_name,
                        'ability_id': ability_id,
                        'timestamp': death.get('timestamp', 0)
                    })
    
    return parsed_data

if __name__ == '__main__':
    config.validate_config()
    data = fetch_weekly_data()
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"Fetched {len(data['raids'])} raids")
    print(f"Fetched {len(data['encounters'])} encounters")
    print(f"Fetched {len(data['players'])} player records")
    print(f"Fetched {len(data['deaths'])} death events")
    print(f"{'='*60}")