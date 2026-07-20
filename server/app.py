from collections import deque
from flask import Flask, send_file
import asyncio
import websockets
import threading
import sounddevice as sd
import time
import io
from pydub import AudioSegment

app = Flask(__name__)

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2


audio_buffer = deque()


async def ping_loop(websocket):
    """Send periodic pings to keep connection alive."""
    try:
        while True:
            await websocket.ping()
            await asyncio.sleep(20)
    except:
        pass


async def handle_websocket(websocket):
    global audio_buffer
    print(f"[DEBUG] WebSocket connected from {websocket.remote_address}")
    asyncio.create_task(ping_loop(websocket))

    try:
        async for message in websocket:

            if isinstance(message, bytes):
                audio_buffer.append(message)

            elif isinstance(message, str):
                print(f"[DEBUG] Received text message: {message}")
                if(message == "send_audio"):
                    await send_audio(websocket, "1.mp3")

    except websockets.exceptions.ConnectionClosed:
        print("[DEBUG] WebSocket connection closed")
        
    except Exception as e:
        print(f"[ERROR] WebSocket error: {e}")


async def websocket_server_main():
    print("[DEBUG] Starting WebSocket server on port 8765...")
    async with websockets.serve(handle_websocket, "0.0.0.0", 8765):
        await asyncio.Future()



async def send_audio(websocket, filepath):
    filename = filepath.split('/')[-1]

    
    audio = AudioSegment.from_file(filepath)

    # Convert to match ESP32 I2S config: 16kHz, mono, 16-bit PCM
    audio = audio.set_frame_rate(16000)
    audio = audio.set_channels(1)
    audio = audio.set_sample_width(2)  

    raw_pcm = audio.raw_data

    chunk_size = 4096  # 4KB chunks
    stream = io.BytesIO(raw_pcm)

    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        await websocket.send(chunk)
        await asyncio.sleep(0.01)  # Small delay to prevent overwhelming

    print(f"Sent audio file back to client: {filename}")




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
        audio_data = audio_buffer.popleft()
        stream.write(audio_data) 




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

    print("[DEBUG] Starting Flask HTTP server on port 5000...")
    print("WS Thread and Audio Thread running.")
    app.run(host='0.0.0.0', port=5000, debug=False)






