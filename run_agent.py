
import os
import json  # ### CAMBIO: Importar json ###
from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.transcriptions.language import Language
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams

load_dotenv(override=True)

# --- ### CAMBIO: Función para cargar el prompt desde el archivo ---
def load_system_prompt():
    """Lee el prompt del sistema desde config.json"""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get("system_prompt", "Error: No se encontró el prompt. Usando default.")
    except FileNotFoundError:
        logger.warning("config.json no encontrado. Usando prompt de emergencia.")
        return "Eres un asistente de IA. El archivo de configuración no se encontró."
    except json.JSONDecodeError:
        logger.error("Error al leer config.json. El archivo puede estar corrupto.")
        return "Eres un asistente de IA. Error al leer config."
# --- Fin del cambio ---


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"), language="es")
    cartesia_voice = os.getenv("CARTESIA_VOICE_ID", "15d0c2e2-8d29-44c3-be23-d585d5f154a1")
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id=cartesia_voice,
    )
    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), system_prompt="Responde siempre en español y usa un tono natural y conversacional.")

    # --- ### CAMBIO: Cargar el prompt dinámicamente ---
    system_prompt_from_ui = load_system_prompt()
    logger.info(f"Usando prompt del sistema: {system_prompt_from_ui[:50]}...") # Log para verificar

    print(system_prompt_from_ui, 'ass')
    messages = [
        {
            "role": "system",
            "content": system_prompt_from_ui, # Usar la variable en lugar de texto fijo
        },
    ]
    # --- Fin del cambio ---

    context = LLMContext(messages)
    context_aggregator = LLMContextAggregatorPair(context)
    
    # ... (el resto de tu script de pipeline no cambia)
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    pipeline = Pipeline(
        [
            transport.input(),
            rtvi,
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected")
        # debe instruir al bot sobre cómo empezar, o simplemente esperar al usuario.
        # Si AÚN quieres que el bot hable primero, puedes mantener esto:
        messages.append({"role": "system", "content": "Di hola y preséntate brevemente en español."})
        await task.queue_frames([LLMRunFrame()])
        # --- Fin del cambio ---

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for the bot starter."""
    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
        ),
    }
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main
    main()