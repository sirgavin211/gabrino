from dotenv import load_dotenv

# Load .env before importing auth — auth reads GABRINO_SECRET / GABRINO_DEVICE_TOKEN
# at import time.
load_dotenv()

from collections import deque
from flask import Flask, send_file, request, jsonify
import asyncio
import websockets
import threading
import sounddevice as sd
import time
from pydub import AudioSegment
import json
from urllib.parse import urlparse, parse_qs
import auth
from vision import main


app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    """Allow the frontend (dev server on another port) to call the API."""
    origin = request.headers.get("Origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def _token_from_request():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):].strip()
    return None


SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # bytes — 16-bit PCM
CHUNK_BYTES = 4096

audio_buffer = deque()

# All live WebSocket connections (web UI + robot). Movement commands from any
# client are relayed to every other client.
clients = set()


async def broadcast_movement(sender, message):
    """Relay a movement command to every connected client except the sender."""
    for client in list(clients):
        if client is sender:
            continue
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            clients.discard(client)


async def ping_loop(websocket):
    """Send periodic pings to keep the connection alive."""
    try:
        while True:
            await websocket.ping()
            await asyncio.sleep(20)
    except websockets.exceptions.ConnectionClosed:
        pass


def parse_json(message):
    """Parse a JSON message, or return None if it isn't valid JSON."""
    try:
        return json.loads(message)
    except json.JSONDecodeError:
        return None


def _token_from_ws(websocket):
    """Pull ?token=... from the WebSocket handshake URL."""
    try:
        query = urlparse(websocket.request.path).query
        return parse_qs(query).get("token", [None])[0]
    except Exception:
        return None


async def handle_websocket(websocket):
    # Require a valid session (or device) token before doing anything.
    user = auth.verify_token(_token_from_ws(websocket))
    if not user:
        print(f"[AUTH] Rejected unauthenticated WebSocket from {websocket.remote_address}")
        await websocket.close(code=4001, reason="unauthorized")
        return

    print(f"[DEBUG] WebSocket connected from {websocket.remote_address} as '{user}'")
    clients.add(websocket)
    asyncio.create_task(ping_loop(websocket))

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                audio_buffer.append(message)
                continue

            data = parse_json(message)
            # Relay control commands (movement + speed) straight to gabrino.
            if data and data.get("type") in ("movement", "speed"):
                print(f"[DEBUG] control: {data}")
                await broadcast_movement(websocket, message)
                continue

            print(f"[DEBUG] Received text message: {message}")
            if message == "send_audio":
                await websocket.send(json.dumps({"status": "test"}))
                await send_audio(websocket, "1.mp3")

    except websockets.exceptions.ConnectionClosed:
        print("[DEBUG] WebSocket connection closed")
    except Exception as e:
        print(f"[ERROR] WebSocket error: {e}")
    finally:
        clients.discard(websocket)


async def websocket_server_main():
    print("[DEBUG] Starting WebSocket server on port 8765...")
    async with websockets.serve(handle_websocket, "0.0.0.0", 8765):
        await asyncio.Future()


def mp3_to_pcm16k_mono(mp3_path):
    """Decode an MP3 to raw 16kHz mono 16-bit PCM (no WAV header)."""
    audio = AudioSegment.from_mp3(mp3_path)
    audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(CHANNELS).set_sample_width(SAMPLE_WIDTH)
    return audio.raw_data


async def send_audio(websocket, path):
    pcm_bytes = mp3_to_pcm16k_mono(path)
    for i in range(0, len(pcm_bytes), CHUNK_BYTES):
        await websocket.send(pcm_bytes[i:i + CHUNK_BYTES])
    await websocket.send("EOF")


def start_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(websocket_server_main())


def play_captured_audio():
    stream = sd.RawOutputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='int16',
        blocksize=0,
    )
    stream.start()
    while True:
        if len(audio_buffer) == 0:
            time.sleep(0.005)
            continue
        stream.write(audio_buffer.popleft())


@app.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return ("", 204)
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    if not auth.verify_password(username, password):
        return jsonify({"error": "invalid credentials"}), 401
    token = auth.create_token(username)
    return jsonify({"token": token, "username": username})


@app.route("/me", methods=["GET", "OPTIONS"])
def me():
    if request.method == "OPTIONS":
        return ("", 204)
    user = auth.verify_token(_token_from_request())
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"username": user})


@app.route("/health")
def health():
    return {"status": "ok", "audio_chunks_buffered": len(audio_buffer)}


@app.route("/1", methods=['GET'])
def audio_file():
    return send_file('1.mp3', mimetype='audio/mpeg')


if __name__ == '__main__':
    ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
    ws_thread.start()

    audio_thread = threading.Thread(target=play_captured_audio, daemon=True)
    audio_thread.start()

    camera_thread = threading.Thread(target=main, daemon=True)
    camera_thread.start()

    if not auth.has_users():
        print("[WARN] No users defined — nobody can log in. "
              "Create one:  python adduser.py <username>")

    print("[DEBUG] Starting Flask HTTP server on port 5000...")
    print("WS Thread and Audio Thread running.")
    app.run(host='0.0.0.0', port=5000, debug=False)
