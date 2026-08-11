// Deployado en Supabase como Edge Function "upload-match".
// Recibe partidas de LoL desde el .exe de LoL Centinela (autenticado solo con
// la publishable key, que es publica) y hace el insert usando la secret key
// del lado del servidor -- esa key nunca sale de Supabase.
import { createClient } from "npm:@supabase/supabase-js@2";

interface RiotPlayer {
  puuid?: string;
  riotIdGameName?: string;
  riotIdTagLine?: string;
  championName?: string;
  stats?: Record<string, number>;
}

interface RiotTeam {
  isBottomTeam?: boolean;
  players: RiotPlayer[];
}

interface MatchPayload {
  gameId: number | string;
  gameLength?: number;
  teams: RiotTeam[];
}

interface UploadRequestBody {
  tournament_id?: number;
  match?: MatchPayload;
  force?: boolean;
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function getSecretKey(): string {
  const raw = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (raw) {
    const parsed = JSON.parse(raw) as Record<string, string>;
    if (parsed.default) return parsed.default;
  }
  const legacy = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (legacy) return legacy;
  throw new Error("No secret key configured for this function.");
}

function getPublishableKeys(): string[] {
  const keys: string[] = [];
  const raw = Deno.env.get("SUPABASE_PUBLISHABLE_KEYS");
  if (raw) {
    const parsed = JSON.parse(raw) as Record<string, string>;
    keys.push(...Object.values(parsed));
  }
  const legacyAnon = Deno.env.get("SUPABASE_ANON_KEY");
  if (legacyAnon) keys.push(legacyAnon);
  return keys;
}

function stat(player: RiotPlayer, key: string): number | null {
  const value = player.stats?.[key];
  return value === undefined || value === null ? null : Number(value);
}

function playerName(player: RiotPlayer): string | null {
  if (player.riotIdGameName && player.riotIdTagLine) {
    return `${player.riotIdGameName}#${player.riotIdTagLine}`;
  }
  return player.riotIdGameName ?? null;
}

function teamName(team: RiotTeam): string {
  if (team.isBottomTeam === true) return "bottom";
  if (team.isBottomTeam === false) return "top";
  return "unknown";
}

function mapPlayerMatch(player: RiotPlayer, team: RiotTeam, gameId: string) {
  return {
    player_puuid: player.puuid ?? null,
    current_name: playerName(player),
    team: teamName(team),
    champion: player.championName ?? null,
    kills: stat(player, "CHAMPIONS_KILLED"),
    deaths: stat(player, "NUM_DEATHS"),
    assist: stat(player, "ASSISTS"),
    gold: stat(player, "GOLD_EARNED"),
    largest_killing_spree: stat(player, "LARGEST_KILLING_SPREE"),
    largest_critical: stat(player, "LARGEST_CRITICAL_STRIKE"),
    magic_damage_dealt: stat(player, "MAGIC_DAMAGE_DEALT_TO_CHAMPIONS"),
    magic_damage_taken: stat(player, "MAGIC_DAMAGE_TAKEN"),
    minions_killed: stat(player, "MINIONS_KILLED"),
    physical_damage_dealt: stat(player, "PHYSICAL_DAMAGE_DEALT_TO_CHAMPIONS"),
    physical_damage_taken: stat(player, "PHYSICAL_DAMAGE_TAKEN"),
    time_ccsing: stat(player, "TIME_CCING_OTHERS"),
    total_damage_dealt: stat(player, "TOTAL_DAMAGE_DEALT_TO_CHAMPIONS"),
    building_damage: stat(player, "TOTAL_DAMAGE_DEALT_TO_BUILDINGS"),
    healing_done: stat(player, "TOTAL_HEAL"),
    crowd_control_score: stat(player, "TOTAL_TIME_CROWD_CONTROL_DEALT"),
    damage_shielded: stat(player, "TOTAL_DAMAGE_SHIELDED_ON_TEAMMATES"),
    time_spent_dead: stat(player, "TOTAL_TIME_SPENT_DEAD"),
    match_id: gameId,
  };
}

function validateMatchPayload(match: MatchPayload): void {
  if (!Array.isArray(match.teams)) {
    throw new Error("match.teams debe ser una lista.");
  }
  match.teams.forEach((team, index) => {
    if (!Array.isArray(team.players)) {
      throw new Error(`match.teams[${index}].players debe ser una lista.`);
    }
    if (team.players.length < 1 || team.players.length > 5) {
      throw new Error(
        `match.teams[${index}].players debe tener entre 1 y 5 jugadores, tiene ${team.players.length}.`,
      );
    }
  });
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  const apiKey = req.headers.get("apikey");
  if (!apiKey || !getPublishableKeys().includes(apiKey)) {
    return jsonResponse({ error: "Falta o es invalido el header apikey." }, 401);
  }

  let body: UploadRequestBody;
  try {
    body = await req.json();
  } catch {
    return jsonResponse({ error: "Body invalido, se esperaba JSON." }, 400);
  }

  const tournamentId = body.tournament_id;
  const match = body.match;

  if (typeof tournamentId !== "number") {
    return jsonResponse({ error: "tournament_id (number) es obligatorio." }, 400);
  }
  if (!match || (typeof match.gameId !== "number" && typeof match.gameId !== "string")) {
    return jsonResponse({ error: "match.gameId es obligatorio." }, 400);
  }

  try {
    validateMatchPayload(match);
  } catch (error) {
    return jsonResponse({ error: (error as Error).message }, 400);
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
  const supabase = createClient(supabaseUrl, getSecretKey());
  const gameId = String(match.gameId);

  const { data: tournament, error: tournamentError } = await supabase
    .from("Tournament")
    .select("id")
    .eq("id", tournamentId)
    .maybeSingle();

  if (tournamentError) return jsonResponse({ error: tournamentError.message }, 500);
  if (!tournament) {
    return jsonResponse({ error: `tournament_id ${tournamentId} no existe.` }, 404);
  }

  if (!body.force) {
    const { data: existingPlayers, error: existingError } = await supabase
      .from("player_match")
      .select("id")
      .eq("match_id", gameId)
      .limit(1);

    if (existingError) return jsonResponse({ error: existingError.message }, 500);
    if (existingPlayers && existingPlayers.length > 0) {
      return jsonResponse({ ok: true, gameId, skipped: true, playerRows: 0 });
    }
  }

  const { error: upsertError } = await supabase
    .from("match")
    .upsert(
      { game_id: gameId, game_length: match.gameLength ?? null, tournament: tournamentId },
      { onConflict: "game_id" },
    );

  if (upsertError) return jsonResponse({ error: upsertError.message }, 500);

  const rows = match.teams.flatMap((team) =>
    team.players.map((player) => mapPlayerMatch(player, team, gameId))
  );

  if (rows.length > 0) {
    const { error: insertError } = await supabase.from("player_match").insert(rows);
    if (insertError) return jsonResponse({ error: insertError.message }, 500);
  }

  return jsonResponse({ ok: true, gameId, skipped: false, playerRows: rows.length });
});
