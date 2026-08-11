"""
Parsers for different AI chat export formats (ChatGPT, Claude, Deepseek).
"""

from .detect import detect_platform

__all__ = ["detect_platform"]
