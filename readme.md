
# Agente Pipecat — Custom Agent

Documento breve para entender, configurar y levantar este proyecto de agente conversacional localmente.

## Resumen

Este repositorio contiene un ejemplo de agente conversacional construido sobre la biblioteca `pipecat`.
El agente usa servicios de STT/TTS/LLM (Deepgram, Cartesia, OpenAI) y soporta transportes como WebRTC / Daily.

Archivos clave:
- `run_agent.py` — script principal que arma el pipeline del agente y arranca el runner.
- `config.json` — prompt del sistema configurable (ver sección abajo).
- `requirements.txt` — dependencias Python.
- `api_server.py` — (si existe) servidor HTTP complementario.

## Requisitos

- Python 3.11+ (recomendado). Probado en 3.11/3.12/3.13 en entornos virtuales.
- Git
- Conexión de red si usas servicios externos (OpenAI, Deepgram, Cartesia).

Recomendación: crea un entorno virtual y usa la versión del sistema o pyenv/conda si lo prefieres.

## Instalación (local)

1. Clona el repo (si aún no lo hiciste):

```bash
git clone <repo-url>
cd customAgent
```

2. Crea y activa un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instala dependencias:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. (Opcional) Si quieres reproducir el entorno usado por el desarrollador, instala las extras de `pipecat` ya listadas en `requirements.txt`.

## Variables de entorno

El agente requiere (según los servicios que utilices) varias variables de entorno. Las principales son:

- `OPENAI_API_KEY` — clave para el servicio LLM (si usas OpenAI).
- `DEEPGRAM_API_KEY` — clave para Deepgram STT.
- `CARTESIA_API_KEY` — clave para Cartesia TTS.
- `CARTESIA_VOICE_ID` — id de la voz a usar (opcional, hay un valor por defecto en el código).
- `SYSTEM_PROMPT` — (opcional) si está presente, sobreescribe el `system_prompt` de `config.json`.

Puedes poner estas variables en un archivo `.env` en la raíz (el proyecto ya carga `.env` con `python-dotenv`). Ejemplo `.env`:

```env
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=...
```

## `config.json`

El proyecto usa `config.json` (junto al script) para un `system_prompt` inicial. Formato esperado:

```json
{
	"system_prompt": "Eres un asistente llamado Lauro, eres formal y ayudas a las personas..."
}
```

Comportamiento del código:
- Si existe la variable de entorno `SYSTEM_PROMPT`, esta tiene prioridad y se usa en lugar de `config.json`.
- Si `config.json` no existe o está corrupto, se usa un prompt por defecto de emergencia y se registra un warning/error.

## Ejecutar localmente

Con el entorno virtual activado y las variables configuradas, ejecuta:

```bash
python run_agent.py
```

Esto invoca `main()` de `pipecat.runner.run` (tal y como está definido en `run_agent.py`) y arranca el pipeline.

Nota: algunos transportes (ej. WebRTC) requieren configuraciones adicionales (credenciales de TURN/STUN, o usar el playground de `pipecat`) para funcionar correctamente.

## Mensajes de debug comunes

- "Client not connected. Queuing app-message." — indica que se intentó enviar un frame antes de que el transporte marcara al cliente como listo. Soluciones:
	- Esperar unos instantes tras la conexión antes de encolar frames (el código ya aplica una pequeña pausa en `on_client_connected`).
	- Habilitar logs detallados del transporte para ver el ciclo de conexión.
	- Aumentar el tiempo de espera si tu red es lenta o si el cliente necesita más tiempo.

- Errores de credenciales / 401 — verifica las variables de entorno y las cuotas del servicio.

## Depuración y desarrollo

- Para añadir logs: `logger.debug(...)` / `logger.info(...)` ya está disponible con `loguru`.
- Si el pipeline no procesa audio, revisa que los servicios STT/TTS estén recibiendo paquetes y que `vad_analyzer` y `turn_analyzer` estén configurados correctamente.

## Tests (sencillo)

No hay tests automatizados incluidos por defecto en este repo. Para comprobar que el `system_prompt` se carga correctamente, puedes ejecutar:

```bash
python -c "from run_agent import load_system_prompt; print(load_system_prompt())"
```

Esto imprimirá el prompt que el agente usará (ya sea desde `SYSTEM_PROMPT` o desde `config.json`).

## Buenas prácticas y notas

- Mantén tus claves en `.env` (no en el repo).
- Si vas a desplegar en producción, considera secretos gestionados y limites de concurrencia para evitar costes inesperados.
- Si cambias el prompt con frecuencia, usar `SYSTEM_PROMPT` facilita el CI/CD sin tocar archivos.

Si quieres, puedo:
- Añadir tests unitarios mínimos para `load_system_prompt`.
- Documentar cómo configurar un transporte WebRTC/Daily paso a paso.
- Crear ejemplos de `.env.example` y plantillas para `config.json`.

---

Actualizado el README: guía rápida para levantar y entender el proyecto.
