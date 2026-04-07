import time
import argparse
import numpy as np
import os
from PIL import Image
import cv2
import sys
import ffmpeg
from tqdm import tqdm
from itertools import groupby
import threading
from queue import Queue
import shutil

# -------------------------------
# RLE (run-length encoding) for bytes object (not implemented yet)
# -------------------------------
def rle_encode_bytes(data: bytes) -> bytes:
    encoded = bytearray()
    for byte_value, group in groupby(data):
        count = len(list(group))
        while count > 0:
            # Encode counts in chunks of 255 (max value for a single byte)
            current_count = min(count, 255)
            encoded.append(current_count)
            encoded.append(byte_value)
            count -= current_count
    return bytes(encoded)

# -------------------------------
# Decode bytewise run-length encoding (not implemented yet)
# -------------------------------
def rle_decode_bytes(encoded_data: bytes) -> bytes:
    decoded = bytearray()
    # Iterate over the encoded data in count, byte pairs
    for i in range(0, len(encoded_data), 2):
        count = encoded_data[i]
        byte_value = encoded_data[i+1]
        decoded.extend([byte_value] * count)
    return bytes(decoded)


# -------------------------------
# Fetch frame count from video metadata (fast, may be inaccurate)
# -------------------------------
def get_frame_count_metadata(video_path: str) -> int:
    probe = ffmpeg.probe(video_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    if video_stream and 'nb_frames' in video_stream:
        return int(video_stream['nb_frames'])
    return 0 # Or handle the error as appropriate

parser = argparse.ArgumentParser(description="Encoder/decoder utility for AVS (ASCII Video Stream) files")
parser.add_argument("action", help="enc/dec - the action for the utility to perform")
parser.add_argument("file", help="the file to encode or decode")
parser.add_argument("-w", "--width", help="width of output frames")
parser.add_argument("-b", "--brightness", help="exposure scale of output frames")
parser.add_argument("-r", "--framerate", help="framerate of output FILE")
parser.add_argument("-o", "--output", help="file to output frame data to (include extension)")

# -------------------------------
# AVS STANDARD CHARSET - DO NOT EDIT
# -------------------------------
cs5 = " .'`^\",:;Il!i~+_-?][}{1)(|\\/*tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

def clamp(n, min_val, max_val):
    return max(min_val, min(n, max_val))

# -------------------------------
# Convert single frame to ASCII + RGB bytes
# -------------------------------
def frame_to_ascii_fast(frame, width=120, charset=cs5, brightness=1):
    #path = os.path.expanduser(path)
    #frame = cv2.imread(path, cv2.IMREAD_COLOR)
    if frame is None:
        #raise FileNotFoundError(f"Cannot load image at: {path}")
        pass

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(frame)

    # Resize keeping aspect ratio
    w, h = image.size
    aspect_ratio = h / w
    new_height = max(1, int(aspect_ratio * width * 0.5))
    image = image.resize((width, new_height))

    arr = np.array(image)
    gray = brightness * (0.2126*arr[:,:,0] + 0.7152*arr[:,:,1] + 0.0722*arr[:,:,2])
    indices = np.clip((gray / 255 * (len(charset)-1)).astype(int), 0, len(charset)-1)

    chars = bytearray()
    colors = bytearray()
    for y in range(new_height):
        for x in range(width):
            chars.append(ord(charset[indices[y,x]]))
            #chars.append("█")
            r, g, b = arr[y,x]
            colors.extend([clamp(r, 0, 254), clamp(g, 0, 254), clamp(b, 0, 254)])

    return chars + colors, width, new_height


# -------------------------------
# Convert video input to AVS
# -------------------------------
def create_rgb_avs(file_path, width=32, frame_rate=1, version=3, charset=cs5, brightness=6, outfile="output.avs"):
    frames_count = get_frame_count_metadata(os.path.expanduser(file_path))
    cap = cv2.VideoCapture(os.path.expanduser(file_path))
    ret, frame = cap.read()
    ret_frame, w, h = frame_to_ascii_fast(frame, width, charset, brightness)
    header = b'AVS' + bytes([version])
    header += w.to_bytes(2, 'big') + h.to_bytes(2, 'big')
    header += bytes([frame_rate, 1, 3])  # charset_id=1, color_depth=3

    RED = rgb_ansi(255, 0, 0)
    GREEN = rgb_ansi(0, 255, 0)
    BLUE = rgb_ansi(0, 0, 255)
    ORANGE = rgb_ansi(252, 125, 1)
    RESET = "\033[0m"

    print("-------------------------")
    print("  avsutil - encode task  ")
    print("-------------------------")
    print(f"Metadata: \n\t{RED}Width{RESET}: {w}\n\t{RED}Height{RESET}: {h}\n\t{RED}Framecount{RESET} ({ORANGE}approx{RESET}): {frames_count}\n\t{RED}AVS Version{RESET}: {version}\n\t{RED}Framerate{RESET}: {frame_rate}\n\t{RED}Charset{RESET}: {GREEN}{charset}{RESET}\n\t{RED}Brightness mod{RESET}: {brightness}\n\t{RED}Color mode{RESET}: {[f"{rgb_ansi(255, 255, 255)}monochrome{RESET}", f"{ORANGE}ANSI{RESET}", f"24-bit {RED}R{GREEN}G{BLUE}B{RESET}"][version - 1]}")
    frame_idx = 0

    separator = b'\xFF'
    frames_data = bytearray()
    render_time = 0
    try:
        for i in tqdm(range(frames_count), desc=f"avsutil: Generating frames from file: {file_path.replace(os.path.expanduser('~'), '~', 1)}", unit="frames", colour='green'):
            render_start_time = time.time()
            ret, frame = cap.read()

            if not ret:
                break

            ret_frame, w, h = frame_to_ascii_fast(frame, width, charset, brightness)
            frame_bytes = w * h
            color_bytes = frame_bytes * 3
            frames_data += ret_frame + separator
            render_end_time = time.time()
            render_time = render_end_time - render_start_time
            status = f"avsutil: Created frame {rgb_ansi(255, 0, 0)}{frame_idx}\033[0m ({rgb_ansi(252, 125, 1)}{w}\033[0mx{rgb_ansi(252, 125, 1)}{h}\033[0m) in {rgb_ansi(0, 255, 0)}{((render_end_time - render_start_time)*1000):.3f}\033[0m ms"
            #sys.stdout.write('\r')
            #sys.stdout.write(' ' * len(status))
            #sys.stdout.write('\r')
            #sys.stdout.flush()
            #print(f"{status}", end='')
            frame_idx += 1
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()

    output_path = "output.avs"
    with open(outfile, 'wb') as f:
        f.write(header + frames_data)

    print(f"\nCreated {output_path} ({w}x{h}, {frames_count} frame(s) at {frame_rate} FPS)")

# -------------------------------
# ANSI 24-bit RGB escape
# -------------------------------
def rgb_ansi(r,g,b):
    return f"\033[38;2;{r};{g};{b}m"

# -------------------------------
# Queue frames so we don't have to preload all of them before playing
# -------------------------------
def queue_future_frames(data, queue, flag):
    while not flag.is_set():
        #size = shutil.get_terminal_size(fallback=(80, 24))
        version = data[3]
        width = int.from_bytes(data[4:6], 'big')
        height = int.from_bytes(data[6:8], 'big')
        fps = data[8]
        color_depth = data[10]

        frame_bytes = width * height
        color_bytes = frame_bytes * color_depth

        width = int.from_bytes(data[4:6], 'big')
        height = int.from_bytes(data[6:8], 'big')
        fps = data[8]
        color_depth = data[10]

        frame_bytes = width * height
        color_bytes = frame_bytes * color_depth

        raw_frames = data[11:].split(b'\xFF')
        frames = []
        #for raw in tqdm(raw_frames, desc=f"avsutil: Caching frames from file: {file_path.replace(os.path.expanduser('~'), '~', 1)}", unit="frames", colour='green'):
        for raw in raw_frames:
            #if not queue.full():
            if True:
                if len(raw) < frame_bytes + color_bytes:
                    continue
                chars = raw[:frame_bytes]
                colors = raw[frame_bytes:frame_bytes+color_bytes]
                frame = []
                for y in range(height):
                    #line = (' ' * ((size.columns // 2) - width // 2))
                    line = ""
                    for x in range(width):
                        idx = y*width + x
                        char = chr(chars[idx])
                        r, g, b = colors[idx*3:idx*3+3]
                        line += (f"{rgb_ansi(r,g,b)}{char}")
                    frame.append(line)
            #frames.append(frame)
                queue.put(frame)
            #else:
            #    try:
            #        while True:
            #            q.get_nowait()
            #            q.task_done() # Important if using q.join()
            #    except queue.Empty:
            #        pass
            #    continue
            #queue.put(None)
            #stop_event.wait(1)
    queue.put(None)
    print("\navsutil: Gracefully killing decoder...")


# -------------------------------
# Play AVS file in terminal
# -------------------------------
def play_rgb_avs(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    #size = shutil.get_terminal_size(fallback=(80, 24))

    queue = Queue(maxsize=10)

    if data[0:3] != b'AVS':
        raise ValueError("Not a valid .avs file")

    version = data[3]
    width = int.from_bytes(data[4:6], 'big')
    height = int.from_bytes(data[6:8], 'big')
    fps = data[8]
    color_depth = data[10]

    frame_bytes = width * height
    color_bytes = frame_bytes * color_depth

    raw_frames = data[11:].split(b'\xFF')
    #frames = []
    #for raw in tqdm(raw_frames, desc=f"avsutil: Caching frames from file: {file_path.replace(os.path.expanduser('~'), '~', 1)}", unit="frames", colour='green'):
    #    if len(raw) < frame_bytes + color_bytes:
    #        continue
    #    chars = raw[:frame_bytes]
    #    colors = raw[frame_bytes:frame_bytes+color_bytes]
    #    frame = []
    #    for y in range(height):
    #        line = ""
    #        for x in range(width):
    #            idx = y*width + x
    #            char = chr(chars[idx])
    #            r, g, b = colors[idx*3:idx*3+3]
    #            line += f"{rgb_ansi(r,g,b)}{char}"
    #        frame.append(line)
    #    frames.append(frame)
    kill_flag = threading.Event()
    decoder_thread = threading.Thread(target=queue_future_frames, daemon=True, args=(data, queue, kill_flag))
    decoder_thread.start()


    print("\033[H\033[J", end="")  # clear screen
    print("\033[?25l", end="")

    while decoder_thread.is_alive():
        try:
            #frames = queue.queue
            delay = 1 / fps
            #for frame in frames:
            frame = queue.get()
            #print("\033[?25l", end="")
            print("\033[H", end="")  # clear screen
            #print(f"{"\n" * ((size.lines // 2) - height // 2)}")
            print("\n".join(frame))
            time.sleep(delay)
            print("\033[0m")  # reset
        except KeyboardInterrupt, ValueError:
            print("\033[?25h", end="")
            kill_flag.set()
            break
    
    kill_flag.set()
    print("\033[?25h", end="")

# -------------------------------
# Parse argument for command-line tool
# -------------------------------
args = parser.parse_args()
if args.action == "enc":
    create_rgb_avs(os.path.expanduser(args.file), width=int(args.width), frame_rate=int(args.framerate), version=3, charset=cs5, brightness=int(args.brightness), outfile=args.output)
elif args.action == "dec":
    play_rgb_avs(args.file)
