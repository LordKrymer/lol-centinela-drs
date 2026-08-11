
import asyncio
import aiohttp
from lcu_driver import Connector


class LoLDataExtractor:
    def __init__(self, loop: asyncio.AbstractEventLoop, processing_callback, app=None):
        self.connector = Connector(loop=loop)
        self.callback = processing_callback
        self.app = app
        self._is_match_processed = False

        self.PHASE_MESSAGES = {
            "None": "Esperando en el menú principal o inactivo...",
            "Lobby": "Estás en la sala de espera (Lobby)...",
            "Matchmaking": "Buscando partida activa...",
            "ReadyCheck": "¡Partida encontrada! Esperando que todos acepten...",
            "ChampSelect": "Estás en la selección de campeones...",
            "GameStart": "La partida está iniciando (Pantalla de carga)...",
            "InProgress": "Partida en curso...",
            "WaitingForStats": "Esperando el bloque de estadísticas final...",
            "PreEndOfGame": "La partida terminó. Conectando con la API...",
            "EndOfGame": "Partida finalizada. Extrayendo estadísticas...",
            "Spectating": "Modo Espectador detectado..."
        }

        self.connector.ready(self._on_client_ready)
        self.connector.close(self._on_client_close)

        @self.connector.ws.register('/lol-gameflow/v1/gameflow-phase', event_types=('UPDATE',))
        async def gameflow_changed(conn, event):
            await self._evaluate_phase(conn, event.data)

    def _log(self, message: str):
        """Método auxiliar para decidir si imprime en consola o escribe en la GUI"""
        if self.app:
            self.app.write_log(message)
        else:
            print(message)

    async def _on_client_ready(self, connection) -> None:
        self._log("=======================================================")
        self._log("[SISTEMA] Conectado con éxito al cliente de LoL.")
        self._log("[SISTEMA] Escuchando eventos del juego... No cierres esta ventana.")
        self._log("=======================================================")
        self._is_match_processed = False

    async def _on_client_close(self, connection) -> None:
        self._log("[SISTEMA] El cliente de LoL se ha cerrado.")
        self._log("[SISTEMA] Intentando reconectar automáticamente cuando abras el juego...")

    async def _evaluate_phase(self, connection, current_phase: str) -> None:
        friendly_message = self.PHASE_MESSAGES.get(current_phase, f"Fase actual: {current_phase}")
        self._log(f"[ESTADO] LoL -> {friendly_message}")

        # Resetear el candado si volvemos al menú o lobby
        if current_phase in ["None", "Lobby", "Matchmaking", "ChampSelect"]:
            if self._is_match_processed:
                self._log("[SISTEMA] Listo para la próxima partida. Monitoreo reactivado...")
                self._is_match_processed = False

        if current_phase in ["InProgress", "Spectating"] and not self._is_match_processed:
            gameflow_session = await connection.request('GET', '/lol-gameflow/v1/session')
            if gameflow_session.status == 200:
                session_data = await gameflow_session.json()
                is_spectator = session_data.get('gameData', {}).get('isSpectating', False)

                if is_spectator:
                    self._is_match_processed = True
                    self._log("[PROCESO] ¡Confirmado modo Espectador! Conectando a la Live Game API (Espera 5 seg)...")
                    await asyncio.sleep(5)
                    await self._extract_live_spectator_data()
                else:
                    self._log("[ESTADO] LoL -> Estás jugando la partida actualmente (Esperando el final)...")

        if current_phase == "EndOfGame" and not self._is_match_processed:
            self._is_match_processed = True
            self._log("[PROCESO] ¡Fin de partida detectado como jugador! Descargando datos...")

            response = await connection.request('GET', '/lol-end-of-game/v1/eog-stats-block')
            if response.status == 200:
                payload = await response.json()
                payload['DATA_SOURCE'] = 'PLAYER_EOG'
                await self.callback(payload)
            else:
                self._log("[ERROR] No se pudieron obtener las estadísticas de fin de juego.")

    async def _extract_live_spectator_data(self) -> None:
        """Helper para pegarle a la API local de juego en vivo de Riot"""
        live_url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.get(live_url) as response:
                    if response.status == 200:
                        payload = await response.json()
                        payload['DATA_SOURCE'] = 'SPECTATOR_LIVE'
                        await self.callback(payload)
                    else:
                        self._log(f"[ALERTA] La Live API respondió con código de error: {response.status}")
            except Exception as e:
                self._log(f"[ERROR] No se pudo conectar a la Live API de espectador: {e}")