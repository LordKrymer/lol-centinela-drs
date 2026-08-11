# LoL Centinela

App de escritorio (GUI, `customtkinter`) que reemplaza el flujo manual de captura:
se conecta al cliente de League of Legends (LCU) mientras jugás, detecta fin de
partida (o modo espectador en vivo), limpia el JSON crudo y lo sube directo a
Supabase — sin exportar nada a mano, y sin que el usuario tenga que configurar
nada.

Usada por la comunidad **DRS** para cargar estadísticas de sus torneos
([TorneosDRS-Stats](https://github.com/LordKrymer/TorneosDRS-Stats)). Basada en
[lmq94/Lol-centinela](https://github.com/lmq94/Lol-centinela).

## Descargar

Últimos builds en [Releases](../../releases) — bajate el `.zip`, descomprimilo
y corré `LOL-centinela.exe`. No hace falta configurar nada: se conecta sola
al cliente de LoL y sube al torneo que esté marcado como activo.

## Arquitectura del upload

`upload_match_to_supabase.py` **no** habla directo con la base — le pega por
HTTP a una Edge Function de Supabase (`upload-match`, código en
`edge-function/index.ts`) que valida el payload e inserta en
`match`/`player_match` usando la secret key del lado del servidor. El script
solo necesita la **publishable key**, que es pública por diseño — por eso
está hardcodeada como constante en el propio archivo (`SUPABASE_URL`,
`SUPABASE_PUBLISHABLE_KEY`) en vez de pedirle a cada usuario que configure
credenciales. Ningún secreto viaja en el `.exe` que se reparte al equipo.

El `Tournament.id` a usar tampoco lo configura nadie: `fetch_active_tournament_id()`
le pregunta a Supabase cuál es el torneo activo en cada upload. Si no hay
ninguno activo en ese momento, el upload se salta con un log claro en vez de
romper.

Si necesitás redeployar la función después de tocarla:

```bash
supabase functions deploy upload-match --project-ref hbclvfrhfdekjstcrlas --no-verify-jwt
```

(`--no-verify-jwt` porque la función valida la publishable key a mano — las
keys nuevas de Supabase no son JWTs, así que la verificación automática no
aplica acá.)

## Setup (para desarrollar)

```bash
python -m venv .venv
.venv/Scripts/activate   # o source .venv/bin/activate en mac/linux
pip install -r requirements.txt
python main.py
```

Para uso manual/batch desde la CLI (`python upload_match_to_supabase.py
--json archivo.json`), `--tournament-id` existe como override opcional si
querés apuntar a un torneo puntual en vez del activo.

## Compilar el .exe

`LOL-centinela.spec` no empaqueta ningún `.env` (`datas` solo lleva el
ícono) — no hace falta, el script no tiene secretos ni configuración que
proteger. El `.exe` funciona standalone apenas se abre.

```bash
pip install pyinstaller
pyinstaller LOL-centinela.spec
```

El build queda en `dist/LOL-centinela/`.

⚠️ Si tu Python es una distribución no estándar (ej. Laragon), PyInstaller
puede tirar `WARNING: tkinter installation is broken. It will be excluded` y
armar un `.exe` que crashea al abrir (`ModuleNotFoundError: No module named
'tkinter'`) aunque `import tkinter` funcione bien normalmente. Si te pasa,
seteá `TCL_LIBRARY`/`TK_LIBRARY` apuntando a las carpetas `tcl8.6`/`tk8.6` de
tu instalación de Python antes de compilar:

```powershell
$env:TCL_LIBRARY = "<ruta a tu Python>\tcl\tcl8.6"
$env:TK_LIBRARY = "<ruta a tu Python>\tcl\tk8.6"
pyinstaller LOL-centinela.spec --noconfirm
```

Después de compilar, probá que la ventana abra antes de repartir el `.exe`.
