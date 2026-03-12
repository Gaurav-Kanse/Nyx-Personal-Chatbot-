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

    ws = websocket.create_connection(
        ws_url,
        header=[f"xi-api-key: {api_key}"]
    )

    # Read initial conversation_initiation_metadata
    init_msg = ws.recv()
    init_data = json.loads(init_msg)
    conversation_id = init_data.get("conversation_initiation_metadata_event", {}).get("conversation_id", "unknown")
    print(f"[Session started | ID: {conversation_id}]\n")

    try:
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            # Send user text message
            ws.send(json.dumps({
                "user_message": user_input
            }))

            # Collect agent response (may come in multiple chunks)
            reply_parts = []
            while True:
                raw = ws.recv()
                msg = json.loads(raw)
                msg_type = msg.get("type")

                if msg_type == "agent_response":
                    text = msg.get("agent_response_event", {}).get("agent_response", "")
                    if text:
                        reply_parts.append(text)

                elif msg_type == "agent_response_correction":
                    # Replace with corrected response
                    text = msg.get("agent_response_correction_event", {}).get("corrected_agent_response", "")
                    if text:
                        reply_parts = [text]

                elif msg_type == "interruption" or msg_type == "ping":
                    # Send pong to keep alive
                    if msg_type == "ping":
                        event_id = msg.get("ping_event", {}).get("event_id")
                        ws.send(json.dumps({"type": "pong", "event_id": event_id}))
                    continue

                elif msg_type == "conversation_initiation_metadata":
                    continue

                # Stop collecting once we have a full response
                if reply_parts:
                    break

            reply = " ".join(reply_parts).strip()
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