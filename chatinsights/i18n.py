"""
Simple internationalization support (English / Russian) for the GUI.
"""

SUPPORTED_LANGUAGES = ("en", "ru")

TRANSLATIONS = {
    "en": {
        # Tabs
        "tab.import": "Import & Process",
        "tab.concepts": "Concept Tracker",
        "tab.training": "Training Data",
        "tab.settings": "Settings",
        # Import tab
        "import.export_file": "AI Chat Export File (ChatGPT, Claude or Deepseek)",
        "import.browse": "Browse",
        "import.platform": "Platform Selection",
        "import.auto": "Auto-detect",
        "import.platform_chatgpt": "ChatGPT",
        "import.platform_claude": "Claude",
        "import.platform_deepseek": "Deepseek",
        "import.options": "Processing Options",
        "import.output_dir": "Output Directory:",
        "import.your_name": "Your Name:",
        "import.assistant_name": "Assistant Name:",
        "import.system_name": "System Name:",
        "import.process": "Process AI Export",
        "import.process_analyze": "Process & Analyze Concepts",
        "import.log": "Process Log",
        "import.results": "Results",
        "import.no_results": "No processing has been done yet",
        "import.open_output": "Open Output Folder",
        # Concepts tab
        "concepts.info_title": "Concept Tracker",
        "concepts.info": (
            "The Concept Tracker analyzes your conversations to identify key topics "
            "and how they evolve over time.\n"
            "It generates an Obsidian-compatible vault with concept notes, maps of content, and dashboards.\n\n"
            "Works with ChatGPT, Claude, and Deepseek conversation exports!\n\n"
            "Once you've processed your AI export, you can run the concept tracker to:\n"
            "1. Identify recurring themes and topics in your conversations\n"
            "2. Track how concepts evolve over time\n"
            "3. Discover relationships between different concepts\n"
            "4. Generate a knowledge graph of your AI interactions"
        ),
        "concepts.core_title": "Core Concepts to Track",
        "concepts.run": "Run Concept Tracker",
        "concepts.stats": "Concept Statistics",
        "concepts.open_vault": "Open Obsidian Vault",
        # Training tab
        "training.title": "Training Data Generation",
        "training.info": (
            "This tool can generate instruction-response pairs from your conversations "
            "for fine-tuning your own LLM models.\n"
            "The training data is exported in JSONL format, with each line containing an "
            "instruction and its corresponding response.\n\n"
            "Supports ChatGPT, Claude, and Deepseek conversation formats!\n\n"
            "You can use this data to:\n"
            "1. Fine-tune existing LLM models to respond more like your assistant\n"
            "2. Create a personalized AI assistant that reflects your interaction style\n"
            "3. Train specialized models for specific domains based on your conversations"
        ),
        "training.options": "Training Data Options",
        "training.min_length": "Minimum instruction length (characters):",
        "training.format": "Export format:",
        "training.jsonl": "JSONL (for fine-tuning)",
        "training.csv": "CSV",
        "training.generate": "Generate Training Data",
        "training.preview": "Training Data Preview",
        "training.generated_count": "Generated {count} training pairs",
        "training.sample": "Sample training pairs:",
        "training.pair": "--- Pair {i} ---",
        "training.instruction": "Instruction: {text}",
        "training.response": "Response: {text}",
        "training.no_pairs": "No training pairs were generated. Check your conversations data.",
        # Settings tab
        "settings.theme": "Theme",
        "settings.theme_light": "Light",
        "settings.theme_dark": "Dark",
        "settings.language": "Language",
        "settings.paths": "Default Paths",
        "settings.output_folder": "Default Output Folder:",
        "settings.browse": "Browse",
        "settings.save": "Save Settings",
        "settings.reset": "Reset to Defaults",
        "settings.about_title": "About ChatInsights",
        "settings.about": (
            "ChatInsights v3.0\n"
            "A tool for analyzing and extracting insights from your AI chat conversations.\n\n"
            "Now supports ChatGPT, Claude, and Deepseek conversation exports!\n\n"
            "This application combines the functionality of:\n"
            "- AI chat export processor (converting JSON to readable text files)\n"
            "- The Concept Tracker (analyzing topics and their evolution)\n"
            "- Training data generator (creating instruction-response pairs for LLM fine-tuning)\n\n"
            "Features:\n"
            "- Auto-detection of ChatGPT vs Claude vs Deepseek exports\n"
            "- Universal conversation processing\n"
            "- Cross-platform concept tracking\n"
            "- Training data generation from multiple AI assistants\n"
            "- Deepseek thinking/response fragment support\n"
            "- Claude thinking block extraction\n"
            "- Claude conversation summary extraction\n"
            "- Automatic model identification in output headers\n\n"
            "v3 Improvements by GitHub Copilot (Claude Opus 4.5)"
        ),
        # Status
        "status.ready": "Ready",
        "status.detected": "Detected: {platform}",
        "status.no_detect": "Unable to auto-detect, please select manually",
        "status.invalid_export": "Invalid export file",
        "status.read_error": "Error reading file",
        "status.processing": "Processing AI export...",
        "status.starting": "Starting to process AI export file...",
        "status.streaming": "Large export detected, using streaming mode...",
        "status.auto_detected": "Auto-detected platform: {platform}",
        "status.processing_stream": "Processing {platform} export (streaming)...",
        "status.processing_count": "Processing {platform} export with {count} conversations...",
        "status.checking_empty": "Checking for empty untitled files...",
        "status.cleanup_done": "Cleanup completed: {count} empty untitled files moved",
        "status.generating_pairs": "Generating training data pairs...",
        "status.generating_titles": "Generating conversation titles file for concept tracker...",
        "status.complete": "Processing complete!",
        "status.processed_count": "Processed {count} conversations",
        "status.dirs_count": "Created files in {count} directories",
        "status.pairs_count": "Generated {count} training data pairs",
        "status.result": (
            "Successfully processed {count} {platform} conversations. "
            "Generated {pairs} training pairs and prepared data for concept tracking."
        ),
        "status.done": "Processing complete",
        "status.failed": "Processing failed",
        "status.tracker_running": "Running concept tracker...",
        "status.tracker_starting": "Starting concept tracking analysis...",
        "status.tracker_done": "Concept tracking complete!",
        "status.tracker_and_copy_done": "Concept tracking and conversation copy complete",
        "status.copy_failed": "Concept tracking complete, but conversation copy failed",
        "status.tracker_failed": "Concept tracking failed",
        "status.training_running": "Generating training data...",
        "status.training_starting": "Starting training data generation...",
        "status.training_done": "Training data generation complete! Created {count} pairs.",
        "status.training_complete": "Training data generation complete",
        "status.training_failed": "Training data generation failed",
        # Tracker stats
        "tracker.processed": "Processed {count} conversations\n",
        "tracker.orphaned": "Orphaned conversations: {count}\n\n",
        "tracker.concept_mentions": "Concept mentions:",
        "tracker.mentions": "mentions",
        "tracker.additional_terms": "Additional terms found:",
        "tracker.occurrences": "occurrences",
        # Dialogs
        "dlg.error": "Error",
        "dlg.warning": "Warning",
        "dlg.theme_title": "Theme Changed",
        "dlg.theme_message": "Theme will be fully applied when you restart the application",
        "dlg.lang_title": "Language Changed",
        "dlg.lang_message": "Language will be fully applied when you restart the application",
        "dlg.settings_saved_title": "Settings Saved",
        "dlg.settings_saved_message": "Your settings have been saved successfully",
        "dlg.reset_title": "Reset Settings",
        "dlg.reset_message": "Are you sure you want to reset all settings to defaults?",
        "dlg.reset_done_title": "Settings Reset",
        "dlg.reset_done_message": "Settings have been reset to defaults",
        # Errors
        "err.no_file": "Please select a valid AI export file",
        "err.empty_export": "The export file is empty.",
        "err.no_platform": "Unable to detect export format. Please select the platform manually.",
        "err.no_conversations": "No conversations found in the export file.",
        "err.processing": "An error occurred while processing: {error}",
        "err.config_save": "Failed to save configuration: {error}",
        "err.no_titles": "Conversation titles file not found. Please process the AI export first.",
        "err.no_concepts": "No valid concepts found. Using default concepts.",
        "err.tracker_error": "An error occurred in concept tracker: {error}",
        "err.copy_failed": "Error copying conversations to Obsidian: {error}",
        "err.no_pruned": "Processed conversation data not found. Please process the AI export first.",
        "err.load_pruned": "Error loading pruned data: {error}",
        "err.training_error": "An error occurred while generating training data: {error}",
        "err.no_output": "Output directory does not exist",
        "err.no_obsidian": "Obsidian directory does not exist",
        # File dialogs
        "file.select_export": "Select AI Export File (ChatGPT or Claude)",
        "file.select_output": "Select Output Directory",
    },
    "ru": {
        # Tabs
        "tab.import": "Импорт и обработка",
        "tab.concepts": "Трекер концепций",
        "tab.training": "Обучающие данные",
        "tab.settings": "Настройки",
        # Import tab
        "import.export_file": "Файл экспорта ИИ-чатов (ChatGPT, Claude или Deepseek)",
        "import.browse": "Обзор",
        "import.platform": "Выбор платформы",
        "import.auto": "Автоопределение",
        "import.platform_chatgpt": "ChatGPT",
        "import.platform_claude": "Claude",
        "import.platform_deepseek": "Deepseek",
        "import.options": "Параметры обработки",
        "import.output_dir": "Каталог вывода:",
        "import.your_name": "Ваше имя:",
        "import.assistant_name": "Имя ассистента:",
        "import.system_name": "Имя системы:",
        "import.process": "Обработать экспорт ИИ",
        "import.process_analyze": "Обработать и проанализировать",
        "import.log": "Журнал обработки",
        "import.results": "Результаты",
        "import.no_results": "Обработка ещё не выполнялась",
        "import.open_output": "Открыть папку вывода",
        # Concepts tab
        "concepts.info_title": "Трекер концепций",
        "concepts.info": (
            "Трекер концепций анализирует ваши разговоры, чтобы выявить ключевые темы "
            "и проследить их развитие во времени.\n"
            "Он создаёт хранилище Obsidian с заметками о концепциях, картами контента и дашбордами.\n\n"
            "Работает с экспортами ChatGPT, Claude и Deepseek!\n\n"
            "После обработки экспорта вы можете запустить трекер концепций, чтобы:\n"
            "1. Выявить повторяющиеся темы в ваших разговорах\n"
            "2. Проследить развитие концепций во времени\n"
            "3. Обнаружить связи между разными концепциями\n"
            "4. Создать граф знаний ваших взаимодействий с ИИ"
        ),
        "concepts.core_title": "Отслеживаемые концепции",
        "concepts.run": "Запустить трекер",
        "concepts.stats": "Статистика концепций",
        "concepts.open_vault": "Открыть хранилище Obsidian",
        # Training tab
        "training.title": "Генерация обучающих данных",
        "training.info": (
            "Этот инструмент создаёт пары «инструкция-ответ» из ваших разговоров "
            "для дообучения собственных LLM-моделей.\n"
            "Обучающие данные экспортируются в формате JSONL: каждая строка содержит "
            "инструкцию и соответствующий ответ.\n\n"
            "Поддерживаются форматы ChatGPT, Claude и Deepseek!\n\n"
            "Вы можете использовать эти данные, чтобы:\n"
            "1. Дообучить существующие LLM-модели отвечать в стиле вашего ассистента\n"
            "2. Создать персонального ИИ-ассистента под ваш стиль общения\n"
            "3. Обучить специализированные модели для конкретных областей"
        ),
        "training.options": "Параметры обучающих данных",
        "training.min_length": "Минимальная длина инструкции (символов):",
        "training.format": "Формат экспорта:",
        "training.jsonl": "JSONL (для дообучения)",
        "training.csv": "CSV",
        "training.generate": "Сгенерировать обучающие данные",
        "training.preview": "Предпросмотр обучающих данных",
        "training.generated_count": "Сгенерировано пар: {count}",
        "training.sample": "Примеры пар:",
        "training.pair": "--- Пара {i} ---",
        "training.instruction": "Инструкция: {text}",
        "training.response": "Ответ: {text}",
        "training.no_pairs": "Пары не созданы. Проверьте данные ваших разговоров.",
        # Settings tab
        "settings.theme": "Тема",
        "settings.theme_light": "Светлая",
        "settings.theme_dark": "Тёмная",
        "settings.language": "Язык",
        "settings.paths": "Каталоги по умолчанию",
        "settings.output_folder": "Каталог вывода по умолчанию:",
        "settings.browse": "Обзор",
        "settings.save": "Сохранить настройки",
        "settings.reset": "Сбросить настройки",
        "settings.about_title": "О программе ChatInsights",
        "settings.about": (
            "ChatInsights v3.0\n"
            "Инструмент для анализа и извлечения инсайтов из ваших разговоров с ИИ.\n\n"
            "Теперь поддерживаются экспорты ChatGPT, Claude и Deepseek!\n\n"
            "Приложение объединяет функции:\n"
            "- Обработчик экспорта ИИ-чатов (конвертация JSON в читаемые текстовые файлы)\n"
            "- Трекер концепций (анализ тем и их развития)\n"
            "- Генератор обучающих данных (пары «инструкция-ответ» для дообучения LLM)\n\n"
            "Возможности:\n"
            "- Автоопределение экспортов ChatGPT, Claude и Deepseek\n"
            "- Универсальная обработка разговоров\n"
            "- Кросс-платформенное отслеживание концепций\n"
            "- Генерация обучающих данных из нескольких ИИ-ассистентов\n"
            "- Поддержка фрагментов Deepseek (thinking/response)\n"
            "- Извлечение блоков размышлений Claude\n"
            "- Извлечение сводок разговоров Claude\n"
            "- Автоматическая идентификация моделей в заголовках вывода\n\n"
            "Улучшения v3 от GitHub Copilot (Claude Opus 4.5)"
        ),
        # Status
        "status.ready": "Готово",
        "status.detected": "Определено: {platform}",
        "status.no_detect": "Не удалось определить платформу, выберите вручную",
        "status.invalid_export": "Некорректный файл экспорта",
        "status.read_error": "Ошибка чтения файла",
        "status.processing": "Обработка экспорта ИИ...",
        "status.starting": "Начало обработки файла экспорта ИИ...",
        "status.streaming": "Обнаружен большой экспорт, используется потоковый режим...",
        "status.auto_detected": "Платформа определена автоматически: {platform}",
        "status.processing_stream": "Обработка экспорта {platform} (потоковый режим)...",
        "status.processing_count": "Обработка экспорта {platform}: {count} разговоров...",
        "status.checking_empty": "Проверка пустых файлов без названия...",
        "status.cleanup_done": "Очистка завершена: перемещено пустых файлов: {count}",
        "status.generating_pairs": "Генерация пар обучающих данных...",
        "status.generating_titles": "Создание файла заголовков разговоров для трекера концепций...",
        "status.complete": "Обработка завершена!",
        "status.processed_count": "Обработано разговоров: {count}",
        "status.dirs_count": "Созданы файлы в {count} каталогах",
        "status.pairs_count": "Создано пар обучающих данных: {count}",
        "status.result": (
            "Успешно обработано {count} разговоров {platform}. Создано {pairs} обучающих пар "
            "и подготовлены данные для трекера концепций."
        ),
        "status.done": "Обработка завершена",
        "status.failed": "Обработка не удалась",
        "status.tracker_running": "Запуск трекера концепций...",
        "status.tracker_starting": "Запуск анализа концепций...",
        "status.tracker_done": "Отслеживание концепций завершено!",
        "status.tracker_and_copy_done": "Трекер концепций и копирование разговоров завершены",
        "status.copy_failed": "Трекер завершён, но копирование разговоров не удалось",
        "status.tracker_failed": "Трекер концепций не выполнен",
        "status.training_running": "Генерация обучающих данных...",
        "status.training_starting": "Начало генерации обучающих данных...",
        "status.training_done": "Генерация обучающих данных завершена! Создано пар: {count}.",
        "status.training_complete": "Генерация обучающих данных завершена",
        "status.training_failed": "Не удалось сгенерировать обучающие данные",
        # Tracker stats
        "tracker.processed": "Обработано разговоров: {count}\n",
        "tracker.orphaned": "Разговоров без концепций: {count}\n\n",
        "tracker.concept_mentions": "Упоминания концепций:",
        "tracker.mentions": "упоминаний",
        "tracker.additional_terms": "Найденные дополнительные термины:",
        "tracker.occurrences": "вхождений",
        # Dialogs
        "dlg.error": "Ошибка",
        "dlg.warning": "Предупреждение",
        "dlg.theme_title": "Тема изменена",
        "dlg.theme_message": "Тема полностью применится после перезапуска приложения",
        "dlg.lang_title": "Язык изменён",
        "dlg.lang_message": "Язык полностью применится после перезапуска приложения",
        "dlg.settings_saved_title": "Настройки сохранены",
        "dlg.settings_saved_message": "Ваши настройки успешно сохранены",
        "dlg.reset_title": "Сброс настроек",
        "dlg.reset_message": "Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?",
        "dlg.reset_done_title": "Настройки сброшены",
        "dlg.reset_done_message": "Настройки сброшены к значениям по умолчанию",
        # Errors
        "err.no_file": "Пожалуйста, выберите корректный файл экспорта ИИ",
        "err.empty_export": "Файл экспорта пуст.",
        "err.no_platform": "Не удалось определить формат экспорта. Выберите платформу вручную.",
        "err.no_conversations": "В файле экспорта не найдено разговоров.",
        "err.processing": "Произошла ошибка при обработке: {error}",
        "err.config_save": "Не удалось сохранить конфигурацию: {error}",
        "err.no_titles": "Файл заголовков разговоров не найден. Сначала обработайте экспорт ИИ.",
        "err.no_concepts": "Не найдено корректных концепций. Будут использованы концепции по умолчанию.",
        "err.tracker_error": "Произошла ошибка в трекере концепций: {error}",
        "err.copy_failed": "Ошибка копирования разговоров в Obsidian: {error}",
        "err.no_pruned": "Обработанные данные разговоров не найдены. Сначала обработайте экспорт ИИ.",
        "err.load_pruned": "Ошибка загрузки обработанных данных: {error}",
        "err.training_error": "Произошла ошибка при генерации обучающих данных: {error}",
        "err.no_output": "Каталог вывода не существует",
        "err.no_obsidian": "Каталог Obsidian не существует",
        # File dialogs
        "file.select_export": "Выберите файл экспорта ИИ (ChatGPT или Claude)",
        "file.select_output": "Выберите каталог вывода",
    },
}


class I18n:
    """Tiny translation helper for the GUI."""

    def __init__(self, lang="en"):
        self.set_lang(lang)

    def set_lang(self, lang):
        self.lang = lang if lang in SUPPORTED_LANGUAGES else "en"

    def tr(self, key, **kwargs):
        text = TRANSLATIONS[self.lang].get(key)
        if text is None:
            text = TRANSLATIONS["en"].get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text

    def supported_languages(self):
        """Return a mapping of language codes to display names."""
        return {
            "en": "English",
            "ru": "Русский",
        }
