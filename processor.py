
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from models import MatchSummary
from json_cleaner import MatchDataCleaner
from upload_match_to_supabase import JsonUploaderError, upload_match_json

def check_for_transgressors(match_data: dict, app) -> None:
    """Recorre los jugadores del JSON y abre la alerta si alguno es tóxico."""
    for team in match_data.get('teams', []):
        for player in team.get('players', []):
            stats = player.get('stats', {})
            was_toxic = stats.get("WAS_SEVERE_TRANSGRESSOR", 0) == 1
            was_premade_toxic = stats.get("WAS_PREMADE_WITH_SEVERE_TRANSGRESSOR", 0) == 1

            if was_toxic or was_premade_toxic:
                riot_name = player.get("riotIdGameName", "Desconocido").upper()
                champion = player.get("championName", "Campeón")

                if was_toxic:
                    msg = "Hubo un gordo sorete en la partida,"
                    app.write_log(f"⚠️ ¡ALERTA! DETECTADO GORDO SORETE: {riot_name} ({champion})")
                else:
                    msg = "Alerta: este jugador estaba en premade con un gordo sorete,"
                    app.write_log(f"⚠️ ¡ALERTA PREMADE! {riot_name} entró con un tóxico.")
                app.mostrar_alerta_toxico(riot_name, champion, msg)


def _get_compact_match_data(match_data: dict) -> dict:
    source = match_data.get('DATA_SOURCE', 'PLAYER_EOG')
    if source == 'PLAYER_EOG':
        return MatchDataCleaner.to_compact_format(match_data)
    if source == 'SPECTATOR_LIVE':
        return MatchDataCleaner.to_compact_spectator_format(match_data)
    return match_data


def _save_json_to_desktop(match_data: dict, reduced_match_data: dict, app) -> None:
    try:
        if getattr(sys, 'frozen', False):
            base_path = Path(sys.executable).parent
        else:
            base_path = Path(__file__).resolve().parent

        local_history_path = base_path / "historial"
        os.makedirs(local_history_path, exist_ok=True)
        # ----------------------------------------------

        source = match_data.get('DATA_SOURCE', 'PLAYER_EOG')

        if source == 'PLAYER_EOG':
            match_id = match_data.get('gameId', 'unknown')
            filename_original = f"match_{match_id}.json"
            filename_reducido = f"match_{match_id}-reducido.json"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_original = f"spectator_{timestamp}.json"
            filename_reducido = f"spectator_{timestamp}-reducido.json"

        file_path_original = local_history_path / filename_original
        file_path_reducido = local_history_path / filename_reducido

        with open(file_path_original, 'w', encoding='utf-8') as json_file:
            json.dump(match_data, json_file, ensure_ascii=False, indent=4)
        app.write_log(f"[SYSTEM] Original JSON saved locally: historial/{filename_original}")

        with open(file_path_reducido, 'w', encoding='utf-8') as json_file_red:
            json.dump(reduced_match_data, json_file_red, ensure_ascii=False, indent=4)
        app.write_log(f"[SYSTEM] Reduced JSON saved locally: historial/{filename_reducido}")

    except Exception as e:
        app.write_log(f"[ERROR] Could not save the JSON files: {e}")


def _print_match_table(match: MatchSummary, app) -> None:
    app.write_log(f"-> Match ID: {match.match_id} | Mode: {match.game_mode} | Duration: {match.duration_str}")
    app.write_log("-" * 75)
    app.write_log(f"{'Player Name':<16} | {'Champion':<12} | {'KDA':<7} | {'Damage':<8} | {'Gold':<6} | {'Result':<6}")
    app.write_log("-" * 75)

    for player in match.players:
        result_label = "WIN" if player.is_winner else "LOSS"
        app.write_log(
            f"{player.name:<16} | {player.champion:<12} | {player.kda_ratio:<7} | "
            f"{player.damage_dealt:<8,} | {player.gold_earned:<6,} | {result_label:<6}"
        )

    app.write_log("-" * 75)
    app.write_log("[PROCESADOR] End of object-oriented performance summary.\n")


async def process_raw_match_data(match_data: dict, app) -> None:
    app.write_log("[PROCESADOR] Raw match payload successfully received!")

    check_for_transgressors(match_data, app)

    reduced_match_data = _get_compact_match_data(match_data)
    _save_json_to_desktop(match_data, reduced_match_data, app)

    try:
        await upload_match_json(match_data, reduced_match_data)
        app.write_log("[REMOTO] La informacion de la partida en formato JSON fue enviada a la base de datos.")
    except JsonUploaderError as e:
        app.write_log(f"[REMOTO] Remote upload skipped: {e}")

    match = MatchSummary(match_data)
    _print_match_table(match, app)