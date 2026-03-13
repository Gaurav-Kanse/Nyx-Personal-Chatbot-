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
    print(f"[INIT] {init_msg}\n")  # temporary debug — shows what server expects
    init_data = json.loads(init_msg)
    conversation_id = init_data.get("conversation_initiation_metadata_event", {}).get("conversation_id", "unknown")
    print(f"[Session started | ID: {conversation_id}]\n")

    try:
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            # Send the user message
            ws.send(json.dumps({"user_message": user_input}))

            # Try all known VAD/turn-end signals
            ws.send(json.dumps({"type": "user_activity", "event": "speaking_stopped"}))
            ws.send(json.dumps({"type": "user_activity", "user_activity_event": {"activity": "text_input_end"}}))

            reply_parts = []
            got_response = False

            while True:
                raw = ws.recv()
                msg = json.loads(raw)
                msg_type = msg.get("type")

                print(f"  [DEBUG] type={msg_type} | {raw[:150]}")

                if msg_type == "agent_response":
                    text = msg.get("agent_response_event", {}).get("agent_response", "")
                    if text:
                        reply_parts.append(text)
                        got_response = True

                elif msg_type == "agent_response_correction":
                    text = msg.get("agent_response_correction_event", {}).get("corrected_agent_response", "")
                    if text:
                        reply_parts = [text]
                        got_response = True

                elif msg_type == "ping":
                    event_id = msg.get("ping_event", {}).get("event_id")
                    ws.send(json.dumps({"type": "pong", "event_id": event_id}))
                    if got_response:
                        break

                elif msg_type == "interruption":
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