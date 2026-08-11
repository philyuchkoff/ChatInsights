"""
Deepseek conversation export parser.
"""

import json
import os
import re
from datetime import datetime

from .chatgpt import DEFAULT_NAMES


def get_deepseek_messages(conversation, names=None):
    """Get messages from a Deepseek conversation"""
    names = names or DEFAULT_NAMES
    messages = []

    # Deepseek uses same structure as ChatGPT but with 'fragments' instead of 'content'
    # mapping contains nodes with: id, parent, children, message
    # message contains: model, inserted_at, fragments (list of {type, content})
    # Fragment types: REQUEST (user), RESPONSE (assistant), THINK (reasoning)

    mapping = conversation.get('mapping', {})
    if not mapping:
        return messages

    # Collect all message nodes with their data
    message_nodes = []
    for key, node in mapping.items():
        if not isinstance(node, dict) or 'message' not in node:
            continue
        msg_data = node.get('message')
        if not msg_data or not isinstance(msg_data, dict):
            continue

        fragments = msg_data.get('fragments', [])
        inserted_at = msg_data.get('inserted_at', '')

        if fragments:
            message_nodes.append({
                'id': node.get('id', key),
                'parent': node.get('parent'),
                'inserted_at': inserted_at,
                'fragments': fragments
            })

    # Sort by inserted_at timestamp
    message_nodes.sort(key=lambda x: x.get('inserted_at', ''))

    # Process each message node
    for node in message_nodes:
        fragments = node.get('fragments', [])

        for fragment in fragments:
            if not isinstance(fragment, dict):
                continue

            frag_type = fragment.get('type', '')
            content = fragment.get('content', '')

            if not content or not content.strip():
                continue

            # Determine author based on fragment type
            if frag_type == 'REQUEST':
                author = names["user"]
            elif frag_type == 'THINK':
                author = f"{names['assistant']} (Thinking)"
            elif frag_type == 'RESPONSE':
                author = names["assistant"]
            else:
                # Unknown type, skip or treat as user
                author = names["user"]

            messages.append({"author": author, "text": content})

    return messages


def get_deepseek_model(conversation):
    """Extract model from Deepseek conversation"""
    mapping = conversation.get('mapping', {})

    for node_id, node in mapping.items():
        if not isinstance(node, dict):
            continue
        message = node.get('message')
        if not message or not isinstance(message, dict):
            continue

        model = message.get('model')
        if model:
            return model

    return "Deepseek"  # Default fallback


def process_deepseek_conversations(conversations_data, data_dir, names=None, log=None):
    """Process Deepseek conversations with model headers"""
    names = names or DEFAULT_NAMES
    created_directories_info = []
    pruned_data = {}

    # Deepseek uses same top-level format as ChatGPT (list of conversations)
    if isinstance(conversations_data, dict):
        if 'conversations' in conversations_data:
            conversations_data = conversations_data['conversations']
        else:
            conversations_data = [conversations_data]

    processed_count = 0
    for idx, conversation in enumerate(conversations_data):
        processed_count += 1
        if idx == 0 and log:
            log(f"Debug - First conversation keys: {list(conversation.keys())}")

        # Get timestamps - Deepseek uses 'updated_at' and 'inserted_at' at conversation level
        updated_at = conversation.get('updated_at', '') or conversation.get('inserted_at', '')

        if not updated_at:
            continue

        # Parse ISO format timestamp
        try:
            # Handle various timezone formats
            ts = updated_at.replace('Z', '+00:00')
            if '+' in ts[10:]:
                ts = ts[:ts.rfind('+')]
            updated_date = datetime.fromisoformat(ts[:19])
        except Exception as e:
            if idx < 3 and log:
                log(f"Debug - Failed to parse timestamp '{updated_at}': {e}")
            continue

        directory_name = updated_date.strftime('%B_%Y')
        directory_path = os.path.join(data_dir, directory_name)
        os.makedirs(directory_path, exist_ok=True)

        # Get title from conversation or first user message
        title = conversation.get('title', '')
        messages = get_deepseek_messages(conversation, names)

        if not title:
            for msg in messages:
                if msg['author'] == names["user"]:
                    title = msg['text'][:50].replace('\n', ' ')
                    if len(msg['text']) > 50:
                        title += "..."
                    break

        if not title:
            title = 'Untitled'

        # NEW: Extract model from conversation
        model_slug = get_deepseek_model(conversation)

        # keep the Cyrillic alphabet
        sanitized_title = re.sub(r"[^\w\s\-]", "_", title, flags=re.UNICODE)
        sanitized_title = re.sub(r"[\s\-]+", "_", sanitized_title)
        sanitized_title = sanitized_title[:120].strip("_")
        if not sanitized_title:
            sanitized_title = "untitled"

        file_name = os.path.join(directory_path, f"{sanitized_title}_{updated_date.strftime('%d_%m_%Y_%H_%M_%S')}.txt")

        if messages:
            with open(file_name, 'w', encoding="utf-8") as file:
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

            pruned_data[directory_name].append({
                "title": title,
                "create_time": conversation.get('inserted_at', updated_at),
                "update_time": updated_at,
                "model": model_slug,
                "messages": messages
            })

            created_directories_info.append({
                "directory": directory_path,
                "file": file_name
            })
        else:
            if idx < 5 and log:
                log(f"Debug - Conversation '{title}' has no messages")

    if log:
        log(f"Debug - Processed {processed_count} Deepseek conversations, created {len(created_directories_info)} files with messages")

    pruned_json_path = os.path.join(data_dir, "pruned.json")
    with open(pruned_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(pruned_data, json_file, ensure_ascii=False, indent=4)

    return created_directories_info, pruned_data
