import time
import threading
from queue import Queue
from avs_utils import rgb_ansi


class AVSDecoder:
    # -------------------------------
    # Queue frames so we don't have to preload all of them before playing
    # -------------------------------
    def _queue_future_frames(self, data, queue, flag):
        while not flag.is_set():
            version = data[3]
            width = int.from_bytes(data[4:6], "big")
            height = int.from_bytes(data[6:8], "big")
            fps = data[8]
            color_depth = data[10]

            frame_bytes = width * height
            color_bytes = frame_bytes * color_depth

            width = int.from_bytes(data[4:6], "big")
            height = int.from_bytes(data[6:8], "big")
            fps = data[8]
            color_depth = data[10]

            frame_bytes = width * height
            color_bytes = frame_bytes * color_depth

            raw_frames = data[11:].split(b"\xff")
            frames = []
            for raw in raw_frames:
                if True:
                    if len(raw) < frame_bytes + color_bytes:
                        continue
                    chars = raw[:frame_bytes]
                    colors = raw[frame_bytes : frame_bytes + color_bytes]
                    frame = []
                    for y in range(height):
                        line = ""
                        for x in range(width):
                            idx = y * width + x
                            char = chr(chars[idx])
                            r, g, b = colors[idx * 3 : idx * 3 + 3]
                            line += f"{rgb_ansi(r,g,b)}{char}"
                        frame.append(line)
                    queue.put(frame)
        queue.put(None)
        print("\navsutil: Gracefully killing decoder...")

    # -------------------------------
    # Play AVS file in terminal
    # -------------------------------
    def play_rgb_avs(self, file_path):
        with open(file_path, "rb") as f:
            data = f.read()

        if data[0:3] != b"AVS":
            raise ValueError("Not a valid .avs file")

        version = data[3]
        width = int.from_bytes(data[4:6], "big")
        height = int.from_bytes(data[6:8], "big")
        fps = data[8]
        color_depth = data[10]

        frame_bytes = width * height
        color_bytes = frame_bytes * color_depth

        queue = Queue(maxsize=(fps // 2))

        raw_frames = data[11:].split(b"\xff")

        kill_flag = threading.Event()
        decoder_thread = threading.Thread(
            target=self._queue_future_frames, daemon=True, args=(data, queue, kill_flag)
        )
        decoder_thread.start()

        print("\033[H\033[J", end="")  # clear screen
        print("\033[?25l", end="")

        frame_duration = 1 / fps
        next_frame_time = time.time()

        while decoder_thread.is_alive():
            try:
                frame = queue.get()

                print("\033[H", end="")
                print("\n".join(frame))
                print("\033[0m")

                next_frame_time += frame_duration
                sleep_time = next_frame_time - time.time()

                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    # skip delay if behind
                    next_frame_time = time.time()

            except (KeyboardInterrupt, ValueError):
                print("\033[?25h", end="")
                kill_flag.set()
                break
        kill_flag.set()
        print("\033[?25h", end="")
