import time
import numpy as np
import os
from typing import Tuple, Optional
from PIL import Image
import cv2
import ffmpeg
from tqdm import tqdm
from avs_utils import CS5, clamp, rgb_ansi


class AVSEncoder:
    def __init__(
        self,
        width: int = 120,
        frame_rate: int = 1,
        version: int = 3,
        charset: str = CS5,
        brightness: int = 1,
    ) -> None:
        self.width = width
        self.frame_rate = frame_rate
        self.version = version
        self.charset = charset
        self.brightness = brightness

    def _get_frame_count_metadata(self, video_path: str) -> int:
        probe = ffmpeg.probe(video_path)
        video_stream = next(
            (stream for stream in probe["streams"] if stream["codec_type"] == "video"),
            None,
        )
        if video_stream and "nb_frames" in video_stream:
            return int(video_stream["nb_frames"])
        return 0

    def _frame_to_ascii_fast(
        self, frame: Optional[np.ndarray]
    ) -> Tuple[bytearray, int, int]:
        if frame is None:
            return bytearray(), 0, 0

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)

        # aspect ratio preserving resize
        w, h = image.size
        aspect_ratio = h / w
        new_height = max(1, int(aspect_ratio * self.width * 0.5))
        image = image.resize((self.width, new_height))

        arr = np.array(image)
        gray = self.brightness * (
            0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
        )
        indices = np.clip(
            (gray / 255 * (len(self.charset) - 1)).astype(int), 0, len(self.charset) - 1
        )

        chars = bytearray()
        colors = bytearray()
        for y in range(new_height):
            for x in range(self.width):
                chars.append(ord(self.charset[indices[y, x]]))
                r, g, b = arr[y, x]
                colors.extend([clamp(r, 0, 254), clamp(g, 0, 254), clamp(b, 0, 254)])

        return chars + colors, self.width, new_height

    def encode(self, file_path: str, outfile: str = "output.avs") -> None:
        expanded_path = os.path.expanduser(file_path)
        frames_count = self._get_frame_count_metadata(expanded_path)
        cap = cv2.VideoCapture(expanded_path)

        ret, frame = cap.read()
        if frame is None:
            # Handle empty video or failed read
            cap.release()
            return

        ret_frame, w, h = self._frame_to_ascii_fast(frame)
        header = b"AVS" + bytes([self.version])
        header += w.to_bytes(2, "big") + h.to_bytes(2, "big")
        header += bytes([self.frame_rate, 1, 3])  # charset_id=1, color_depth=3

        RED = rgb_ansi(255, 0, 0)
        GREEN = rgb_ansi(0, 255, 0)
        BLUE = rgb_ansi(0, 0, 255)
        ORANGE = rgb_ansi(252, 125, 1)
        RESET = "\033[0m"

        print("-------------------------")
        print("  avsutil - encode task  ")
        print("-------------------------")
        print(
            f'Metadata: \n\t{RED}Width{RESET}: {w}\n\t{RED}Height{RESET}: {h}\n\t{RED}Framecount{RESET} ({ORANGE}approx{RESET}): {frames_count}\n\t{RED}AVS Version{RESET}: {self.version}\n\t{RED}Framerate{RESET}: {self.frame_rate}\n\t{RED}Charset{RESET}: {GREEN}{self.charset}{RESET}\n\t{RED}Brightness mod{RESET}: {self.brightness}\n\t{RED}Color mode{RESET}: {[f"{rgb_ansi(255, 255, 255)}monochrome{RESET}", f"{ORANGE}ANSI{RESET}", f"24-bit {RED}R{GREEN}G{BLUE}B{RESET}"][self.version - 1]}'
        )

        frame_idx = 0
        separator = b"\xff"
        frames_data = bytearray()

        try:
            for i in tqdm(
                range(frames_count),
                desc=f"avsutil: Generating frames from file: {file_path.replace(os.path.expanduser('~'), '~', 1)}",
                unit="frames",
                colour="green",
            ):
                render_start_time = time.time()
                ret, frame = cap.read()

                if not ret:
                    break

                ret_frame, w, h = self._frame_to_ascii_fast(frame)
                frames_data += ret_frame + separator
                render_end_time = time.time()
                frame_idx += 1
        except KeyboardInterrupt:
            pass
        finally:
            cap.release()

        with open(outfile, "wb") as f:
            f.write(header + frames_data)

        print(
            f"\nCreated {outfile} ({w}x{h}, {frames_count} frame(s) at {self.frame_rate} FPS)"
        )
