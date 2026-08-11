"""
Platform detection for AI chat exports.
"""


def detect_platform(data):
    """Detect whether the JSON is from ChatGPT, Claude or Deepseek"""
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], dict):
            first_item = data[0]

            # Check for Deepseek first - has mapping with messages that use 'fragments'
            if "mapping" in first_item:
                mapping = first_item.get("mapping", {})
                for key, node in mapping.items():
                    if isinstance(node, dict) and "message" in node:
                        msg = node.get("message")
                        if isinstance(msg, dict) and "fragments" in msg:
                            return "deepseek"
                # If no fragments found, it's ChatGPT format
                return "chatgpt"

            # Check for conversation_id (ChatGPT)
            if "conversation_id" in first_item:
                return "chatgpt"

            # Check for Claude structure - look for uuid and chat_messages
            if "uuid" in first_item:
                if "chat_messages" in first_item or "name" in first_item:
                    return "claude"

    elif isinstance(data, dict):
        if "conversations" in data:
            return detect_platform(data["conversations"])

    # Try to detect by message structure
    try:
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if "chat_messages" in first_item and isinstance(first_item["chat_messages"], list):
                return "claude"
            if "uuid" in first_item and ("created_at" in first_item or "updated_at" in first_item):
                return "claude"
    except Exception:
        pass

    return "unknown"
