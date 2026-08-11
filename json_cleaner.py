class MatchDataCleaner:
    """
    Clase especializada en transformar y estandarizar los JSON de LoL.
    Filtra y reduce la información para dejar el esqueleto limpio esperado.
    """

    @staticmethod
    def to_compact_format(raw_data: dict) -> dict:
        """
        [PARA JUGADOR - END OF GAME]
        Toma el JSON crudo de fin de juego y mantiene las estadísticas completas de los
        jugadores, pero reduce quirúrgicamente el bloque de estadísticas del equipo.
        """
        if not isinstance(raw_data, dict):
            return {}

        player_team = None
        for team in raw_data.get('teams', []):
            if team.get('isPlayerTeam') is True:
                player_team = team
                break

        if not player_team and raw_data.get('teams'):
            player_team = raw_data['teams'][0]

        compact_teams = []
        if player_team:
            raw_team_stats = player_team.get("stats", {})
            compact_team_stats = {
                "ASSISTS": raw_team_stats.get("ASSISTS", 0),
                "BARRACKS_KILLED": raw_team_stats.get("BARRACKS_KILLED", 0),
                "CAUSED_GAME_END_FROM_IGNB_SURRENDER": raw_team_stats.get("CAUSED_GAME_END_FROM_IGNB_SURRENDER", 0),
                "CHAMPIONS_KILLED": raw_team_stats.get("CHAMPIONS_KILLED", 0),
                "GAME_ENDED_IN_EARLY_SURRENDER": raw_team_stats.get("GAME_ENDED_IN_EARLY_SURRENDER", 0),
                "GAME_ENDED_IN_SURRENDER": raw_team_stats.get("GAME_ENDED_IN_SURRENDER", 0),
                "GOLD_EARNED": raw_team_stats.get("GOLD_EARNED", 0),
                "LARGEST_CRITICAL_STRIKE": raw_team_stats.get("LARGEST_CRITICAL_STRIKE", 0),
                "LARGEST_KILLING_SPREE": raw_team_stats.get("LARGEST_KILLING_SPREE", 0),
                "LARGEST_MULTI_KILL": raw_team_stats.get("LARGEST_MULTI_KILL", 0),
                "LEVEL": raw_team_stats.get("LEVEL", 0),
                "MAGIC_DAMAGE_DEALT_PLAYER": raw_team_stats.get("MAGIC_DAMAGE_DEALT_PLAYER", 0),
                "MAGIC_DAMAGE_DEALT_TO_CHAMPIONS": raw_team_stats.get("MAGIC_DAMAGE_DEALT_TO_CHAMPIONS", 0),
                "MAGIC_DAMAGE_TAKEN": raw_team_stats.get("MAGIC_DAMAGE_TAKEN", 0),
                "MINIONS_KILLED": raw_team_stats.get("MINIONS_KILLED", 0),
                "NEUTRAL_MINIONS_KILLED": raw_team_stats.get("NEUTRAL_MINIONS_KILLED", 0),
                "NUM_DEATHS": raw_team_stats.get("NUM_DEATHS", 0),
                "PHYSICAL_DAMAGE_DEALT_PLAYER": raw_team_stats.get("PHYSICAL_DAMAGE_DEALT_PLAYER", 0),
                "PHYSICAL_DAMAGE_DEALT_TO_CHAMPIONS": raw_team_stats.get("PHYSICAL_DAMAGE_DEALT_TO_CHAMPIONS", 0),
                "PHYSICAL_DAMAGE_TAKEN": raw_team_stats.get("PHYSICAL_DAMAGE_TAKEN", 0),
                "PLAYER_AUGMENT_1": raw_team_stats.get("PLAYER_AUGMENT_1", 0),
                "PLAYER_AUGMENT_2": raw_team_stats.get("PLAYER_AUGMENT_2", 0),
                "PLAYER_AUGMENT_3": raw_team_stats.get("PLAYER_AUGMENT_3", 0),
                "PLAYER_AUGMENT_4": raw_team_stats.get("PLAYER_AUGMENT_4", 0),
                "PLAYER_AUGMENT_5": raw_team_stats.get("PLAYER_AUGMENT_5", 0),
                "PLAYER_AUGMENT_6": raw_team_stats.get("PLAYER_AUGMENT_6", 0),
                "SPELL1_CAST": raw_team_stats.get("SPELL1_CAST", 0),
                "SPELL2_CAST": raw_team_stats.get("SPELL2_CAST", 0),
                "TEAM_EARLY_SURRENDERED": raw_team_stats.get("TEAM_EARLY_SURRENDERED", 0),
                "TEAM_OBJECTIVE": raw_team_stats.get("TEAM_OBJECTIVE", 0),
                "TIME_CCING_OTHERS": raw_team_stats.get("TIME_CCING_OTHERS", 0),
                "TOTAL_DAMAGE_DEALT": raw_team_stats.get("TOTAL_DAMAGE_DEALT", 0),
                "TOTAL_DAMAGE_DEALT_TO_BUILDINGS": raw_team_stats.get("TOTAL_DAMAGE_DEALT_TO_BUILDINGS", 0),
                "TOTAL_DAMAGE_DEALT_TO_CHAMPIONS": raw_team_stats.get("TOTAL_DAMAGE_DEALT_TO_CHAMPIONS", 0),
                "TOTAL_DAMAGE_DEALT_TO_OBJECTIVES": raw_team_stats.get("TOTAL_DAMAGE_DEALT_TO_OBJECTIVES", 0),
                "TOTAL_DAMAGE_DEALT_TO_TURRETS": raw_team_stats.get("TOTAL_DAMAGE_DEALT_TO_TURRETS", 0),
                "TOTAL_DAMAGE_SELF_MITIGATED": raw_team_stats.get("TOTAL_DAMAGE_SELF_MITIGATED", 0),
                "TOTAL_DAMAGE_SHIELDED_ON_TEAMMATES": raw_team_stats.get("TOTAL_DAMAGE_SHIELDED_ON_TEAMMATES", 0),
                "TOTAL_DAMAGE_TAKEN": raw_team_stats.get("TOTAL_DAMAGE_TAKEN", 0),
                "TOTAL_HEAL": raw_team_stats.get("TOTAL_HEAL", 0),
                "TOTAL_HEAL_ON_TEAMMATES": raw_team_stats.get("TOTAL_HEAL_ON_TEAMMATES", 0),
                "TOTAL_TIME_CROWD_CONTROL_DEALT": raw_team_stats.get("TOTAL_TIME_CROWD_CONTROL_DEALT", 0),
                "TOTAL_TIME_SPENT_DEAD": raw_team_stats.get("TOTAL_TIME_SPENT_DEAD", 0),
                "TRUE_DAMAGE_DEALT_PLAYER": raw_team_stats.get("TRUE_DAMAGE_DEALT_PLAYER", 0),
                "TRUE_DAMAGE_DEALT_TO_CHAMPIONS": raw_team_stats.get("TRUE_DAMAGE_DEALT_TO_CHAMPIONS", 0),
                "TRUE_DAMAGE_TAKEN": raw_team_stats.get("TRUE_DAMAGE_TAKEN", 0),
                "TURRETS_KILLED": raw_team_stats.get("TURRETS_KILLED", 0),
                "VISION_WARDS_BOUGHT_IN_GAME": raw_team_stats.get("VISION_WARDS_BOUGHT_IN_GAME", 0),
                "WAS_PREMADE_WITH_IGNB_GAME_END_CAUSER": raw_team_stats.get("WAS_PREMADE_WITH_IGNB_GAME_END_CAUSER", 0),
                "WAS_PREMADE_WITH_SEVERE_TRANSGRESSOR": raw_team_stats.get("WAS_PREMADE_WITH_SEVERE_TRANSGRESSOR", 0),
                "WAS_SEVERE_TRANSGRESSOR": raw_team_stats.get("WAS_SEVERE_TRANSGRESSOR", 0),
                "WIN": raw_team_stats.get("WIN", 1)
            }

            clean_team = {
                "isBottomTeam": player_team.get("isBottomTeam", False),
                "isPlayerTeam": player_team.get("isPlayerTeam", True),
                "isWinningTeam": player_team.get("isWinningTeam", False),
                "players": [],
                "stats": compact_team_stats,  # Las estadísticas filtradas
                "tag": player_team.get("tag", ""),
                "teamId": player_team.get("teamId", 100)
            }

            for p in player_team.get('players', []):
                clean_player = {
                    "championName": p.get("championName", "Unknown"),
                    "gameId": p.get("gameId", raw_data.get("gameId")),
                    "items": p.get("items", [0, 0, 0, 0, 0, 0, 0]),
                    "puuid": p.get("puuid", ""),
                    "riotIdGameName": p.get("riotIdGameName", "Unknown/Bot"),
                    "riotIdTagLine": p.get("riotIdTagLine", ""),
                    "spell1Id": p.get("spell1Id", 0),
                    "spell2Id": p.get("spell2Id", 0),
                    "stats": p.get("stats", {}),
                    "summonerId": p.get("summonerId", 0),
                    "teamId": p.get("teamId", clean_team["teamId"])
                }
                clean_team["players"].append(clean_player)
            compact_teams.append(clean_team)

        return {
            "gameId": raw_data.get("gameId"),
            "gameLength": raw_data.get("gameLength", 0),
            "teams": compact_teams,
            "DATA_SOURCE": "PLAYER_EOG"
        }

    @staticmethod
    def to_compact_spectator_format(live_data: dict) -> dict:
        """
        [PARA ESPECTADOR - LIVE GAME API]
        Mantiene la misma lógica estructural para el modo espectador.
        """
        if not isinstance(live_data, dict):
            return {}

        game_data = live_data.get("gameData", {})
        game_id = game_data.get("gameId")
        game_length = int(game_data.get("gameTime", 0))

        all_players = live_data.get("allPlayers", [])
        compact_players = []
        for p in all_players:
            clean_player = {
                "championName": p.get("championName", "Unknown"),
                "gameId": game_id,
                "items": [item.get("itemID", 0) for item in p.get("items", [])][:7],
                "puuid": p.get("puuid", ""),
                "riotIdGameName": p.get("riotIdGameName") or p.get("summonerName") or "Unknown/Bot",
                "riotIdTagLine": "",
                "spell1Id": 0,
                "spell2Id": 0,
                "stats": p.get("scores", {}),
                "summonerId": 0,
                "teamId": 100 if p.get("team") == "ORDER" else 200
            }
            compact_players.append(clean_player)

        simulated_team = {
            "isBottomTeam": True,
            "isPlayerTeam": False,
            "isWinningTeam": False,
            "players": compact_players,
            "stats": {
                "CHAMPIONS_KILLED": 0,
                "GOLD_EARNED": 0,
                "WIN": 0
            },
            "tag": "",
            "teamId": 100
        }

        return {
            "gameId": game_id,
            "gameLength": game_length,
            "teams": [simulated_team],
            "DATA_SOURCE": "SPECTATOR_LIVE"
        }