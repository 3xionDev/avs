from itertools import groupby
from typing import Union

# -------------------------------
# AVS STANDARD CHARSET - DO NOT EDIT
# -------------------------------
CS5: str = " `'.,:;\"^-_~+<>i!lI?/\\|()[]{}1tfjrxnuvczXYJLTFSykaeohpqdb#*=%SOGUVCAEPRKHMNDBQ0WZ@&$"


def clamp(
    n: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]
) -> Union[int, float]:
    return max(min_val, min(n, max_val))


def rgb_ansi(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def rle_encode_bytes(data: bytes) -> bytes:
    encoded = bytearray()
    for byte_value, group in groupby(data):
        count = len(list(group))
        while count > 0:
            # chunks of 255
            current_count = min(count, 255)
            encoded.append(current_count)
            encoded.append(byte_value)
            count -= current_count
    return bytes(encoded)


def rle_decode_bytes(encoded_data: bytes) -> bytes:
    decoded = bytearray()
    # iterate in count-byte pair
    for i in range(0, len(encoded_data), 2):
        count = encoded_data[i]
        byte_value = encoded_data[i + 1]
        decoded.extend([byte_value] * count)
    return bytes(decoded)
