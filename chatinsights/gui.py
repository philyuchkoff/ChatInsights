"""
ChatInsights v3 - AI Chat Analysis Tool
=======================================
A comprehensive tool for analyzing and extracting insights from AI chat conversations.
Supports ChatGPT, Claude, and Deepseek conversation exports.

Features:
- Auto-detection of platform (ChatGPT/Claude/Deepseek)
- Model identification in output headers
- Claude thinking block extraction
- Claude conversation summary extraction
- Deepseek reasoning chain extraction
- Concept tracking with Obsidian integration
- Training data generation for LLM fine-tuning

v3 Improvements by GitHub Copilot (Claude Opus 4.5):
- Added Claude thinking block extraction (content.type='thinking')
- Added Claude conversation summary extraction
- Added automatic model-slug headers to all output files
- Enhanced message processing for all platforms

Original application structure by Eden_Eldith(P.C O'Brien).
"""

import itertools
import json
import logging
import os
import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

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

logger = logging.getLogger(__name__)

# Global variables
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "ChatInsights")
CONFIG_FILE = os.path.join(OUTPUT_DIR, "config.json")


class ChatInsightsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ChatInsights v3 - AI Chat Analysis Tool (ChatGPT, Claude & Deepseek)")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Default configuration
        self.config = {
            "assistant_name": "Assistant",
            "user_name": "User",
            "system_name": "System",
            "output_dir": OUTPUT_DIR,
            "last_import_file": "",
            "themes": {
                "dark": {"bg": "#2e2e2e", "fg": "#ffffff", "button": "#3d3d3d", "highlight": "#4a86e8"},
                "light": {"bg": "#f0f0f0", "fg": "#333333", "button": "#e0e0e0", "highlight": "#4a86e8"},
            },
            "current_theme": "light",
            "last_platform": "auto",  # auto, chatgpt, claude
        }
        self.load_config()

        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.import_tab = ttk.Frame(self.notebook)
        self.concepts_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.training_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.import_tab, text="Import & Process")
        self.notebook.add(self.concepts_tab, text="Concept Tracker")
        self.notebook.add(self.training_tab, text="Training Data")
        self.notebook.add(self.settings_tab, text="Settings")

        # Create import tab
        self.create_import_tab()

        # Create concepts tab
        self.create_concepts_tab()

        # Create settings tab
        self.create_settings_tab()

        # Create training tab
        self.create_training_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _names(self):
        """Build names dict for parser functions from current config."""
        return {
            "user": self.config["user_name"],
            "assistant": self.config["assistant_name"],
            "system": self.config["system_name"],
        }

    def _load_default_concepts(self):
        """Load default concept tracking list from the bundled resource file."""
        resource = os.path.join(os.path.dirname(__file__), "default_concepts.txt")
        try:
            with open(resource, "r", encoding="utf-8") as f:
                content = f.read()
            return content.strip()
        except OSError as e:
            logger.warning("Unable to load default concepts from %s: %s", resource, e)
            return "AI: \\bAI\\b|Artificial Intelligence|GPT|Claude|LLM"

    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if os.path.exists(CONFIG_FILE):
                try:
                    saved_config = load_json_file(CONFIG_FILE)
                except ExportLoadError as e:
                    logger.warning("Ignoring invalid config file: %s", e)
                    saved_config = {}
                if isinstance(saved_config, dict):
                    # Update config with saved values, keeping defaults for any missing keys
                    for key, value in saved_config.items():
                        self.config[key] = value

            # Ensure output directory exists
            os.makedirs(self.config["output_dir"], exist_ok=True)
        except Exception as e:
            logger.error("Error loading config: %s", e)

    def save_config(self):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            return False

    def create_import_tab(self):
        """Create import and process tab"""
        frame = ttk.Frame(self.import_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # File selection
        file_frame = ttk.LabelFrame(frame, text="AI Chat Export File (ChatGPT, Claude or Deepseek)")
        file_frame.pack(fill=tk.X, pady=10)

        self.file_path_var = tk.StringVar()
        if self.config["last_import_file"] and os.path.exists(self.config["last_import_file"]):
            self.file_path_var.set(self.config["last_import_file"])

        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=70)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        # Platform selection
        platform_frame = ttk.LabelFrame(frame, text="Platform Selection")
        platform_frame.pack(fill=tk.X, pady=10)

        self.platform_var = tk.StringVar(value=self.config.get("last_platform", "auto"))

        ttk.Radiobutton(platform_frame, text="Auto-detect", variable=self.platform_var, value="auto").pack(
            side=tk.LEFT, padx=10, pady=5
        )
        ttk.Radiobutton(platform_frame, text="ChatGPT", variable=self.platform_var, value="chatgpt").pack(
            side=tk.LEFT, padx=10, pady=5
        )
        ttk.Radiobutton(platform_frame, text="Claude", variable=self.platform_var, value="claude").pack(
            side=tk.LEFT, padx=10, pady=5
        )
        ttk.Radiobutton(platform_frame, text="Deepseek", variable=self.platform_var, value="deepseek").pack(
            side=tk.LEFT, padx=10, pady=5
        )

        # Platform info label
        self.platform_info = ttk.Label(platform_frame, text="", foreground="blue")
        self.platform_info.pack(side=tk.RIGHT, padx=10, pady=5)

        # Processing options
        options_frame = ttk.LabelFrame(frame, text="Processing Options")
        options_frame.pack(fill=tk.X, pady=10)

        # Export path
        path_frame = ttk.Frame(options_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(path_frame, text="Output Directory:").pack(side=tk.LEFT, padx=5)

        self.output_dir_var = tk.StringVar(value=self.config["output_dir"])
        output_dir_entry = ttk.Entry(path_frame, textvariable=self.output_dir_var, width=50)
        output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        browse_dir_btn = ttk.Button(path_frame, text="Browse", command=self.browse_output_dir)
        browse_dir_btn.pack(side=tk.RIGHT, padx=5)

        # Custom naming options
        names_frame = ttk.Frame(options_frame)
        names_frame.pack(fill=tk.X, padx=5, pady=5)

        # User name
        ttk.Label(names_frame, text="Your Name:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.user_name_var = tk.StringVar(value=self.config["user_name"])
        ttk.Entry(names_frame, textvariable=self.user_name_var, width=20).grid(row=0, column=1, padx=5, pady=2)

        # Assistant name
        ttk.Label(names_frame, text="Assistant Name:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.assistant_name_var = tk.StringVar(value=self.config["assistant_name"])
        ttk.Entry(names_frame, textvariable=self.assistant_name_var, width=20).grid(row=0, column=3, padx=5, pady=2)

        # System name
        ttk.Label(names_frame, text="System Name:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.system_name_var = tk.StringVar(value=self.config["system_name"])
        ttk.Entry(names_frame, textvariable=self.system_name_var, width=20).grid(row=1, column=1, padx=5, pady=2)

        # Action buttons
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=10)

        self.process_btn = ttk.Button(buttons_frame, text="Process AI Export", command=self.process_export)
        self.process_btn.pack(side=tk.LEFT, padx=5)

        self.analyze_btn = ttk.Button(
            buttons_frame, text="Process & Analyze Concepts", command=self.process_and_analyze
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=5)

        # Log output
        log_frame = ttk.LabelFrame(frame, text="Process Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Results section
        results_frame = ttk.LabelFrame(frame, text="Results")
        results_frame.pack(fill=tk.X, pady=10)

        self.result_text = ttk.Label(results_frame, text="No processing has been done yet", wraplength=600)
        self.result_text.pack(padx=10, pady=10)

        self.open_output_btn = ttk.Button(results_frame, text="Open Output Folder", command=self.open_output)
        self.open_output_btn.pack(pady=5)
        self.open_output_btn.config(state=tk.DISABLED)

    def create_concepts_tab(self):
        """Create concept tracking tab"""
        frame = ttk.Frame(self.concepts_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Info section
        info_frame = ttk.LabelFrame(frame, text="Concept Tracker")
        info_frame.pack(fill=tk.X, pady=10)

        info_text = """
The Concept Tracker analyzes your conversations to identify key topics and how they evolve over time.
It generates an Obsidian-compatible vault with concept notes, maps of content, and dashboards.

Works with ChatGPT, Claude, and Deepseek conversation exports!

Once you've processed your AI export, you can run the concept tracker to:
1. Identify recurring themes and topics in your conversations
2. Track how concepts evolve over time
3. Discover relationships between different concepts
4. Generate a knowledge graph of your AI interactions
        """

        info_label = ttk.Label(info_frame, text=info_text, wraplength=600, justify=tk.LEFT)
        info_label.pack(padx=10, pady=10)

        # Core concepts
        concepts_frame = ttk.LabelFrame(frame, text="Core Concepts to Track")
        concepts_frame.pack(fill=tk.X, pady=10)

        self.concepts_text = scrolledtext.ScrolledText(concepts_frame, height=10)
        self.concepts_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.concepts_text.insert(tk.END, self._load_default_concepts())

        # Run tracker button
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=10)

        self.run_tracker_btn = ttk.Button(buttons_frame, text="Run Concept Tracker", command=self.run_concept_tracker)
        self.run_tracker_btn.pack(side=tk.LEFT, padx=5)

        # Stats frame
        self.stats_frame = ttk.LabelFrame(frame, text="Concept Statistics")
        self.stats_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.stats_text = scrolledtext.ScrolledText(self.stats_frame, height=10)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Open Obsidian folder button
        self.open_obsidian_btn = ttk.Button(frame, text="Open Obsidian Vault", command=self.open_obsidian)
        self.open_obsidian_btn.pack(pady=5)
        self.open_obsidian_btn.config(state=tk.DISABLED)

    def create_training_tab(self):
        """Create training data tab"""
        frame = ttk.Frame(self.training_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Info section
        info_frame = ttk.LabelFrame(frame, text="Training Data Generation")
        info_frame.pack(fill=tk.X, pady=10)

        info_text = """
This tool can generate instruction-response pairs from your conversations for fine-tuning your own LLM models.
The training data is exported in JSONL format, with each line containing an instruction and its corresponding response.

Supports ChatGPT, Claude, and Deepseek conversation formats!

You can use this data to:
1. Fine-tune existing LLM models to respond more like your assistant
2. Create a personalized AI assistant that reflects your interaction style
3. Train specialized models for specific domains based on your conversations
        """

        info_label = ttk.Label(info_frame, text=info_text, wraplength=600, justify=tk.LEFT)
        info_label.pack(padx=10, pady=10)

        # Options
        options_frame = ttk.LabelFrame(frame, text="Training Data Options")
        options_frame.pack(fill=tk.X, pady=10)

        # Minimum conversation length
        min_len_frame = ttk.Frame(options_frame)
        min_len_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(min_len_frame, text="Minimum instruction length (characters):").pack(side=tk.LEFT, padx=5)

        self.min_length_var = tk.IntVar(value=10)
        ttk.Spinbox(min_len_frame, from_=1, to=100, textvariable=self.min_length_var, width=5).pack(
            side=tk.LEFT, padx=5
        )

        # Format selection
        format_frame = ttk.Frame(options_frame)
        format_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(format_frame, text="Export format:").pack(side=tk.LEFT, padx=5)

        self.format_var = tk.StringVar(value="jsonl")
        ttk.Radiobutton(format_frame, text="JSONL (for fine-tuning)", variable=self.format_var, value="jsonl").pack(
            side=tk.LEFT, padx=5
        )
        ttk.Radiobutton(format_frame, text="CSV", variable=self.format_var, value="csv").pack(side=tk.LEFT, padx=5)

        # Action buttons
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=10)

        self.generate_btn = ttk.Button(
            buttons_frame, text="Generate Training Data", command=self.generate_training_data
        )
        self.generate_btn.pack(side=tk.LEFT, padx=5)

        # Preview frame
        preview_frame = ttk.LabelFrame(frame, text="Training Data Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.preview_text = scrolledtext.ScrolledText(preview_frame)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_settings_tab(self):
        """Create settings tab"""
        frame = ttk.Frame(self.settings_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Theme settings
        theme_frame = ttk.LabelFrame(frame, text="Theme")
        theme_frame.pack(fill=tk.X, pady=10)

        self.theme_var = tk.StringVar(value=self.config["current_theme"])
        ttk.Radiobutton(
            theme_frame, text="Light", variable=self.theme_var, value="light", command=self.apply_theme
        ).pack(side=tk.LEFT, padx=20, pady=10)
        ttk.Radiobutton(theme_frame, text="Dark", variable=self.theme_var, value="dark", command=self.apply_theme).pack(
            side=tk.LEFT, padx=20, pady=10
        )

        # Default path settings
        path_frame = ttk.LabelFrame(frame, text="Default Paths")
        path_frame.pack(fill=tk.X, pady=10)

        ttk.Label(path_frame, text="Default Output Folder:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        default_output_var = tk.StringVar(value=self.config["output_dir"])
        ttk.Entry(path_frame, textvariable=default_output_var, width=50).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W
        )

        ttk.Button(path_frame, text="Browse", command=lambda: self.browse_dir(default_output_var)).grid(
            row=0, column=2, padx=5, pady=5
        )

        # Action buttons
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=20)

        ttk.Button(buttons_frame, text="Save Settings", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Reset to Defaults", command=self.reset_settings).pack(side=tk.LEFT, padx=5)

        # About section
        about_frame = ttk.LabelFrame(frame, text="About ChatInsights")
        about_frame.pack(fill=tk.X, pady=10)

        about_text = """
ChatInsights v3.0
A tool for analyzing and extracting insights from your AI chat conversations.

Now supports ChatGPT, Claude, and Deepseek conversation exports!

This application combines the functionality of:
- AI chat export processor (converting JSON to readable text files)
- The Concept Tracker (analyzing topics and their evolution)
- Training data generator (creating instruction-response pairs for LLM fine-tuning)

Features:
- Auto-detection of ChatGPT vs Claude vs Deepseek exports
- Universal conversation processing
- Cross-platform concept tracking
- Training data generation from multiple AI assistants
- Deepseek thinking/response fragment support
- Claude thinking block extraction
- Claude conversation summary extraction
- Automatic model identification in output headers

v3 Improvements by GitHub Copilot (Claude Opus 4.5)
        """

        about_label = ttk.Label(about_frame, text=about_text, wraplength=600, justify=tk.LEFT)
        about_label.pack(padx=10, pady=10)

    def browse_file(self):
        """Open file dialog to select conversations.json"""
        filename = filedialog.askopenfilename(
            title="Select AI Export File (ChatGPT or Claude)",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        )
        if filename:
            self.file_path_var.set(filename)
            self.config["last_import_file"] = filename
            self.save_config()

            # Try to auto-detect platform
            try:
                data = load_json_file(filename)
                platform = detect_platform(data)
                if platform != "unknown":
                    self.platform_var.set(platform)
                    self.platform_info.config(text=f"Detected: {platform.upper()}")
                else:
                    self.platform_info.config(text="Unable to auto-detect, please select manually")
            except ExportLoadError as e:
                self.platform_info.config(text="Invalid export file")
                logger.warning("Cannot detect platform: %s", e)
            except Exception:
                self.platform_info.config(text="Error reading file")

    def browse_output_dir(self):
        """Open directory dialog to select output location"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)
            self.config["output_dir"] = directory
            self.save_config()

    def browse_dir(self, var):
        """Generic directory browser that updates a StringVar"""
        directory = filedialog.askdirectory()
        if directory:
            var.set(directory)

    def log(self, message):
        """Add message to log and scroll to end"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)
        self.root.update_idletasks()

    def process_export(self):
        """Process the AI export file"""
        file_path = self.file_path_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid AI export file")
            return

        # Update config
        self.config["output_dir"] = self.output_dir_var.get()
        self.config["user_name"] = self.user_name_var.get()
        self.config["assistant_name"] = self.assistant_name_var.get()
        self.config["system_name"] = self.system_name_var.get()
        self.config["last_platform"] = self.platform_var.get()
        self.save_config()

        # Run in a separate thread to keep UI responsive
        self.process_btn.config(state=tk.DISABLED)
        self.analyze_btn.config(state=tk.DISABLED)

        processing_thread = threading.Thread(target=self._process_export_thread, args=(file_path,))
        processing_thread.daemon = True
        processing_thread.start()

    def process_and_analyze(self):
        """Process export and then run concept tracker"""
        file_path = self.file_path_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid AI export file")
            return

        # Update config
        self.config["output_dir"] = self.output_dir_var.get()
        self.config["user_name"] = self.user_name_var.get()
        self.config["assistant_name"] = self.assistant_name_var.get()
        self.config["system_name"] = self.system_name_var.get()
        self.config["last_platform"] = self.platform_var.get()
        self.save_config()

        # Run in a separate thread to keep UI responsive
        self.process_btn.config(state=tk.DISABLED)
        self.analyze_btn.config(state=tk.DISABLED)

        processing_thread = threading.Thread(target=self._process_and_analyze_thread, args=(file_path,))
        processing_thread.daemon = True
        processing_thread.start()

    def _process_export_thread(self, file_path):
        """Background thread for processing exports"""
        try:
            self.update_status("Processing AI export...")
            self.log("Starting to process AI export file...")

            output_dir = self.config["output_dir"]
            data_dir = os.path.join(output_dir, "data")
            os.makedirs(data_dir, exist_ok=True)

            # Detect platform
            platform = self.platform_var.get()

            # Load the export (streaming for large files)
            if use_streaming(file_path):
                self.log("Large export detected, using streaming mode...")
                try:
                    conversations_iter = iter_conversations(file_path)
                    first_conversation = next(conversations_iter)
                except StopIteration:
                    self.log("Error: export file is empty.")
                    messagebox.showerror("Error", "The export file is empty.")
                    self.process_btn.config(state=tk.NORMAL)
                    self.analyze_btn.config(state=tk.NORMAL)
                    self.update_status("Processing failed")
                    return
                if platform == "auto":
                    platform = detect_platform([first_conversation])
                    self.log(f"Auto-detected platform: {platform}")
                conversations_data = itertools.chain([first_conversation], conversations_iter)
                conversation_count = None
            else:
                try:
                    conversations_data = load_json_file(file_path)
                except ExportLoadError as e:
                    self.log(f"Error: {e}")
                    messagebox.showerror("Error", str(e))
                    self.process_btn.config(state=tk.NORMAL)
                    self.analyze_btn.config(state=tk.NORMAL)
                    self.update_status("Processing failed")
                    return
                if platform == "auto":
                    platform = detect_platform(conversations_data)
                    self.log(f"Auto-detected platform: {platform}")
                conversation_count = len(conversations_data) if isinstance(conversations_data, list) else None

            if platform == "unknown":
                self.log("Unable to detect platform. Please select manually.")
                messagebox.showerror("Error", "Unable to detect export format. Please select the platform manually.")
                self.process_btn.config(state=tk.NORMAL)
                self.analyze_btn.config(state=tk.NORMAL)
                return

            if conversation_count is not None and conversation_count == 0:
                self.log("Error: no conversations found in the export.")
                messagebox.showerror("Error", "No conversations found in the export file.")
                self.process_btn.config(state=tk.NORMAL)
                self.analyze_btn.config(state=tk.NORMAL)
                self.update_status("Processing failed")
                return

            # Process conversations based on platform
            if conversation_count is None:
                self.log(f"Processing {platform.upper()} export (streaming)...")
            else:
                self.log(f"Processing {platform.upper()} export with {conversation_count} conversations...")

            names = self._names()
            if platform == "chatgpt":
                created_dirs, pruned_data = process_chatgpt_conversations(
                    conversations_data, data_dir, names, log=self.log
                )
            elif platform == "deepseek":
                created_dirs, pruned_data = process_deepseek_conversations(
                    conversations_data, data_dir, names, log=self.log
                )
            else:  # claude
                created_dirs, pruned_data = process_claude_conversations(
                    conversations_data, data_dir, names, log=self.log
                )
                # Cleanup empty untitled files
                self.log("\nChecking for empty untitled files...")
                cleanup_results = cleanup_empty_untitled_files(data_dir, log=self.log)
                if cleanup_results["count"] > 0:
                    self.log(f"Cleanup completed: {cleanup_results['count']} empty untitled files moved")

            # Create training pairs
            self.log("Generating training data pairs...")
            training_pairs = create_training_pairs(
                pruned_data, os.path.join(data_dir, "training_data.jsonl"), names, log=self.log
            )

            # Generate conversation titles file for concept tracker
            self.log("Generating conversation titles file for concept tracker...")
            generate_conversation_titles(data_dir, log=self.log)

            self.log("Processing complete!")
            self.log(f"Processed {len(created_dirs)} conversations")
            self.log(f"Created files in {len(set([info['directory'] for info in created_dirs]))} directories")
            self.log(f"Generated {len(training_pairs)} training data pairs")

            # Update result
            self.result_text.config(
                text=f"Successfully processed {len(created_dirs)} {platform.upper()} conversations. "
                + f"Generated {len(training_pairs)} training pairs and prepared data for concept tracking."
            )

            # Enable buttons
            self.open_output_btn.config(state=tk.NORMAL)
            self.process_btn.config(state=tk.NORMAL)
            self.analyze_btn.config(state=tk.NORMAL)
            self.run_tracker_btn.config(state=tk.NORMAL)
            self.generate_btn.config(state=tk.NORMAL)

            self.update_status("Processing complete")

        except Exception as e:
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred while processing: {str(e)}")
            self.process_btn.config(state=tk.NORMAL)
            self.analyze_btn.config(state=tk.NORMAL)
            self.update_status("Processing failed")

    def _process_and_analyze_thread(self, file_path):
        """Background thread for processing exports and running concept tracker"""
        try:
            # First process the export
            self._process_export_thread(file_path)

            # Then run the concept tracker
            self.notebook.select(1)  # Switch to concept tracker tab
            self.run_concept_tracker()

        except Exception as e:
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.process_btn.config(state=tk.NORMAL)
            self.analyze_btn.config(state=tk.NORMAL)
            self.update_status("Processing failed")

    def parse_concept_regex(self, content):
        """Parse the Concept-regex.md format into concept patterns"""
        concepts = {}
        lines = content.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" in line:
                concept_name, patterns = line.split(":", 1)
                concept_name = concept_name.strip()
                pattern_text = patterns.strip()

                # Clean up the pattern - add word boundaries and handle pipes
                pattern_parts = []
                for part in pattern_text.split("|"):
                    part = part.strip()
                    if part and not part.startswith("\\b") and not part.endswith("\\b"):
                        # Add word boundaries for standalone terms
                        if " " not in part:  # Single word
                            part = f"\\b{part}\\b"
                        else:  # Multi-word phrase
                            part = part.replace(" ", "\\s+")
                    pattern_parts.append(part)

                if pattern_parts:
                    try:
                        final_pattern = "|".join(pattern_parts)
                        concepts[concept_name] = re.compile(final_pattern, re.I)
                    except re.error as e:
                        self.log(f"Invalid regex for {concept_name}: {e}")

        return concepts

    def run_concept_tracker(self):
        """Run the concept tracker on processed data"""
        data_dir = os.path.join(self.config["output_dir"], "data")
        titles_file = os.path.join(data_dir, "conversation_titles.txt")

        if not os.path.exists(titles_file):
            messagebox.showerror("Error", "Conversation titles file not found. Please process the AI export first.")
            return

        # Get custom concepts from UI using the new parser
        concepts_text = self.concepts_text.get("1.0", tk.END).strip()
        custom_concepts = self.parse_concept_regex(concepts_text)

        if not custom_concepts:
            messagebox.showwarning("Warning", "No valid concepts found. Using default concepts.")
            custom_concepts = None

        # Run in a separate thread
        self.run_tracker_btn.config(state=tk.DISABLED)

        tracking_thread = threading.Thread(target=self._concept_tracker_thread, args=(titles_file, custom_concepts))
        tracking_thread.daemon = True
        tracking_thread.start()

    def _concept_tracker_thread(self, titles_file, custom_concepts):
        """Background thread for concept tracking"""
        try:
            self.update_status("Running concept tracker...")
            self.log("Starting concept tracking analysis...")

            obsidian_dir = os.path.join(self.config["output_dir"], "Obsidian", "Concepts")
            os.makedirs(obsidian_dir, exist_ok=True)

            # Create and run tracker
            tracker = ConceptTracker(custom_concepts)
            results = tracker.process(titles_file, obsidian_dir)

            # Display results
            self.stats_text.delete("1.0", tk.END)
            self.stats_text.insert(tk.END, f"Processed {results['conversations']} conversations\n")
            self.stats_text.insert(tk.END, f"Orphaned conversations: {results['orphaned']}\n\n")
            self.stats_text.insert(tk.END, "Concept mentions:\n")

            for concept, count in sorted(results["concepts"].items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    self.stats_text.insert(tk.END, f"- {concept}: {count} mentions\n")

            self.stats_text.insert(tk.END, "\nAdditional terms found:\n")
            for term, count in sorted(results["additional_terms"].items(), key=lambda x: x[1], reverse=True)[:15]:
                self.stats_text.insert(tk.END, f"- {term}: {count} occurrences\n")

            self.log("Concept tracking complete!")
            self.open_obsidian_btn.config(state=tk.NORMAL)
            self.run_tracker_btn.config(state=tk.NORMAL)

            # Copy conversations to Obsidian
            try:
                data_dir_for_copy = os.path.join(self.config["output_dir"], "data")
                copy_conversations_to_obsidian(data_dir_for_copy, obsidian_dir, log=self.log)
                self.update_status("Concept tracking and conversation copy complete")
            except Exception as copy_e:
                self.log(f"Error copying conversations to Obsidian: {copy_e}")
                self.update_status("Concept tracking complete, but conversation copy failed")

        except Exception as e:
            self.log(f"Error in concept tracker: {str(e)}")
            messagebox.showerror("Error", f"An error occurred in concept tracker: {str(e)}")
            self.run_tracker_btn.config(state=tk.NORMAL)
            self.update_status("Concept tracking failed")

    def generate_training_data(self):
        """Generate training data from processed conversations"""
        data_dir = os.path.join(self.config["output_dir"], "data")
        pruned_file = os.path.join(data_dir, "pruned.json")

        if not os.path.exists(pruned_file):
            messagebox.showerror("Error", "Processed conversation data not found. Please process the AI export first.")
            return

        # Run in a separate thread
        self.generate_btn.config(state=tk.DISABLED)

        training_thread = threading.Thread(target=self._training_data_thread, args=(pruned_file,))
        training_thread.daemon = True
        training_thread.start()

    def _training_data_thread(self, pruned_file):
        """Background thread for generating training data"""
        try:
            self.update_status("Generating training data...")
            self.log("Starting training data generation...")

            # Load pruned data
            try:
                pruned_data = load_json_file(pruned_file)
            except ExportLoadError as e:
                self.log(f"Error loading pruned data: {e}")
                messagebox.showerror("Error", str(e))
                self.generate_btn.config(state=tk.NORMAL)
                self.update_status("Training data generation failed")
                return

            # Generate training data with options from UI
            min_length = self.min_length_var.get()
            format_type = self.format_var.get()

            output_file = os.path.join(self.config["output_dir"], f"training_data.{format_type}")
            training_pairs = create_training_pairs(
                pruned_data, output_file, self._names(), min_length=min_length, log=self.log
            )

            # Show preview
            self.preview_text.delete("1.0", tk.END)

            if training_pairs:
                self.preview_text.insert(tk.END, f"Generated {len(training_pairs)} training pairs\n\n")
                self.preview_text.insert(tk.END, "Sample training pairs:\n\n")

                for i, pair in enumerate(training_pairs[:5]):
                    self.preview_text.insert(tk.END, f"--- Pair {i+1} ---\n")
                    self.preview_text.insert(tk.END, f"Instruction: {pair['instruction'][:100]}...\n")
                    self.preview_text.insert(tk.END, f"Response: {pair['response'][:100]}...\n\n")
            else:
                self.preview_text.insert(tk.END, "No training pairs were generated. Check your conversations data.")

            self.log(f"Training data generation complete! Created {len(training_pairs)} pairs.")
            self.generate_btn.config(state=tk.NORMAL)
            self.update_status("Training data generation complete")

        except Exception as e:
            self.log(f"Error generating training data: {str(e)}")
            messagebox.showerror("Error", f"An error occurred while generating training data: {str(e)}")
            self.generate_btn.config(state=tk.NORMAL)
            self.update_status("Training data generation failed")

    def open_output(self):
        """Open the output directory"""
        output_dir = self.config["output_dir"]
        if os.path.exists(output_dir):
            self.open_folder(output_dir)
        else:
            messagebox.showerror("Error", "Output directory does not exist")

    def open_obsidian(self):
        """Open the Obsidian vault directory"""
        obsidian_dir = os.path.join(self.config["output_dir"], "Obsidian", "Concepts")
        if os.path.exists(obsidian_dir):
            self.open_folder(obsidian_dir)
        else:
            messagebox.showerror("Error", "Obsidian directory does not exist")

    def open_folder(self, path):
        """Open a folder in the default file explorer"""
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":  # macOS
            os.system(f'open "{path}"')
        else:  # Linux
            os.system(f'xdg-open "{path}"')

    def apply_theme(self):
        """Apply the selected theme"""
        self.config["current_theme"] = self.theme_var.get()
        self.save_config()
        messagebox.showinfo("Theme Changed", "Theme will be fully applied when you restart the application")

    def save_settings(self):
        """Save current settings to config file"""
        self.config["output_dir"] = self.output_dir_var.get()
        self.config["user_name"] = self.user_name_var.get()
        self.config["assistant_name"] = self.assistant_name_var.get()
        self.config["system_name"] = self.system_name_var.get()
        self.config["current_theme"] = self.theme_var.get()

        if self.save_config():
            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully")

    def reset_settings(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            self.config = {
                "assistant_name": "Assistant",
                "user_name": "User",
                "system_name": "System",
                "output_dir": os.path.join(os.path.expanduser("~"), "ChatInsights"),
                "last_import_file": "",
                "themes": {
                    "dark": {"bg": "#2e2e2e", "fg": "#ffffff", "button": "#3d3d3d", "highlight": "#4a86e8"},
                    "light": {"bg": "#f0f0f0", "fg": "#333333", "button": "#e0e0e0", "highlight": "#4a86e8"},
                },
                "current_theme": "light",
                "last_platform": "auto",
            }

            self.output_dir_var.set(self.config["output_dir"])
            self.user_name_var.set(self.config["user_name"])
            self.assistant_name_var.set(self.config["assistant_name"])
            self.system_name_var.set(self.config["system_name"])
            self.theme_var.set(self.config["current_theme"])

            self.save_config()
            messagebox.showinfo("Settings Reset", "Settings have been reset to defaults")


def main():
    """Launch the ChatInsights GUI application."""
    configure_logging()
    root = tk.Tk()
    ChatInsightsApp(root)
    root.mainloop()


def configure_logging():
    """Set up module-level logging (level can be raised via CHATINSIGHTS_LOG_LEVEL)."""
    level = os.environ.get("CHATINSIGHTS_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
