import argparse
from avs_encoder import AVSEncoder
from avs_decoder import AVSDecoder


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Encoder/decoder utility for AVS (ASCII Video Stream) files"
    )
    parser.add_argument(
        "ACTION", help="enc/dec - the action for the utility to perform"
    )
    parser.add_argument("FILE", help="the file to encode or decode")
    parser.add_argument("-w", "--width", help="width of output frames")
    parser.add_argument("-b", "--brightness", help="exposure scale of output frames")
    parser.add_argument("-r", "--framerate", help="framerate of output FILE")
    parser.add_argument(
        "-o", "--output", help="file to output frame data to (include extension)"
    )

    args = parser.parse_args()
    if args.ACTION == "enc":
        encoder = AVSEncoder(
            width=int(args.width),
            frame_rate=int(args.framerate),
            version=3,
            brightness=int(args.brightness),
        )
        encoder.encode(args.FILE, outfile=args.output)
    elif args.ACTION == "dec":
        decoder = AVSDecoder()
        decoder.play_rgb_avs(args.FILE)


if __name__ == "__main__":
    main()
