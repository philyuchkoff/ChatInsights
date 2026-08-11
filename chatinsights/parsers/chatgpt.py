"""
ChatGPT conversation export parser.
"""

import json
import os
import re
from datetime import datetime

DEFAULT_NAMES = {
    "user": "User",
    "assistant": "Assistant",
    "system": "System",
}


def get_chatgpt_messages(conversation, names=None):
    """Get messages from a ChatGPT conversation"""
    names = names or DEFAULT_NAMES
    messages = []
    current_node = conversation.get("current_node")
    mapping = conversation.get("mapping", {})

    while current_node:
        node = mapping.get(current_node, {})
        message = node.get("message") if node else None
        content = message.get("content") if message else None
        author = message.get("author", {}).get("role", "") if message else ""

        if content and content.get("content_type") == "text":
            parts = content.get("parts", [])
            if parts and isinstance(parts[0], str) and parts[0].strip():
                if author != "system" or (message.get("metadata", {}) if message else {}).get("is_user_system_message"):
                    if author == "assistant":
                        author = names["assistant"]
                    elif author == "system":
                        author = names["system"]
                    elif author == "user":
                        author = names["user"]
                    messages.append({"author": author, "text": parts[0]})

        current_node = mapping.get(current_node, {}).get("parent")

    return messages[::-1]


def get_chatgpt_model_slug(conversation):
    """Extract model_slug from ChatGPT conversation metadata"""
    mapping = conversation.get("mapping", {})

    # Look through all messages to find the model_slug
    for node_id, node in mapping.items():
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not message or not isinstance(message, dict):
            continue

        metadata = message.get("metadata", {})
        if metadata and isinstance(metadata, dict):
            model_slug = metadata.get("model_slug")
            if model_slug:
                return model_slug

    return "ChatGPT"  # Default fallback


def process_chatgpt_conversations(conversations_data, data_dir, names=None, log=None):
    """Process ChatGPT conversations with model headers"""
    names = names or DEFAULT_NAMES
    created_directories_info = []
    pruned_data = {}

    for conversation in conversations_data:
        updated = conversation.get("update_time")
        if not updated:
            continue

        updated_date = datetime.fromtimestamp(updated)
        directory_name = updated_date.strftime("%B_%Y")
        directory_path = os.path.join(data_dir, directory_name)

        os.makedirs(directory_path, exist_ok=True)

        title = conversation.get("title", "Untitled")

        # NEW: Extract model_slug from conversation
        model_slug = get_chatgpt_model_slug(conversation)

        # keep the Cyrillic alphabet
        sanitized_title = re.sub(r"[^\w\s\-]", "_", title, flags=re.UNICODE)
        sanitized_title = re.sub(r"[\s\-]+", "_", sanitized_title)
        sanitized_title = sanitized_title[:120].strip("_")
        if not sanitized_title:
            sanitized_title = "untitled"

        file_name = os.path.join(directory_path, f"{sanitized_title}_{updated_date.strftime('%d_%m_%Y_%H_%M_%S')}.txt")

        messages = get_chatgpt_messages(conversation, names)

        with open(file_name, "w", encoding="utf-8") as file:
            # NEW: Write model header at the top
            file.write(f"# Model: {model_slug}\n")
            file.write(f"# Title: {title}\n")
            file.write(f"# Date: {updated_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"\n{'='*60}\n\n")

            for message in messages:
                file.write(f"{message['author']}\n")
                file.write(f"{message['text']}\n\n")

        if directory_name not in pruned_data:
            pruned_data[directory_name] = []

        pruned_data[directory_name].append(
            {
                "title": title,
                "create_time": datetime.fromtimestamp(conversation.get("create_time")).strftime("%Y-%m-%d %H:%M:%S"),
                "update_time": updated_date.strftime("%Y-%m-%d %H:%M:%S"),
                "model": model_slug,
                "messages": messages,
            }
        )

        created_directories_info.append({"directory": directory_path, "file": file_name})

    pruned_json_path = os.path.join(data_dir, "pruned.json")
    with open(pruned_json_path, "w", encoding="utf-8") as json_file:
        json.dump(pruned_data, json_file, ensure_ascii=False, indent=4)

    return created_directories_info, pruned_data
