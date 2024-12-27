# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License

import argparse
import os
import glob
import time
from pathlib import Path

import onnxruntime_genai as og


def _find_dir_contains_sub_dir(current_dir: Path, target_dir_name: str) -> Path | None:
    """
    Recursively search for a directory containing a specified subdirectory.

    Args:
        current_dir (Path): The directory to start the search from.
        target_dir_name (str): The name of the subdirectory to search for.

    Returns:
        Path | None: The absolute path to the found directory or None if not found.
    """
    curr_path = Path(current_dir).absolute()
    target_dir = glob.glob(target_dir_name, root_dir=curr_path)
    if target_dir:
        return Path(curr_path / target_dir[0]).absolute()
    else:
        if curr_path.parent == curr_path:
            # Root directory reached
            return None
        return _find_dir_contains_sub_dir(curr_path / '..', target_dir_name)


def _complete(text: str, state: int) -> str | None:
    """
    Autocompletion helper for interactive input.

    Args:
        text (str): The current input text.
        state (int): The completion state.

    Returns:
        str | None: The completed text or None if no completions are found.
    """
    return (glob.glob(text + "*") + [None])[state]


def run(args: argparse.Namespace) -> None:
    """
    Main function to load the model, process inputs, and generate responses.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    print("Loading model...")
    if hasattr(og, 'Config'):
        config = og.Config(args.model_path)
        config.clear_providers()
        if args.provider != "cpu":
            print(f"Setting model to {args.provider}...")
            config.append_provider(args.provider)
        model = og.Model(config)
    else:
        model = og.Model(args.model_path)
    print("Model loaded")

    processor = model.create_multimodal_processor()
    tokenizer_stream = processor.create_stream()
    interactive = not args.non_interactive

    while True:
        # Image path handling
        if interactive:
            try:
                # Setup readline for autocompletion
                import readline
                readline.set_completer_delims(" \t\n;")
                readline.parse_and_bind("tab: complete")
                readline.set_completer(_complete)
            except ImportError:
                # readline may not be available on all platforms
                pass
            image_paths = [
                image_path.strip()
                for image_path in input(
                    "Image Path (comma separated; leave empty if no image): "
                ).split(",")
            ]
        else:
            # Non-interactive mode
            if args.image_paths:
                image_paths = args.image_paths
            else:
                image_paths = [
                    str(
                        _find_dir_contains_sub_dir(
                            Path(__file__).parent, "test"
                        ) / "test_models" / "images" / "australia.jpg"
                    )
                ]

        image_paths = [image_path for image_path in image_paths if image_path]
        images = None
        prompt = "<|user|>\n"

        # Load images if provided
        if not image_paths:
            print("No image provided")
        else:
            for i, image_path in enumerate(image_paths):
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Image file not found: {image_path}")
                print(f"Using image: {image_path}")
                prompt += f"<|image_{i + 1}|>\n"

            images = og.Images.open(*image_paths)

        # Prompt handling
        if interactive:
            text = input("Prompt: ")
        else:
            text = args.prompt if args.prompt else "What is shown in this image?"
        prompt += f"{text}<|end|>\n<|assistant|>\n"

        print("Processing images and prompt...")
        inputs = processor(prompt, images=images)

        print("Generating response...")
        params = og.GeneratorParams(model)
        params.set_inputs(inputs)
        params.set_search_options(max_length=7680)

        generator = og.Generator(model, params)
        start_time = time.time()

        # Generate and print response
        while not generator.is_done():
            generator.compute_logits()
            generator.generate_next_token()
            new_token = generator.get_next_tokens()[0]
            print(tokenizer_stream.decode(new_token), end="", flush=True)

        print()
        total_run_time = time.time() - start_time
        print(f"Total Time : {total_run_time:.2f}")

        print("\n" * 3)

        # Cleanup the generator to free resources
        del generator

        if not interactive:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an ONNX multimodal model with specified parameters.")
    parser.add_argument(
        "-m", "--model_path", type=str, required=True, help="Path to the folder containing the model"
    )
    parser.add_argument(
        "-p", "--provider", type=str, required=True, help="Provider to run the model (e.g., CPU, CUDA)"
    )
    parser.add_argument(
        "--image_paths", nargs='*', type=str, help="Path to the images, mainly for CI usage"
    )
    parser.add_argument(
        "-pr", "--prompt", type=str, help="Input prompts to generate tokens from, mainly for CI usage"
    )
    parser.add_argument(
        "--non-interactive", action=argparse.BooleanOptionalAction, help="Run in non-interactive mode, mainly for CI usage"
    )

    args = parser.parse_args()
    run(args)
