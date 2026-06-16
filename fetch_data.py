import requests
import time
from datetime import datetime, timedelta
import config

DIFFICULTY_MAP = {
    3: 'Normal',
    4: 'Heroic',
    5: 'Mythic',
    14: 'LFR'
}

# Maps a unique keyword (lowercase, checked with `in`) to the canonical display name.
# Any WCL boss name containing the keyword is normalised to the canonical form.
# Using partial keywords handles WCL's inconsistent naming across patches/difficulties.
BOSS_FILTER = {
    "averzian":      "Imperator Averzian",
    "vorasius":      "Vorasius",
    "salhadaar":     "Fallen-King Salhadaar",
    "vaelgor":       "Vaelgor & Ezzorak",
    "ezzorak":       "Vaelgor & Ezzorak",
    "lightblinded":  "Lightblinded Vanguard",
    "cosmos":        "Crown of the Cosmos",
    "chimaerus":     "Chimaerus, the Undreamt God",
    "belo'ren":      "Belo'ren, Child of Al'ar",
    "midnight falls":"Midnight Falls",
}

# Common targeted external defensive ability IDs (stable across expansions).
# Update this list if new externals are added in a patch.
EXTERNAL_DEFENSIVE_IDS = [
    33206,   # Pain Suppression (Disc Priest)
    102342,  # Ironbark (Druid)
    116849,  # Life Cocoon (Mistweaver Monk)
    6940,    # Blessing of Sacrifice (Paladin)
    1022,    # Blessing of Protection (Paladin)
    633,     # Lay on Hands (Paladin)
    97462,   # Rallying Cry (Warrior)
    31821,   # Aura Mastery (Holy Paladin)
    196718,  # Darkness (Havoc DH)
    145629,  # Anti-Magic Zone (DK)
]

_EXTERNAL_FILTER = (
    "ability.id in ("
    + ",".join(str(i) for i in EXTERNAL_DEFENSIVE_IDS)
    + ")"
)


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

        response = requests.post(
            'https://www.warcraftlogs.com/oauth/token',
            auth=(self.client_id, self.client_secret),
            data={'grant_type': 'client_credentials'}
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.text}")

        data = response.json()
        self.token = data['access_token']
        self.token_expires = datetime.now() + timedelta(seconds=data['expires_in'] - 60)
        return self.token

    def _graphql_query(self, query, variables=None, _retry=3):
        """Execute a GraphQL query against WarcraftLogs API. Retries on 429."""
        token = self._get_access_token()

        response = requests.post(
            config.WARCRAFTLOGS_API_URL,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            json={'query': query, 'variables': variables or {}}
        )

        if response.status_code == 429 and _retry > 0:
            wait = 300  # WCL free-tier resets hourly; wait 5 min between retries
            print(f"  Rate limited — waiting {wait}s before retry ({_retry} retries left)...")
            time.sleep(wait)
            return self._graphql_query(query, variables, _retry=_retry - 1)

        if response.status_code != 200:
            raise Exception(f"GraphQL query failed: {response.text}")

        data = response.json()
        if 'errors' in data:
            raise Exception(f"GraphQL errors: {data['errors']}")

        return data['data']

    def get_guild_reports(self):
        """Get all guild raid reports for the season, paginated."""
        query = """
        query($guildName: String!, $serverSlug: String!, $serverRegion: String!, $page: Int) {
          reportData {
            reports(
              guildName: $guildName
              guildServerSlug: $serverSlug
              guildServerRegion: $serverRegion
              limit: 25
              page: $page
            ) {
              current_page
              last_page
              data {
                code
                title
                owner { name }
                startTime
                endTime
                zone { name }
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

        all_reports = []
        page = 1
        while True:
            variables = {
                'guildName': config.GUILD_NAME,
                'serverSlug': config.GUILD_REALM.lower().replace(' ', '-'),
                'serverRegion': config.GUILD_REGION.upper(),
                'page': page
            }
            result = self._graphql_query(query, variables)
            reports_data = result.get('reportData', {}).get('reports', {})
            reports = reports_data.get('data', [])
            current_page = reports_data.get('current_page', 1)
            last_page = reports_data.get('last_page', 1)

            all_reports.extend(reports)
            print(f"  Fetched report page {current_page}/{last_page} ({len(reports)} reports)")

            if current_page >= last_page:
                break
            page += 1

        # Filter by raid team owner/title
        if config.RAID_TEAM_FILTER:
            desired = config.RAID_TEAM_FILTER.lower()
            all_reports = [
                r for r in all_reports
                if desired in r.get('owner', {}).get('name', '').lower()
                   or desired in r.get('title', '').lower()
            ]

        # Filter to on/after season start
        if config.SEASON_START:
            all_reports = [r for r in all_reports if r['startTime'] >= config.SEASON_START]

        print(f"Found {len(all_reports)} reports after filtering")
        return all_reports

    def get_actor_mappings(self, report_code):
        """Get actor ID to name mappings and the set of player actor IDs."""
        query = """
        query($code: String!) {
          reportData {
            report(code: $code) {
              masterData {
                actors { id  name  type  subType }
                abilities { gameID  name }
              }
            }
          }
        }
        """
        try:
            result = self._graphql_query(query, {'code': report_code})
            master_data = result.get('reportData', {}).get('report', {}).get('masterData', {})
            actors = master_data.get('actors', [])
            actor_map = {a['id']: a['name'] for a in actors}
            player_ids = {a['id'] for a in actors if a.get('type') == 'Player'}
            ability_map = {ability['gameID']: ability['name'] for ability in master_data.get('abilities', [])}
            return actor_map, ability_map, player_ids
        except Exception as e:
            print(f"  Warning: Could not fetch actor mappings: {e}")
            return {}, {}, set()

    def get_fight_details(self, report_code, fight_id):
        """Get fight details: DPS, HPS, damage taken, deaths, and external defensives."""
        query = """
        query($code: String!, $fightIDs: [Int]!, $externalFilter: String!) {
          reportData {
            report(code: $code) {
              table(fightIDs: $fightIDs, dataType: DamageDone)
              healingTable: table(fightIDs: $fightIDs, dataType: Healing)
              damageTakenTable: table(fightIDs: $fightIDs, dataType: DamageTaken)
              rankings(fightIDs: $fightIDs)
              deaths: events(fightIDs: $fightIDs, dataType: Deaths, limit: 1000) {
                data
              }
              externals: events(
                fightIDs: $fightIDs
                dataType: Buffs
                filterExpression: $externalFilter
                limit: 1000
              ) {
                data
              }
            }
          }
        }
        """
        try:
            result = self._graphql_query(query, {
                'code': report_code,
                'fightIDs': [fight_id],
                'externalFilter': _EXTERNAL_FILTER,
            })
            return result.get('reportData', {}).get('report', {})
        except Exception as e:
            print(f"  Warning: Could not fetch details for fight {fight_id}: {e}")
            return {}


def fetch_season_data(skip_raid_ids=None):
    """Fetch and parse all season raid data.

    skip_raid_ids: set of report codes already stored in the DB — their fight
    details are skipped to avoid redundant API calls.
    """
    api = WarcraftLogsAPI()
    skip_raid_ids = skip_raid_ids or set()

    reports = api.get_guild_reports()

    parsed_data = {
        'raids': [],
        'encounters': [],
        'players': [],
        'deaths': [],
        'externals': [],
    }

    for report in reports:
        report_code = report['code']
        print(f"\nProcessing report: {report['title']} ({report_code})")

        if report_code in skip_raid_ids:
            print(f"  Already stored — skipping detail fetch")
            continue

        print("  Fetching actor/ability mappings...")
        actor_map, ability_map, player_ids = api.get_actor_mappings(report_code)

        raid_data = {
            'raid_id': report_code,
            'raid_name': report['title'],
            'start_time': report['startTime'],
            'end_time': report['endTime'],
            'zone_name': report.get('zone', {}).get('name') if report.get('zone') else None,
        }

        report_has_valid_fights = False

        for fight in report.get('fights', []):
            boss_name = fight['name']

            if boss_name == 'Trash':
                continue

            boss_lower = boss_name.lower()
            canonical_name = next(
                (name for kw, name in BOSS_FILTER.items() if kw in boss_lower),
                None
            )
            if canonical_name is None:
                print(f"  Skipping {boss_name} (not in boss filter)")
                continue

            if config.DIFFICULTY_FILTER is not None:
                fight_difficulty = fight.get('difficulty', 0)
                if fight_difficulty != config.DIFFICULTY_FILTER:
                    print(f"  Skipping {boss_name} (difficulty {fight_difficulty}, want {config.DIFFICULTY_FILTER})")
                    continue

            report_has_valid_fights = True
            difficulty = DIFFICULTY_MAP.get(fight.get('difficulty'), 'Unknown')
            boss_name = canonical_name  # normalize to canonical form for storage
            is_kill = fight.get('kill', False)
            print(f"  Processing fight: {boss_name} ({difficulty}) {'[KILL]' if is_kill else '[WIPE]'}")

            encounter_data = {
                'raid_id': report_code,
                'fight_id': fight['id'],
                'boss_name': boss_name,
                'difficulty': difficulty,
                'is_kill': is_kill,
                'kill_time': fight.get('endTime'),
                'kill_duration_ms': fight.get('endTime', 0) - fight.get('startTime', 0),
                'wipe_count': 0 if is_kill else 1,
            }
            parsed_data['encounters'].append(encounter_data)

            time.sleep(1)  # throttle to stay within WCL free-tier rate limit
            fight_details = api.get_fight_details(report_code, fight['id'])
            fight_duration = max((fight['endTime'] - fight['startTime']) / 1000, 1)

            # --- Deaths (always captured, kills and wipes) ---
            for death in fight_details.get('deaths', {}).get('data', []):
                target_id = death.get('targetID', -1)
                ability_id = death.get('killingAbilityGameID', 0)
                player_name = actor_map.get(target_id, f'Unknown (ID: {target_id})')
                ability_name = ability_map.get(ability_id) or (
                    'Environmental / Unknown' if ability_id == 0 else f'Unknown (ID: {ability_id})'
                )
                parsed_data['deaths'].append({
                    'raid_id': report_code,
                    'fight_id': fight['id'],
                    'boss_name': boss_name,
                    'difficulty': difficulty,
                    'player_name': player_name,
                    'ability_name': ability_name,
                    'ability_id': ability_id,
                    'timestamp': death.get('timestamp', 0),
                })

            # --- External defensives (always captured) ---
            for event in fight_details.get('externals', {}).get('data', []):
                if event.get('type') not in ('applybuff', 'refreshbuff'):
                    continue
                source_id = event.get('sourceID', -1)
                target_id = event.get('targetID', -1)
                if source_id == target_id:
                    continue  # self-buff, not an external
                if source_id not in player_ids:
                    continue  # ignore NPC/environment sources
                ability_id = event.get('abilityGameID', 0)
                parsed_data['externals'].append({
                    'raid_id': report_code,
                    'fight_id': fight['id'],
                    'boss_name': boss_name,
                    'difficulty': difficulty,
                    'caster_name': actor_map.get(source_id, f'Unknown (ID: {source_id})'),
                    'target_name': actor_map.get(target_id, f'Unknown (ID: {target_id})'),
                    'ability_id': ability_id,
                    'ability_name': ability_map.get(ability_id, f'Unknown (ID: {ability_id})'),
                    'timestamp': event.get('timestamp', 0),
                })

            # Skip DPS/HPS/damage-taken stats on wipes — skews averages
            if not is_kill:
                continue

            # --- Build rank percentile lookups ---
            dps_rank_lookup = {}
            heal_rank_lookup = {}
            for fight_rankings in fight_details.get('rankings', {}).get('data', []):
                for role_key, role_data in fight_rankings.get('roles', {}).items():
                    for char in role_data.get('characters', []):
                        name = char.get('name')
                        pct = char.get('rankPercent')
                        if name and pct is not None:
                            if role_key == 'healers':
                                heal_rank_lookup[name] = pct
                            else:
                                dps_rank_lookup[name] = pct

            # --- DPS ---
            dps_table = fight_details.get('table', {})
            if dps_table and isinstance(dps_table, dict) and 'data' in dps_table:
                for entry in dps_table.get('data', {}).get('entries', []):
                    if entry.get('type') in ('NPC', 'Boss'):
                        continue
                    player_name = entry.get('name', 'Unknown')
                    if player_name not in dps_rank_lookup:
                        continue
                    total_damage = entry.get('total', 0)
                    parsed_data['players'].append({
                        'raid_id': report_code,
                        'fight_id': fight['id'],
                        'boss_name': boss_name,
                        'difficulty': difficulty,
                        'player_name': player_name,
                        'player_class': entry.get('type', 'Unknown'),
                        'spec': entry.get('icon', '').split('-')[-1] if entry.get('icon') else 'Unknown',
                        'role': 'DPS',
                        'dps': total_damage / fight_duration,
                        'total_damage': total_damage,
                        'percentile': dps_rank_lookup.get(player_name),
                    })

            # --- HPS ---
            heal_table = fight_details.get('healingTable', {})
            if heal_table and isinstance(heal_table, dict) and 'data' in heal_table:
                for entry in heal_table.get('data', {}).get('entries', []):
                    if entry.get('type') in ('NPC', 'Boss'):
                        continue
                    player_name = entry.get('name', 'Unknown')
                    if player_name not in heal_rank_lookup:
                        continue
                    total_healing = entry.get('total', 0)
                    parsed_data['players'].append({
                        'raid_id': report_code,
                        'fight_id': fight['id'],
                        'boss_name': boss_name,
                        'difficulty': difficulty,
                        'player_name': player_name,
                        'player_class': entry.get('type', 'Unknown'),
                        'spec': entry.get('icon', '').split('-')[-1] if entry.get('icon') else 'Unknown',
                        'role': 'Healer',
                        'hps': total_healing / fight_duration,
                        'total_healing': total_healing,
                        'percentile': heal_rank_lookup.get(player_name),
                    })

            # --- Damage taken ---
            dt_table = fight_details.get('damageTakenTable', {})
            if dt_table and isinstance(dt_table, dict) and 'data' in dt_table:
                dt_by_player = {}
                for entry in dt_table.get('data', {}).get('entries', []):
                    if entry.get('type') in ('NPC', 'Boss'):
                        continue
                    player_name = entry.get('name', 'Unknown')
                    dt_by_player[player_name] = entry.get('total', 0)

                # Attach damage_taken to matching player records added above
                for p in parsed_data['players']:
                    if (p['raid_id'] == report_code
                            and p['fight_id'] == fight['id']
                            and p['player_name'] in dt_by_player):
                        p['total_damage_taken'] = dt_by_player[p['player_name']]

        if report_has_valid_fights:
            parsed_data['raids'].append(raid_data)
        else:
            print(f"  Skipping report {report_code} — no valid raid fights found")

    return parsed_data


# Keep old name as an alias so any external callers don't break immediately.
fetch_weekly_data = fetch_season_data


if __name__ == '__main__':
    config.validate_config()
    data = fetch_season_data()
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"Fetched {len(data['raids'])} raids")
    print(f"Fetched {len(data['encounters'])} encounters")
    print(f"Fetched {len(data['players'])} player records")
    print(f"Fetched {len(data['deaths'])} death events")
    print(f"Fetched {len(data['externals'])} external defensive casts")
    print(f"{'='*60}")
