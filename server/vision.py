import os
import socket
import time
from collections import deque

import cv2
import numpy as np


UDP_IP = "0.0.0.0"
UDP_PORT = 2222

# Create socket with larger buffer
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)  # 4MB buffer
sock.settimeout(0.01)  # 10ms timeout for responsive loop

buf = b""
frame_len = 0

frame_count = 0
dropped_frames = 0
crc_errors = 0
start_time = time.time()
last_frame_time = time.time()
fps_samples = deque(maxlen=30)
last_status_update = time.time()

print(f"Listening on UDP port {UDP_PORT}...")
print("Optimized for packet loss handling")


def crc16(data: bytes):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc & 0xFFFF


cv2.namedWindow("ESP32-CAM Stream", cv2.WINDOW_NORMAL)


#send test mp3 to hardware
def handle_window_key() -> bool:

    key = cv2.waitKey(1) & 0xFF

    if key == 27:  # ESC to exit
        return True
    if key == ord("s"):
        pass
    return False


def show_no_video_placeholder(
    test_mp3_path: str,
    seconds_since_frame: float,
) -> bool:
    img = np.zeros((480, 640, 3), dtype=np.uint8)

    cv2.putText(
        img,
        "No video frames received",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        img,
        f"Waiting: {seconds_since_frame:.1f}s",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (180, 180, 180),
        2,
    )
    cv2.putText(
        img,
        "Press 's' to send test.mp3",
        (20, 220),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2,
    )
    cv2.putText(
        img,
        "Press ESC to exit",
        (20, 260),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )

    cv2.imshow("ESP32-CAM Stream", img)

    return handle_window_key()


def main():
    global last_frame_time
    global buf
    global frame_len
    global dropped_frames
    global crc_errors
    global frame_count
    global last_status_update

    expected_crc = None

    test_mp3_path = os.path.join(os.path.dirname(__file__), "test.mp3")
    last_placeholder_draw = 0.0
    last_no_data_log = 0.0

    print("Press 's' in stream window to send test.mp3 play request to hardware")

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
                    if show_no_video_placeholder( test_mp3_path, seconds_since_frame):
                        break
                    last_placeholder_draw = now
            continue
        except Exception as e:
            print(f"Socket error: {e}")
            continue

        # Header packet (4 bytes = frame length)
        if len(data) == 4:
            frame_len = int.from_bytes(data, "little")
            buf = b""
            expected_crc = None
            continue

        # CRC packet (2 bytes = CRC16)
        if len(data) == 2 and frame_len > 0:
            expected_crc = int.from_bytes(data, "little")

            if len(buf) == frame_len:
                actual_crc = crc16(buf)

                if actual_crc == expected_crc:
                    arr = np.frombuffer(buf, dtype=np.uint8)
                    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

                    if img is not None:
                        now = time.time()
                        frame_time = now - last_frame_time
                        last_frame_time = now

                        if frame_time > 0:
                            fps_samples.append(1.0 / frame_time)

                        fps = sum(fps_samples) / len(fps_samples) if fps_samples else 0
                        frame_count += 1

                        total_attempts = frame_count + dropped_frames + crc_errors
                        loss_rate = (
                            (dropped_frames + crc_errors) / total_attempts * 100
                            if total_attempts > 0
                            else 0
                        )

                        cv2.putText(
                            img,
                            f"FPS: {fps:.1f}",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 0),
                            2,
                        )
                        cv2.putText(
                            img,
                            f"Resolution: {img.shape[1]}x{img.shape[0]}",
                            (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            2,
                        )
                        cv2.putText(
                            img,
                            f"Loss: {loss_rate:.1f}%",
                            (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0)
                            if loss_rate < 5
                            else (0, 165, 255)
                            if loss_rate < 15
                            else (0, 0, 255),
                            2,
                        )

                        cv2.putText(
                            img,
                            "Press 's' to send test.mp3",
                            (10, 150),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 0),
                            2,
                        )

                        if loss_rate > 15:
                            cv2.putText(
                                img,
                                "HIGH PACKET LOSS!",
                                (10, 180),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                (0, 0, 255),
                                2,
                            )

                        cv2.imshow("ESP32-CAM Stream", img)

                        if handle_window_key():
                            break
                else:
                    crc_errors += 1
                    if time.time() - last_status_update > 2.0:
                        print(f"CRC error detected (total: {crc_errors})")
                        last_status_update = time.time()
            else:
                dropped_frames += 1
                if time.time() - last_status_update > 2.0:
                    print(
                        f"Dropped incomplete frame (expected {frame_len}, got {len(buf)})"
                    )
                    last_status_update = time.time()

            frame_len = 0
            buf = b""
            expected_crc = None
            continue

        if frame_len > 0:
            if len(data) > 3000:
                print(f"Warning: Dropping suspiciously large packet ({len(data)} bytes).")
                continue

            buf += data

            if len(buf) > frame_len * 1.5 + 10000 and frame_len > 0:
                print(f"Buffer overflow/runaway - resetting (got {len(buf)}, expected {frame_len})")
                buf = b""
                frame_len = 0
                expected_crc = None
                continue

    sock.close()
    cv2.destroyAllWindows()

    elapsed = time.time() - start_time
    print("\n--- Session Statistics ---")
    print(f"Total frames: {frame_count}")
    print(f"Dropped frames: {dropped_frames}")
    print(f"CRC errors: {crc_errors}")
    print(f"Average FPS: {frame_count / elapsed:.1f}")
    print(
        "Packet loss rate: "
        f"{((dropped_frames + crc_errors) / (frame_count + dropped_frames + crc_errors) * 100):.1f}%"
    )


if __name__ == "__main__":
    main()
