# LoL Centinela

App de escritorio (GUI, `customtkinter`) que reemplaza el flujo manual de captura:
se conecta al cliente de League of Legends (LCU) mientras jugás, detecta fin de
partida (o modo espectador en vivo), limpia el JSON crudo y lo sube directo a
Supabase — sin exportar nada a mano.

Usada por la comunidad **DRS** para cargar estadísticas de sus torneos
([TorneosDRS-Stats](https://github.com/LordKrymer/TorneosDRS-Stats)). Basada en
[lmq94/Lol-centinela](https://github.com/lmq94/Lol-centinela).

## Descargar

Últimos builds en [Releases](../../releases) — bajate el `.zip`, descomprimilo
y corré `LOL-centinela.exe`. Completá `.env` (copiá `.env.example`) con el
`SUPABASE_TOURNAMENT_ID` del torneo en el que estés jugando antes de abrirlo.

## Arquitectura del upload

`upload_match_to_supabase.py` **no** habla directo con la base — le pega por
HTTP a una Edge Function de Supabase (`upload-match`, código en
`edge-function/index.ts`) que valida el payload e inserta en
`match`/`player_match` usando la secret key del lado del servidor. El script
solo necesita la **publishable key**, que es pública por diseño — por eso
está hardcodeada como constante en el propio archivo (`SUPABASE_URL`,
`SUPABASE_PUBLISHABLE_KEY`) en vez de pedirle a cada usuario que configure
credenciales. Ningún secreto viaja en el `.exe` que se reparte al equipo.

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
cp .env.example .env     # completar SUPABASE_TOURNAMENT_ID
python main.py
```

`SUPABASE_TOURNAMENT_ID` es el `Tournament.id` al que se van a asociar las
partidas que capture esta instancia — un `.env` por torneo/evento. No es
sensible (es solo un número), así que cada usuario puede tener el suyo al
lado del `.exe` sin ningún riesgo si se comparte o se pierde.

## Compilar el .exe

`LOL-centinela.spec` no empaqueta ningún `.env` (`datas` solo lleva el
ícono) — no hace falta, porque el script no tiene secretos que proteger.
Cada usuario pone su propio `.env` (con su `SUPABASE_TOURNAMENT_ID`) al lado
del `.exe` compilado, sin necesidad de recompilar por evento.

```bash
pip install pyinstaller
pyinstaller LOL-centinela.spec
```

El build queda en `dist/LOL-centinela/`.
