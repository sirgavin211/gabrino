import socket
import time
from collections import deque

import cv2
import numpy as np


UDP_IP = "0.0.0.0"
UDP_PORT = 2222

RECV_BUF_BYTES = 4 * 1024 * 1024   # 4MB kernel receive buffer
SOCKET_TIMEOUT_S = 0.01            # 10ms — keeps the loop responsive
MAX_PACKET_BYTES = 3000            # payload packets larger than this are junk
WINDOW = "ESP32-CAM Stream"

# HUD colors (BGR).
GREEN = (0, 255, 0)
ORANGE = (0, 165, 255)
RED = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
GREY = (180, 180, 180)


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc & 0xFFFF


def draw_text(img, text, pos, scale, color, thickness=2):
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)


def make_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RECV_BUF_BYTES)
    sock.settimeout(SOCKET_TIMEOUT_S)
    return sock


def handle_window_key() -> bool:
    """True when the user pressed ESC (exit)."""
    return (cv2.waitKey(1) & 0xFF) == 27


def show_no_video_placeholder(seconds_since_frame: float) -> bool:
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    draw_text(img, "No video frames received", (20, 80), 0.9, WHITE)
    draw_text(img, f"Waiting: {seconds_since_frame:.1f}s", (20, 120), 0.7, GREY)
    draw_text(img, "Press 's' to send test.mp3", (20, 220), 0.7, YELLOW)
    draw_text(img, "Press ESC to exit", (20, 260), 0.7, WHITE)
    cv2.imshow(WINDOW, img)
    return handle_window_key()


def draw_stats(img, fps, loss_rate):
    loss_color = GREEN if loss_rate < 5 else ORANGE if loss_rate < 15 else RED
    draw_text(img, f"FPS: {fps:.1f}", (10, 30), 0.8, GREEN)
    draw_text(img, f"Resolution: {img.shape[1]}x{img.shape[0]}", (10, 60), 0.6, GREEN)
    draw_text(img, f"Loss: {loss_rate:.1f}%", (10, 90), 0.6, loss_color)
    draw_text(img, "Press 's' to send test.mp3", (10, 150), 0.6, YELLOW)
    if loss_rate > 15:
        draw_text(img, "HIGH PACKET LOSS!", (10, 180), 0.7, RED)


def main():
    sock = make_socket()
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)

    print(f"Listening on UDP port {UDP_PORT}...")
    print("Optimized for packet loss handling")

    buf = b""
    frame_len = 0
    frame_count = 0
    dropped_frames = 0
    crc_errors = 0

    start_time = time.time()
    last_frame_time = time.time()
    last_status_update = time.time()
    last_placeholder_draw = 0.0
    last_no_data_log = 0.0
    fps_samples = deque(maxlen=30)

    while True:
        try:
            data, _addr = sock.recvfrom(2048)
        except socket.timeout:
            now = time.time()
            seconds_since_frame = now - last_frame_time
            if seconds_since_frame > 2.0:
                if now - last_no_data_log > 2.0:
                    print("No data received for 2 seconds - waiting...")
                    last_no_data_log = now
                if now - last_placeholder_draw >= 0.05:
                    if show_no_video_placeholder(seconds_since_frame):
                        break
                    last_placeholder_draw = now
            continue
        except OSError as e:
            print(f"Socket error: {e}")
            continue

        # Header packet (4 bytes = frame length) — starts a new frame.
        if len(data) == 4:
            frame_len = int.from_bytes(data, "little")
            buf = b""
            continue

        # CRC packet (2 bytes = CRC16) — closes out the current frame.
        if len(data) == 2 and frame_len > 0:
            expected_crc = int.from_bytes(data, "little")

            if len(buf) == frame_len and crc16(buf) == expected_crc:
                img = cv2.imdecode(np.frombuffer(buf, dtype=np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    now = time.time()
                    frame_time = now - last_frame_time
                    last_frame_time = now
                    if frame_time > 0:
                        fps_samples.append(1.0 / frame_time)
                    fps = sum(fps_samples) / len(fps_samples) if fps_samples else 0
                    frame_count += 1

                    total = frame_count + dropped_frames + crc_errors
                    loss_rate = (dropped_frames + crc_errors) / total * 100 if total else 0

                    draw_stats(img, fps, loss_rate)
                    cv2.imshow(WINDOW, img)
                    if handle_window_key():
                        break
            elif len(buf) == frame_len:
                crc_errors += 1
                if time.time() - last_status_update > 2.0:
                    print(f"CRC error detected (total: {crc_errors})")
                    last_status_update = time.time()
            else:
                dropped_frames += 1
                if time.time() - last_status_update > 2.0:
                    print(f"Dropped incomplete frame (expected {frame_len}, got {len(buf)})")
                    last_status_update = time.time()

            frame_len = 0
            buf = b""
            continue

        # Payload packet — accumulate into the current frame buffer.
        if frame_len > 0:
            if len(data) > MAX_PACKET_BYTES:
                print(f"Warning: Dropping suspiciously large packet ({len(data)} bytes).")
                continue
            buf += data
            if len(buf) > frame_len * 1.5 + 10000:
                print(f"Buffer overflow/runaway - resetting (got {len(buf)}, expected {frame_len})")
                buf = b""
                frame_len = 0

    sock.close()
    cv2.destroyAllWindows()

    elapsed = time.time() - start_time
    total = frame_count + dropped_frames + crc_errors
    loss_rate = (dropped_frames + crc_errors) / total * 100 if total else 0
    print("\n--- Session Statistics ---")
    print(f"Total frames: {frame_count}")
    print(f"Dropped frames: {dropped_frames}")
    print(f"CRC errors: {crc_errors}")
    print(f"Average FPS: {frame_count / elapsed:.1f}")
    print(f"Packet loss rate: {loss_rate:.1f}%")


if __name__ == "__main__":
    main()
