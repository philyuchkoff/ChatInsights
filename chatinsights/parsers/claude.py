"""
Claude conversation export parser.
"""

import json
import os
import re
from datetime import datetime

from .chatgpt import DEFAULT_NAMES


def get_claude_messages(conversation, names=None, log=None):
    """Get messages from a Claude conversation, including thinking blocks"""
    names = names or DEFAULT_NAMES
    messages = []

    # Debug: Check what fields are available
    if "chat_messages" in conversation:
        chat_messages = conversation["chat_messages"]

        # If it's a list, process each message
        if isinstance(chat_messages, list):
            for i, msg in enumerate(chat_messages):
                # Debug: log the structure of the first message
                if i == 0 and isinstance(msg, dict):
                    if log:
                        log(f"Debug - First message keys: {list(msg.keys())}")

                # Handle different possible message structures
                sender = None

                # Check if message has direct text/content
                if isinstance(msg, dict):
                    sender = msg.get("sender", "") or msg.get("role", "") or msg.get("author", "")

                    # NEW: Check for 'content' array with typed content blocks (thinking, text, etc.)
                    content_array = msg.get("content", [])
                    if isinstance(content_array, list) and content_array:
                        # Process each content block in the array
                        for content_block in content_array:
                            if isinstance(content_block, dict):
                                block_type = content_block.get("type", "text")

                                # Handle thinking blocks
                                if block_type == "thinking":
                                    thinking_text = content_block.get("thinking", "")
                                    if thinking_text and thinking_text.strip():
                                        # Map sender types to our naming convention with (Thinking) suffix
                                        if sender.lower() in ["assistant", "claude"]:
                                            author = f"{names['assistant']} (Thinking)"
                                        else:
                                            author = f"{sender} (Thinking)"
                                        messages.append({"author": author, "text": str(thinking_text)})

                                # Handle regular text blocks
                                elif block_type == "text":
                                    text_content = content_block.get("text", "")
                                    if text_content and text_content.strip():
                                        # Map sender types to our naming convention
                                        if sender.lower() in ["human", "user"]:
                                            author = names["user"]
                                        elif sender.lower() in ["assistant", "claude"]:
                                            author = names["assistant"]
                                        else:
                                            author = sender
                                        messages.append({"author": author, "text": str(text_content)})

                                # Handle tool_use blocks (log but typically skip content)
                                elif block_type == "tool_use":
                                    tool_name = content_block.get("name", "unknown_tool")
                                    # Optionally log tool usage
                                    if sender.lower() in ["assistant", "claude"]:
                                        author = f"{names['assistant']} (Tool Use)"
                                    else:
                                        author = f"{sender} (Tool Use)"
                                    tool_text = f"[Using tool: {tool_name}]"
                                    messages.append({"author": author, "text": tool_text})

                                # Handle tool_result blocks
                                elif block_type == "tool_result":
                                    # Tool results are typically system-level, skip or minimal log
                                    pass

                        # If we processed content array, continue to next message
                        if content_array:
                            continue

                    # Fallback: Try direct text field
                    content = msg.get("text", "") or msg.get("message", "")

                    # Handle string content field
                    if not content and isinstance(content_array, str):
                        content = content_array

                    if content and sender:
                        # Map sender types to our naming convention
                        if sender.lower() in ["human", "user"]:
                            author = names["user"]
                        elif sender.lower() in ["assistant", "claude"]:
                            author = names["assistant"]
                        else:
                            author = sender

                        messages.append({"author": author, "text": str(content)})

                elif isinstance(msg, str):
                    # Sometimes messages might be strings directly
                    content = msg
                    sender = "unknown"
                    messages.append({"author": sender, "text": str(content)})

        elif isinstance(chat_messages, dict):
            # Sometimes chat_messages might be a dict with indexed keys
            if log:
                log(f"Debug - chat_messages is a dict with keys: {list(chat_messages.keys())}")
            # Try to process as indexed dict
            for key in sorted(chat_messages.keys()):
                msg = chat_messages[key]
                if isinstance(msg, dict):
                    content = msg.get("text", "") or msg.get("content", "") or msg.get("message", "")
                    sender = msg.get("sender", "") or msg.get("role", "") or msg.get("author", "")

                    if content and sender:
                        if sender.lower() in ["human", "user"]:
                            author = names["user"]
                        elif sender.lower() in ["assistant", "claude"]:
                            author = names["assistant"]
                        else:
                            author = sender

                        messages.append({"author": author, "text": str(content)})
    else:
        # Log available fields if chat_messages not found
        if log:
            log(f"Debug - No 'chat_messages' found. Available keys: {list(conversation.keys())}")

        # Try alternative field names
        for field in ["messages", "message_history", "history", "chat"]:
            if field in conversation:
                if log:
                    log(f"Debug - Found '{field}' field, attempting to parse...")
                # Recursively call with modified conversation object
                mod_conv = {"chat_messages": conversation[field]}
                return get_claude_messages(mod_conv, names, log)

    if not messages and "chat_messages" in conversation:
        if log:
            log(f"Debug - chat_messages found but no messages extracted. Type: {type(conversation['chat_messages'])}")

    return messages


def process_claude_conversations(conversations_data, data_dir, names=None, log=None):
    """Process Claude conversations with thinking blocks and summaries"""
    names = names or DEFAULT_NAMES
    created_directories_info = []
    pruned_data = {}

    # Handle if conversations_data is wrapped or is directly a list
    if isinstance(conversations_data, dict) and "conversations" in conversations_data:
        conversations_data = conversations_data["conversations"]

    processed_count = 0
    for idx, conversation in enumerate(conversations_data):
        processed_count += 1
        # Debug first conversation structure
        if idx == 0 and log:
            log(f"Debug - First conversation keys: {list(conversation.keys())}")

        # Claude uses ISO timestamp format
        created_at = conversation.get("created_at", "")
        updated_at = conversation.get("updated_at", created_at)

        if not updated_at:
            continue

        # Parse ISO format timestamp
        try:
            updated_date = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except Exception:
            # Fallback for other timestamp formats
            continue

        directory_name = updated_date.strftime("%B_%Y")
        directory_path = os.path.join(data_dir, directory_name)

        os.makedirs(directory_path, exist_ok=True)

        # Get title from conversation - Claude uses 'name' field
        title = conversation.get("name", "")
        if not title or title == "":
            # Try to extract title from first message
            messages = get_claude_messages(conversation, names, log)
            if messages and len(messages) > 0:
                title = messages[0]["text"][:50] + "..." if len(messages[0]["text"]) > 50 else messages[0]["text"]
            else:
                title = "Untitled"

        # NEW: Extract conversation summary if available
        conversation_summary = conversation.get("summary", "")

        # NEW: Try to detect model from messages or metadata
        model_slug = "Claude"  # Default
        # Claude doesn't typically include model slug in the same way as ChatGPT
        # But we can check for model indicators in the data
        if "model" in conversation:
            model_slug = conversation.get("model", "Claude")

        # keep the Cyrillic alphabet
        sanitized_title = re.sub(r"[^\w\s\-]", "_", title, flags=re.UNICODE)
        sanitized_title = re.sub(r"[\s\-]+", "_", sanitized_title)
        sanitized_title = sanitized_title[:120].strip("_")
        if not sanitized_title:
            sanitized_title = "untitled"

        file_name = os.path.join(directory_path, f"{sanitized_title}_{updated_date.strftime('%d_%m_%Y_%H_%M_%S')}.txt")

        messages = get_claude_messages(conversation, names, log)

        # Only write file if there are messages
        if messages:
            with open(file_name, "w", encoding="utf-8") as file:
                # NEW: Write model header at the top
                file.write(f"# Model: {model_slug}\n")
                file.write(f"# Title: {title}\n")
                file.write(f"# Date: {updated_date.strftime('%Y-%m-%d %H:%M:%S')}\n")

                # NEW: Write conversation summary if available
                if conversation_summary and conversation_summary.strip():
                    file.write("\n## Conversation Summary\n")
                    file.write(f"{conversation_summary}\n")

                file.write(f"\n{'='*60}\n\n")

                for message in messages:
                    file.write(f"{message['author']}\n")
                    file.write(f"{message['text']}\n\n")

            if directory_name not in pruned_data:
                pruned_data[directory_name] = []

            pruned_data[directory_name].append(
                {
                    "title": title,
                    "create_time": created_at,
                    "update_time": updated_at,
                    "model": model_slug,
                    "summary": conversation_summary,
                    "messages": messages,
                }
            )

            created_directories_info.append({"directory": directory_path, "file": file_name})
        else:
            if idx < 5 and log:
                log(f"Debug - Conversation '{title}' has no messages")

    if log:
        log(
            f"Debug - Processed {processed_count} Claude conversations, created {len(created_directories_info)} files with messages"
        )

    pruned_json_path = os.path.join(data_dir, "pruned.json")
    with open(pruned_json_path, "w", encoding="utf-8") as json_file:
        json.dump(pruned_data, json_file, ensure_ascii=False, indent=4)

    return created_directories_info, pruned_data
