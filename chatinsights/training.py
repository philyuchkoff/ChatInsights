"""
Training data generation and auxiliary file operations.
"""

import csv
import json
import os
import shutil
from datetime import datetime

from .parsers.chatgpt import DEFAULT_NAMES


def create_training_pairs(pruned_data, output_file, names=None, min_length=10, log=None):
    """Convert conversation data to instruction-response pairs for fine-tuning."""
    names = names or DEFAULT_NAMES
    training_pairs = []

    for month, conversations in pruned_data.items():
        for conversation in conversations:
            messages = conversation["messages"]

            # Process message pairs (User -> Assistant)
            for i in range(len(messages) - 1):
                # Find User->Assistant pairs
                if messages[i]["author"] == names["user"] and messages[i + 1]["author"] == names["assistant"]:
                    # Skip very short instructions
                    if len(messages[i]["text"]) < min_length:
                        continue

                    # Create a training pair
                    pair = {"instruction": messages[i]["text"], "response": messages[i + 1]["text"]}
                    training_pairs.append(pair)

    # Write to the appropriate format
    if output_file.endswith(".jsonl"):
        # Write to JSONL format (one JSON object per line)
        with open(output_file, "w", encoding="utf-8") as f:
            for pair in training_pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    elif output_file.endswith(".csv"):
        # Write to CSV format
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["instruction", "response"])
            for pair in training_pairs:
                writer.writerow([pair["instruction"], pair["response"]])

    if log:
        log(f"Created {len(training_pairs)} training pairs in {output_file}")
    return training_pairs


def generate_conversation_titles(data_dir, log=None):
    """Generate the conversation_titles.txt file for concept tracker"""
    titles_file = os.path.join(data_dir, "conversation_titles.txt")

    # Add header for Obsidian
    with open(titles_file, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write("tags:\n")
        f.write("  - help\n")
        f.write("  - management\n")
        f.write("  - memory\n")
        f.write("  - support\n")
        f.write("---\n\n\n")

    # Get list of all text files in data directory and subdirectories
    all_files = []
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith(".txt") and file != "conversation_titles.txt" and file != "training_data.txt":
                all_files.append(os.path.join(root, file))

    # Sort files by date (extracted from filename)
    # Fixed sorting function to handle edge cases
    def get_sort_key(filepath):
        filename = os.path.basename(filepath)
        parts = filename.split("_")

        # Try to extract date components from the end of the filename
        # Expected format: ..._DD_MM_YYYY_HH_MM_SS.txt
        if len(parts) >= 6:
            try:
                # Get the last 6 parts before .txt
                date_parts = parts[-6:]
                # Remove .txt from the last part
                date_parts[-1] = date_parts[-1].replace(".txt", "")

                # Convert to a sortable format: YYYY_MM_DD_HH_MM_SS
                year = date_parts[2]
                month = date_parts[1]
                day = date_parts[0]
                hour = date_parts[3]
                minute = date_parts[4]
                second = date_parts[5]

                return f"{year}_{month}_{day}_{hour}_{minute}_{second}"
            except Exception:
                # If parsing fails, return the filename as is
                return filename
        else:
            # If not enough parts, return the filename as is
            return filename

    all_files.sort(key=get_sort_key)

    # Write file list to conversation_titles.txt
    with open(titles_file, "a", encoding="utf-8") as f:
        for i, file_path in enumerate(all_files, 1):
            # Just write the filename without the full path for readability
            filename = os.path.basename(file_path)
            f.write(f"{i}. {filename}\n")

    return titles_file


def cleanup_empty_untitled_files(data_dir, log=None):
    """
    Find and handle files that are named 'untitled' and have 0KB size
    This function should be called after Claude conversation processing
    """
    empty_untitled_files = []
    cleanup_dir = os.path.join(data_dir, "_empty_untitled_cleanup")

    # Scan through all subdirectories in data_dir
    for root, dirs, files in os.walk(data_dir):
        # Skip the cleanup directory itself
        if "_empty_untitled_cleanup" in root:
            continue

        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)

                # Check if file contains "untitled" (case insensitive) and is 0KB
                if "untitled" in file.lower():
                    file_size = os.path.getsize(file_path)
                    if file_size == 0:
                        empty_untitled_files.append(file_path)

    if empty_untitled_files:
        if log:
            log(f"\nFound {len(empty_untitled_files)} empty untitled files:")

        # Create cleanup directory
        os.makedirs(cleanup_dir, exist_ok=True)

        # Create a log file for the cleanup
        cleanup_log_path = os.path.join(cleanup_dir, f"cleanup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

        with open(cleanup_log_path, "w", encoding="utf-8") as log_file:
            log_file.write("Empty Untitled Files Cleanup Log\n")
            log_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Found {len(empty_untitled_files)} empty untitled files\n\n")

            for file_path in empty_untitled_files:
                # Log the file
                if log:
                    log(f"  - {file_path}")
                log_file.write(f"{file_path}\n")

                # Move the file to cleanup directory
                relative_path = os.path.relpath(file_path, data_dir)
                new_path = os.path.join(cleanup_dir, relative_path)

                # Create subdirectories if needed
                os.makedirs(os.path.dirname(new_path), exist_ok=True)

                # Move the file
                shutil.move(file_path, new_path)

        if log:
            log(f"\nMoved empty untitled files to: {cleanup_dir}")
            log(f"Cleanup log saved to: {cleanup_log_path}")

        # Return statistics
        return {"count": len(empty_untitled_files), "cleanup_dir": cleanup_dir, "log_file": cleanup_log_path}
    else:
        if log:
            log("\nNo empty untitled files found.")
        return {"count": 0, "cleanup_dir": None, "log_file": None}


def copy_conversations_to_obsidian(data_dir, obsidian_dir, log=None):
    """Copy .txt conversation files to Obsidian vault as .md files"""
    if log:
        log("Copying conversation logs to Obsidian vault...")
    source_data_dir = data_dir
    target_obsidian_convos_dir = os.path.join(obsidian_dir, "Conversations")
    os.makedirs(target_obsidian_convos_dir, exist_ok=True)

    copied_count = 0
    skipped_count = 0
    for root, _, files in os.walk(source_data_dir):
        # Skip the cleanup directory
        if "_empty_untitled_cleanup" in root:
            continue
        for file in files:
            if file.endswith(".txt") and file not in ["conversation_titles.txt", "training_data.txt"]:
                # Skip empty untitled files
                src_path = os.path.join(root, file)
                if "untitled" in file.lower() and os.path.getsize(src_path) == 0:
                    continue

                relative_path = os.path.relpath(root, source_data_dir)
                target_subdir = os.path.join(target_obsidian_convos_dir, relative_path)
                os.makedirs(target_subdir, exist_ok=True)

                dest_filename = file[:-4] + ".md"
                dest_path = os.path.join(target_subdir, dest_filename)

                try:
                    shutil.copy2(src_path, dest_path)
                    copied_count += 1
                except Exception as e:
                    if log:
                        log(f"Error copying {file}: {e}")
                    skipped_count += 1

    if log:
        log(f"Copied {copied_count} conversation files to {target_obsidian_convos_dir}.")
        if skipped_count > 0:
            log(f"Skipped {skipped_count} files due to errors.")
