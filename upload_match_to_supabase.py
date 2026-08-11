from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_JSON_PATH = ROOT / "resources" / "example.json"

# Seguros de embeber en el .exe: la publishable key es publica por diseno
# (equivalente a la vieja "anon key"), no da acceso mas alla de lo que
# permiten las RLS policies. El insert real lo hace la Edge Function del
# lado del servidor, usando la secret key -- esa nunca sale de Supabase.
SUPABASE_URL = "https://hbclvfrhfdekjstcrlas.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_pLhDMr63Rpxal_uefPZjIg_ecpe_SXF"
UPLOAD_FUNCTION_URL = f"{SUPABASE_URL}/functions/v1/upload-match"
ACTIVE_TOURNAMENT_URL = f"{SUPABASE_URL}/rest/v1/Tournament?select=id&active=eq.true&limit=1"


class JsonUploaderError(RuntimeError):
    pass


def fetch_active_tournament_id() -> int:
    """Torneo activo segun Supabase -- los usuarios finales (0 tecnicos) no
    configuran ningun id a mano, la app lo resuelve sola en cada upload."""
    request = urllib.request.Request(
        ACTIVE_TOURNAMENT_URL,
        headers={"apikey": SUPABASE_PUBLISHABLE_KEY},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            rows = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise JsonUploaderError(
            f"No se pudo consultar el torneo activo ({exc.code}): {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise JsonUploaderError(f"No se pudo conectar con Supabase: {exc.reason}") from exc

    if not rows:
        raise JsonUploaderError("No hay ningun torneo activo en este momento.")

    return int(rows[0]["id"])


def read_matches(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return parse_matches_payload(payload)


def parse_matches_json(raw_json: str) -> list[dict[str, Any]]:
    return parse_matches_payload(json.loads(raw_json))


def parse_matches_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]

    raise ValueError("JSON root must be an object or a list of objects.")


def validate_match_payload(match_payload: dict[str, Any], strict_teams: bool) -> None:
    teams = match_payload.get("teams")
    if not isinstance(teams, list):
        raise ValueError("Match JSON must contain a 'teams' list.")

    if strict_teams and len(teams) != 2:
        raise ValueError(
            f"Expected exactly 2 teams for gameId={match_payload.get('gameId')}, got {len(teams)}."
        )

    for index, team in enumerate(teams):
        players = team.get("players")
        if not isinstance(players, list):
            raise ValueError(f"Team index {index} must contain a 'players' list.")
        if not 1 <= len(players) <= 5:
            raise ValueError(
                f"Team index {index} must contain between 1 and 5 players, got {len(players)}."
            )


def call_upload_function(
    tournament_id: int,
    match_payload: dict[str, Any],
    force: bool = False,
) -> dict[str, Any]:
    body = json.dumps(
        {"tournament_id": tournament_id, "match": match_payload, "force": force}
    ).encode("utf-8")

    request = urllib.request.Request(
        UPLOAD_FUNCTION_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "apikey": SUPABASE_PUBLISHABLE_KEY,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(detail).get("error", detail)
        except (json.JSONDecodeError, AttributeError):
            pass
        raise JsonUploaderError(f"Upload rechazado ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise JsonUploaderError(f"No se pudo conectar con la funcion de upload: {exc.reason}") from exc


def upload_match(
    match_payload: dict[str, Any],
    tournament_id: int,
    strict_teams: bool,
    force: bool = False,
) -> tuple[str, int, bool]:
    validate_match_payload(match_payload, strict_teams)
    result = call_upload_function(tournament_id, match_payload, force=force)
    return str(result["gameId"]), int(result.get("playerRows", 0)), bool(result.get("skipped", False))


async def upload_match_json(
    match_payload: dict[str, Any],
    reduced_match_payload: dict[str, Any] | None = None,
) -> tuple[str, int, bool]:
    import asyncio

    payload_to_upload = match_payload
    if match_payload.get("DATA_SOURCE") == "SPECTATOR_LIVE" and reduced_match_payload:
        payload_to_upload = reduced_match_payload

    def upload() -> tuple[str, int, bool]:
        try:
            return upload_match(
                match_payload=payload_to_upload,
                tournament_id=fetch_active_tournament_id(),
                strict_teams=False,
            )
        except JsonUploaderError:
            raise
        except Exception as exc:
            raise JsonUploaderError(str(exc)) from exc

    return await asyncio.to_thread(upload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sube partidas de LoL (JSON) a Supabase via la Edge Function upload-match."
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON_PATH,
        help=f"Path to a match JSON file. Default: {DEFAULT_JSON_PATH}",
    )
    parser.add_argument(
        "--json-data",
        help=(
            "Raw match JSON string. It can be a single match object or a list of match objects. "
            "When provided, --json is ignored."
        ),
    )
    parser.add_argument(
        "--tournament-id",
        type=int,
        default=None,
        help=(
            "Existing public.Tournament.id to associate with the uploaded matches. "
            "If omitted, uses whichever tournament is currently marked active."
        ),
    )
    parser.add_argument(
        "--allow-incomplete-teams",
        action="store_true",
        help="Allow JSON files with a team count different from 2. Useful for resources/example.json.",
    )
    parser.add_argument(
        "--force-insert-player-matches",
        action="store_true",
        help="Insert player_match rows even if rows already exist for this match.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    matches = parse_matches_json(args.json_data) if args.json_data else read_matches(args.json)
    tournament_id = args.tournament_id if args.tournament_id is not None else fetch_active_tournament_id()

    total_players = 0
    skipped_matches = 0
    for match_payload in matches:
        uploaded_game_id, player_count, skipped = upload_match(
            match_payload=match_payload,
            tournament_id=tournament_id,
            strict_teams=not args.allow_incomplete_teams,
            force=args.force_insert_player_matches,
        )
        if skipped:
            skipped_matches += 1
            print(
                f"Skipped gameId={uploaded_game_id}: "
                "player_match rows already exist."
            )
            continue

        total_players += player_count
        print(
            f"Uploaded gameId={uploaded_game_id} "
            f"with {player_count} player_match rows."
        )

    print(
        f"Done. Uploaded {len(matches) - skipped_matches} match(es), skipped {skipped_matches}, "
        f"and inserted {total_players} player row(s)."
    )


if __name__ == "__main__":
    main()
