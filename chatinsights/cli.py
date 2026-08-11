"""
Command-line interface for ChatInsights - headless processing without the GUI.
"""

import argparse
import itertools
import logging
import os
import sys

from .io import ExportLoadError, iter_conversations, load_json_file, use_streaming
from .parsers import detect_platform
from .parsers.chatgpt import process_chatgpt_conversations
from .parsers.claude import process_claude_conversations
from .parsers.deepseek import process_deepseek_conversations
from .tracker import ConceptTracker
from .training import (
    cleanup_empty_untitled_files,
    copy_conversations_to_obsidian,
    create_training_pairs,
    generate_conversation_titles,
)

logger = logging.getLogger("chatinsights.cli")

DEFAULT_OUTPUT = os.path.join(os.path.expanduser("~"), "ChatInsights")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="chat-insights",
        description="Process ChatGPT, Claude and Deepseek exports into readable logs, "
        "training data and an Obsidian vault.",
    )
    parser.add_argument("file", nargs="?", help="Path to conversations.json export file")
    parser.add_argument(
        "--platform",
        choices=["auto", "chatgpt", "claude", "deepseek"],
        default="auto",
        help="Export platform (default: auto-detect)",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output directory (default: ~/ChatInsights)")
    parser.add_argument("--user-name", default="User", help="Name used for user messages (default: User)")
    parser.add_argument(
        "--assistant-name", default="Assistant", help="Name used for assistant messages (default: Assistant)"
    )
    parser.add_argument("--system-name", default="System", help="Name used for system messages (default: System)")
    parser.add_argument("--no-training", action="store_true", help="Skip training data generation")
    parser.add_argument("--no-concepts", action="store_true", help="Skip concept tracking and Obsidian generation")
    parser.add_argument(
        "--min-length", type=int, default=10, help="Minimum instruction length for training pairs (default: 10)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def run(args):
    """Run the full processing pipeline. Returns process exit code."""
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if not args.file:
        logger.error("No export file provided. Use: chat-insights <file.json> [options]")
        return 2
    if not os.path.exists(args.file):
        logger.error("Export file not found: %s", args.file)
        return 2

    names = {
        "user": args.user_name,
        "assistant": args.assistant_name,
        "system": args.system_name,
    }
    data_dir = os.path.join(args.output, "data")
    os.makedirs(data_dir, exist_ok=True)

    # Load the export (streaming for large files)
    if use_streaming(args.file):
        logger.info("Large export detected, using streaming mode...")
        try:
            conversations_iter = iter_conversations(args.file)
            first_conversation = next(conversations_iter)
        except StopIteration:
            logger.error("The export file is empty.")
            return 1
        platform = args.platform
        if platform == "auto":
            platform = detect_platform([first_conversation])
        conversations = itertools.chain([first_conversation], conversations_iter)
    else:
        try:
            conversations = load_json_file(args.file)
        except ExportLoadError as e:
            logger.error("%s", e)
            return 1
        platform = args.platform
        if platform == "auto":
            platform = detect_platform(conversations)

    if platform == "unknown":
        logger.error("Unable to detect export format. Use --platform to select it manually.")
        return 1
    logger.info("Platform: %s", platform)

    # Process conversations based on platform
    if platform == "chatgpt":
        created, pruned = process_chatgpt_conversations(conversations, data_dir, names, log=logger.info)
    elif platform == "deepseek":
        created, pruned = process_deepseek_conversations(conversations, data_dir, names, log=logger.info)
    else:  # claude
        created, pruned = process_claude_conversations(conversations, data_dir, names, log=logger.info)
        cleanup_results = cleanup_empty_untitled_files(data_dir, log=logger.info)
        if cleanup_results["count"] > 0:
            logger.info("Moved %d empty untitled files to cleanup folder", cleanup_results["count"])

    logger.info("Processed %d conversations", len(created))

    # Training data
    if not args.no_training:
        training_pairs = create_training_pairs(
            pruned, os.path.join(data_dir, "training_data.jsonl"), names, log=logger.info
        )
        logger.info("Created %d training data pairs", len(training_pairs))

    # Conversation titles for concept tracker
    titles_file = generate_conversation_titles(data_dir, log=logger.info)

    # Concept tracking + Obsidian
    if not args.no_concepts:
        obsidian_dir = os.path.join(args.output, "Obsidian", "Concepts")
        os.makedirs(obsidian_dir, exist_ok=True)

        tracker = ConceptTracker()
        results = tracker.process(titles_file, obsidian_dir)
        logger.info(
            "Concept tracking: %d conversations, %d orphaned, %d concepts",
            results["conversations"],
            results["orphaned"],
            len(results["concepts"]),
        )

        copy_conversations_to_obsidian(data_dir, obsidian_dir, log=logger.info)
        logger.info("Obsidian vault ready at %s", obsidian_dir)

    logger.info("Done. Output directory: %s", args.output)
    return 0


def main(argv=None):
    """Entry point for the CLI."""
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except KeyboardInterrupt:
        logger.warning("Interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
