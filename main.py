import os
import signal
import json
import websocket
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


def text_mode_loop():
    print("🔇 Running in TEXT MODE — mic unavailable.")
    print("Type your messages below (Ctrl+C to quit):\n")

    ws_url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}"
    ws = websocket.create_connection(ws_url, header=[f"xi-api-key: {api_key}"])

    init_msg = ws.recv()
    init_data = json.loads(init_msg)
    conversation_id = init_data.get("conversation_initiation_metadata_event", {}).get("conversation_id", "unknown")
    print(f"[Session started | ID: {conversation_id}]\n")

    try:
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            ws.send(json.dumps({"type": "user_message", "text": user_input}))
            ws.send(json.dumps({"type": "user_activity"}))

            reply = None
            audio_count = 0

            while True:
                raw = ws.recv()
                msg = json.loads(raw)
                msg_type = msg.get("type")

                if msg_type == "agent_response":
                    # Always take the latest agent_response as the full reply
                    reply = msg.get("agent_response_event", {}).get("agent_response", "")

                elif msg_type == "agent_response_correction":
                    reply = msg.get("agent_response_correction_event", {}).get("corrected_agent_response", reply)

                elif msg_type == "audio":
                    audio_count += 1
                    # Audio chunks stream in multiples — wait until we have the reply text
                    # then break on the ping that follows
                    
                elif msg_type == "ping":
                    event_id = msg.get("ping_event", {}).get("event_id")
                    ws.send(json.dumps({"type": "pong", "event_id": event_id}))
                    # Only break if we've already received a reply
                    if reply is not None:
                        break

                elif msg_type == "interruption":
                    break

            if reply:
                print(f"Nyx: {reply}\n")

    except KeyboardInterrupt:
        print("\nEnding session...")
    finally:
        ws.close()
        print(f"Conversation ID: {conversation_id}")


if not audio_interface.available:
    text_mode_loop()
else:
    conversation = Conversation(
        elevenlabs,
        agent_id,
        client_tools=client_tools,
        requires_auth=bool(api_key),
        audio_interface=audio_interface,
        callback_agent_response=lambda r: print(f"Nyx: {r}"),
        callback_agent_response_correction=lambda o, c: print(f"Nyx: {o} -> {c}"),
        callback_user_transcript=lambda t: print(f"You: {t}"),
    )

    conversation.start_session()
    signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())
    conversation_id = conversation.wait_for_session_end()
    print(f"Conversation ID: {conversation_id}")