"""Download a reranker model to a local directory."""

from argparse import ArgumentParser
from pathlib import Path

from huggingface_hub import snapshot_download

DEFAULT_MODEL_ID = "mixedbread-ai/mxbai-rerank-base-v1"


def main() -> None:
    parser = ArgumentParser(
        description="Download a reranker model to a local directory."
    )
    parser.add_argument(
        "--model-id",
        default=DEFAULT_MODEL_ID,
        help="Hugging Face model id to download.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where the model should be stored.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=args.model_id,
        local_dir=str(output_dir),
    )
    print(f"Downloaded reranker model {args.model_id} to {output_dir}")


if __name__ == "__main__":
    main()
