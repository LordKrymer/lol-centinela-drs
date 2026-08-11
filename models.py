class PlayerData:
    """
    Represents cleaned, structured performance data for any player/bot.
    """

    def __init__(self, name: str, champion: str, kills: int, deaths: int, assists: int, damage: float, gold: int,
                 is_winner: bool):
        self.name = name if name else "Unknown/Bot"
        self.champion = champion
        self.kda_ratio = f"{kills}/{deaths}/{assists}"
        self.damage_dealt = damage
        self.gold_earned = gold
        self.is_winner = is_winner


class MatchSummary:
    """
    Unified Match Summary parser that handles both Player End-of-Game payloads
    and Live Spectator data payloads.
    """

    def __init__(self, raw_data: dict):
        # Detect source
        source = raw_data.get('DATA_SOURCE', 'PLAYER_EOG')
        self.players = []

        if source == 'PLAYER_EOG':
            # --- PARSER ORIGINAL PARA JUGADOR ---
            self.match_id = raw_data.get('gameId', 'Unknown')
            self.game_mode = raw_data.get('gameMode', 'UNKNOWN')
            duration_seconds = raw_data.get('gameLength', 0)
            self.duration_str = f"{duration_seconds // 60}m {duration_seconds % 60}s"

            teams = raw_data.get('teams', [])
            for team in teams:
                for p in team.get('players', []):
                    game_name = p.get('riotIdGameName')
                    name = game_name if game_name else p.get('summonerName')
                    stats = p.get('stats', {})

                    self.players.append(PlayerData(
                        name=name,
                        champion=p.get('championName', 'Unknown'),
                        kills=stats.get('CHAMPIONS_KILLED', 0),
                        deaths=stats.get('NUM_DEATHS', 0),
                        assists=stats.get('ASSISTS', 0),
                        damage=stats.get('TOTAL_DAMAGE_DEALT_TO_CHAMPIONS', 0),
                        gold=stats.get('GOLD_EARNED', 0),
                        is_winner=bool(stats.get('WIN', 0))
                    ))

        elif source == 'SPECTATOR_LIVE':
            game_data = raw_data.get('gameData', {})
            self.match_id = "LIVE_MATCH"
            self.game_mode = game_data.get('gameMode', 'SPECTATOR')
            duration_seconds = int(game_data.get('gameTime', 0))
            self.duration_str = f"{duration_seconds // 60}m {duration_seconds % 60}s (In Real-Time)"

            all_players = raw_data.get('allPlayers', [])
            for p in all_players:
                # En vivo, el KDA y el oro vienen dentro de 'scores'
                scores = p.get('scores', {})
                self.players.append(PlayerData(
                    name=p.get('summonerName', 'Unknown'),
                    champion=p.get('championName', 'Unknown'),
                    kills=scores.get('kills', 0),
                    deaths=scores.get('deaths', 0),
                    assists=scores.get('assists', 0),
                    damage=0,
                    gold=scores.get('gold', 0),
                    is_winner=True
                ))