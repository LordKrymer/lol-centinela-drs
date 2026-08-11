# main.py
import asyncio
import threading
from app_gui import LoLTrackerApp
from extractor import LoLDataExtractor
from processor import process_raw_match_data


def iniciar_bucle_asyncio(loop, app):
    asyncio.set_event_loop(loop)

    async def lambda_callback(match_data):
        await process_raw_match_data(match_data, app)

    app.write_log("[SISTEMA] Conectando con el extractor LCU...")

    extractor = LoLDataExtractor(loop=loop, processing_callback=lambda_callback, app=app)

    extractor.connector.start()


def main():
    app = LoLTrackerApp()

    app.write_log("=======================================================")
    app.write_log("        MONITOR UNIVERSAL DE ESTADÍSTICAS LOL          ")
    app.write_log("=======================================================")
    app.write_log("[SISTEMA] Iniciando... Buscando proceso del League of Legends.")
    app.write_log("[SISTEMA] Si el juego está cerrado, abrilo para conectar.")

    loop = asyncio.new_event_loop()

    hilo_asyncio = threading.Thread(
        target=iniciar_bucle_asyncio,
        args=(loop, app),
        daemon=True
    )
    hilo_asyncio.start()

    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SISTEMA] Programa cerrado por el usuario. ¡Hasta luego!")