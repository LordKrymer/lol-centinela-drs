from pathlib import Path

import customtkinter as ctk
import time

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class LoLTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LoL centinela")
        self.geometry("750x480")
        self.resizable(False, False)

        ruta_icono = Path(__file__).resolve().parent / "Riot_Ward.ico"
        if ruta_icono.exists():
            self.iconbitmap(str(ruta_icono))

        # Título de la App
        self.title_label = ctk.CTkLabel(
            self, text="LOL Centinela", font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(pady=15)

        # Estado del conector
        self.status_indicator = ctk.CTkLabel(
            self, text="● SERVICIO ACTIVO - MONITOREANDO CLIENTE DE RIOT",
            text_color="#2ecc71", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.status_indicator.pack(pady=5)

        # La caja de texto que reemplaza por completo a la consola
        self.log_textbox = ctk.CTkTextbox(self, width=690, height=300, activate_scrollbars=True)
        self.log_textbox.pack(pady=15)
        self.log_textbox.configure(state="disabled", font=("Consolas", 12))

        self.write_log("Interfaz gráfica modularizada inicializada con éxito.")

    def write_log(self, text: str):
        """Método seguro para hilos/asyncio que escribe en la consola visual."""

        def append():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", f"[{time.strftime('%H:%M:%S')}] {text}\n")
            self.log_textbox.configure(state="disabled")
            self.log_textbox.see("end")

        # .after(0, ...) asegura que la actualización corra en el hilo principal de Tkinter
        self.after(0, append)

    def mostrar_alerta_toxico(self, nombre_invocador: str, campeon: str, mensaje_personalizado: str):
        """Ventana flotante crítica para escrachar al transgresor."""

        def crear_alerta():
            alerta = ctk.CTkToplevel(self)
            alerta.title("⚠️ DETECTADO ⚠️")
            alerta.geometry("550x220")
            alerta.resizable(False, False)
            alerta.attributes("-topmost", True)

            frame_rojo = ctk.CTkFrame(alerta, fg_color="#c0392b", corner_radius=10)
            frame_rojo.pack(padx=15, pady=15, fill="both", expand=True)

            lbl_mensaje = ctk.CTkLabel(
                frame_rojo,
                text=f"{mensaje_personalizado}\nSU NOMBRE ------> {nombre_invocador.upper()}\n({campeon})",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="white",
                justify="center"
            )
            lbl_mensaje.pack(expand=True, pady=10)

            btn_cerrar = ctk.CTkButton(
                frame_rojo, text="Entendido (Mutear)",
                fg_color="#2c3e50", hover_color="#34495e", command=alerta.destroy
            )
            btn_cerrar.pack(pady=10)

        self.after(0, crear_alerta)