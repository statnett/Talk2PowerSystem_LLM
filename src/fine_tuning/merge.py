import argparse
import torch
from unsloth import FastLanguageModel
import os


def merge_and_save(adapter_path, output_path, max_seq_length, save_method):
    print(f"--> Loading model from: {adapter_path}")
    print(f"--> Merge method: {save_method}")

    # 1. Load the model and tokenizer
    # FastLanguageModel.from_pretrained handles loading the base model automatically
    # by reading the adapter_config.json inside the adapter_path.
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=adapter_path,
        max_seq_length=max_seq_length,
        dtype=None,  # None = Auto detection
        load_in_4bit=True,  # Must be True for Unsloth loading, even if merging to 16bit later
    )

    # 2. Force the model into inference mode
    FastLanguageModel.for_inference(model)

    print(f"--> Merging and saving to: {output_path}...")

    # 3. Save the merged model
    # save_pretrained_merged handles the weight merging and tokenizer saving.
    model.save_pretrained_merged(
        output_path,
        tokenizer,
        save_method=save_method,
    )

    print("--> Success! Model merged and saved.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge a LoRA adapter with a base model using Unsloth."
    )

    # Required arguments
    parser.add_argument(
        "--adapter_path",
        type=str,
        help="Path to the LoRA adapter directory (containing adapter_model.bin/safetensors)",
    )
    parser.add_argument(
        "--output_path", type=str, help="Path where the merged model will be saved"
    )

    # Optional arguments
    parser.add_argument(
        "--max_seq_length",
        type=int,
        default=4096,
        help="Maximum sequence length (default: 4096)",
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["merged_16bit", "merged_4bit"],
        default="merged_16bit",
        help="Merge method: 'merged_16bit' (higher quality, larger) or 'merged_4bit' (quantized, smaller). Default is 16bit.",
    )

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)

    merge_and_save(
        args.adapter_path, args.output_path, args.max_seq_length, args.method
    )
