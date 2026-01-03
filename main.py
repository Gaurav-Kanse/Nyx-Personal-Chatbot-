import os
import signal
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from sounddevice_audio import SoundDeviceAudioInterface
from tools import client_tools


load_dotenv()

agent_id = os.getenv("AGENT_ID")
api_key = os.getenv("ELEVENLABS_API_KEY")


elevenlabs = ElevenLabs(api_key=api_key)

audio_interface = SoundDeviceAudioInterface()

conversation = Conversation(
    elevenlabs,
    agent_id,
    client_tools= client_tools,
    requires_auth=bool(api_key),
    audio_interface=audio_interface,

    callback_agent_response=lambda r: print(f"Agent: {r}"),
    callback_agent_response_correction=lambda o, c: print(f"Agent: {o} -> {c}"),
    callback_user_transcript=lambda t: print(f"User: {t}"),
)

conversation.start_session()


signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())

conversation_id = conversation.wait_for_session_end()
print(f"Conversation ID: {conversation_id}")
