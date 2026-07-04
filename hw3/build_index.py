from __future__ import annotations

import argparse

from search import build_local_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local CLIP image index.")
    parser.add_argument("--image-dir", default="data/images", help="Image folder.")
    parser.add_argument("--index-dir", default="index", help="Index output folder.")
    parser.add_argument(
        "--model-name",
        default="openai/clip-vit-base-patch32",
        help="Hugging Face CLIP model name or local model path.",
    )
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--device", default=None, help="cpu, cuda, cuda:0, etc.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count, index_dir = build_local_index(
        image_dir=args.image_dir,
        index_dir=args.index_dir,
        model_name=args.model_name,
        batch_size=args.batch_size,
        device=args.device,
    )
    print(f"Indexed {count} images into {index_dir}.")


if __name__ == "__main__":
    main()
