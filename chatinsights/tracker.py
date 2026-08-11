"""
Concept tracker: analyzes conversation titles and generates Obsidian notes.
"""

import os
import re
from collections import Counter


class ConceptTracker:
    """
    Analyzes conversation titles to track concepts and terminology over time
    and generate Obsidian markdown files for concept tracking.
    """

    def __init__(self, core_concepts=None):
        # Set default core concepts if none provided
        if core_concepts is None:
            self.core_concepts = {
                "AI": re.compile(r"\bAI\b|Artificial Intelligence|GPT|Claude|LLM", re.I),
                "Programming": re.compile(r"Python|JavaScript|Code|Programming", re.I),
                "Data": re.compile(r"Data|Database|CSV|JSON", re.I),
            }
        else:
            self.core_concepts = core_concepts

    def process_conversation_file(self, filename):
        """Process a file containing conversation titles and extract data."""
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        conversations = []
        # Pattern to match your numbered filename format
        pattern = r"^(\d+)\.\s+(.+)_(\d{2})_(\d{2})_(\d{4})_(\d{2})_(\d{2})_(\d{2})\.txt$"

        for line in lines:
            match = re.match(pattern, line.strip())
            if match:
                # Extract components from the filename
                conv = {
                    "id": int(match.group(1)),
                    "title": match.group(2).replace("_", " "),
                    "day": match.group(3),
                    "month": match.group(4),
                    "year": match.group(5),
                    "hour": match.group(6),
                    "minute": match.group(7),
                    "second": match.group(8),
                    "date": f"{match.group(3)}/{match.group(4)}/{match.group(5)}",
                    "time": f"{match.group(6)}:{match.group(7)}:{match.group(8)}",
                    "filename": line.strip()[line.find(" ") + 1 :],
                    "clean_filename": line.strip()[line.find(" ") + 1 :].replace(".txt", ""),
                }
                conversations.append(conv)

        return conversations

    def extract_concepts(self, conversations):
        """Extract key concepts from conversation titles."""
        concept_mentions = {concept: [] for concept in self.core_concepts}

        # Extract concepts based on regex patterns
        for conv in conversations:
            for concept, pattern in self.core_concepts.items():
                if pattern.search(conv["title"]):
                    concept_mentions[concept].append(conv)

        return concept_mentions

    def extract_additional_terms(self, conversations, min_occurrences=3):
        """Extract additional recurring terms that might be concepts."""
        # Extract all words from titles
        all_words = []
        for conv in conversations:
            words = re.findall(r"\b[A-Za-z][A-Za-z0-9]{2,}\b", conv["title"])
            all_words.extend([w for w in words if len(w) > 3])  # Only include words longer than 3 chars

        # Count word frequencies
        word_counts = Counter(all_words)

        # Filter for words that appear multiple times
        recurring_terms = {word: count for word, count in word_counts.items() if count >= min_occurrences}

        # Remove common words and words already in core concepts
        common_words = {"with", "that", "this", "from", "have", "what", "your", "request", "help", "about", "using"}
        for word in list(recurring_terms.keys()):
            if word.lower() in common_words:
                del recurring_terms[word]
            for concept in self.core_concepts:
                if word.lower() in concept.lower():
                    del recurring_terms[word]
                    break

        return recurring_terms

    def analyze_concept_evolution(self, concept_mentions, conversations):
        """Analyze how concepts evolved over time."""
        evolution = {}

        for concept, mentions in concept_mentions.items():
            if not mentions:
                continue

            # Sort mentions by date
            mentions.sort(key=lambda x: f"{x['year']}-{x['month']}-{x['day']}")

            # Group by year-month
            monthly_counts = {}
            for conv in mentions:
                month_key = f"{conv['year']}-{conv['month']}"
                if month_key not in monthly_counts:
                    monthly_counts[month_key] = 0
                monthly_counts[month_key] += 1

            # Calculate first and last mention
            first_mention = mentions[0]
            last_mention = mentions[-1]

            evolution[concept] = {
                "first_mention": first_mention,
                "last_mention": last_mention,
                "monthly_trend": monthly_counts,
                "total_mentions": len(mentions),
            }

        return evolution

    def find_related_concepts(self, concept_mentions, threshold=0.3):
        """Find concepts that frequently appear together."""
        related = {}

        # For each concept pair, calculate co-occurrence
        concepts = list(concept_mentions.keys())
        for i, concept1 in enumerate(concepts):
            if not concept_mentions[concept1]:  # Skip empty concepts
                continue

            related[concept1] = []

            for j, concept2 in enumerate(concepts):
                if i == j or not concept_mentions[concept2]:
                    continue

                # Get sets of conversation IDs for each concept
                conv_ids1 = {conv["id"] for conv in concept_mentions[concept1]}
                conv_ids2 = {conv["id"] for conv in concept_mentions[concept2]}

                # Calculate overlap ratio
                intersection = len(conv_ids1.intersection(conv_ids2))
                if intersection > 0:
                    # Use Jaccard similarity coefficient
                    similarity = intersection / len(conv_ids1.union(conv_ids2))

                    if similarity >= threshold:
                        related[concept1].append(
                            {"concept": concept2, "similarity": similarity, "shared_conversations": intersection}
                        )

        # Sort related concepts by similarity
        for concept in related:
            related[concept].sort(key=lambda x: x["similarity"], reverse=True)

        return related

    def generate_concept_notes(self, concept_mentions, evolution, related_concepts, output_dir):
        """Generate Obsidian notes for each concept."""
        os.makedirs(output_dir, exist_ok=True)

        for concept, mentions in concept_mentions.items():
            if not mentions:
                continue

            # Sort mentions by date
            mentions.sort(key=lambda x: f"{x['year']}-{x['month']}-{x['day']}")

            filename = os.path.join(output_dir, f"{concept.replace(' ', '_')}.md")

            with open(filename, "w", encoding="utf-8") as f:
                # YAML frontmatter
                f.write("---\n")
                f.write(f'concept: "{concept}"\n')
                f.write(f"first_mention: \"{evolution[concept]['first_mention']['date']}\"\n")
                f.write(f"last_mention: \"{evolution[concept]['last_mention']['date']}\"\n")
                f.write(f"mentions: {len(mentions)}\n")

                # Add related concepts to frontmatter
                if related_concepts.get(concept):
                    f.write("related:\n")
                    for related in related_concepts[concept][:5]:  # Top 5 related
                        f.write(f"  - \"{related['concept']}\"\n")

                f.write("tags:\n")
                f.write(f"  - concept/{concept.lower()}\n")
                f.write("  - tracking\n")
                f.write("---\n\n")

                # Content
                f.write(f"# {concept}\n\n")

                f.write("## Overview\n")
                f.write(
                    f"Concept tracked across {len(mentions)} conversations from {evolution[concept]['first_mention']['date']} to {evolution[concept]['last_mention']['date']}.\n\n"
                )

                # Evolution section
                f.write("## Evolution\n")
                f.write("Monthly mentions:\n\n")

                for month, count in evolution[concept]["monthly_trend"].items():
                    f.write(f"- {month}: {count} conversations\n")

                # Related concepts section
                if related_concepts.get(concept):
                    f.write("\n## Related Concepts\n")
                    for related in related_concepts[concept][:5]:
                        f.write(
                            f"- [[{related['concept']}]] - {related['shared_conversations']} shared conversations ({related['similarity']:.2f} similarity)\n"
                        )

                # Chronological mentions
                f.write("\n## Chronological Mentions\n\n")
                for conv in mentions:
                    clean_filename = conv["clean_filename"]
                    f.write(f"- [[{clean_filename}]] - {conv['date']}\n")

    def generate_moc(self, concept_mentions, evolution, output_dir):
        """Generate a Map of Content for all concepts."""
        moc_path = os.path.join(output_dir, "Concepts-MOC.md")

        with open(moc_path, "w", encoding="utf-8") as f:
            f.write("---\ntags:\n  - MOC\n  - concepts\n---\n\n")
            f.write("# Concepts Map of Content\n\n")

            # Calculate date range from all conversations
            all_convs = []
            for mentions in concept_mentions.values():
                all_convs.extend(mentions)

            if all_convs:
                all_convs.sort(key=lambda x: f"{x['year']}-{x['month']}-{x['day']}")
                first_date = all_convs[0]["date"]
                last_date = all_convs[-1]["date"]
                f.write(
                    f"## Overview\nTracking key concepts across conversations from {first_date} to {last_date}.\n\n"
                )
            else:
                f.write("## Overview\nTracking key concepts across conversations.\n\n")

            f.write("## Key Concepts\n\n")

            # Sort concepts by number of mentions
            sorted_concepts = sorted(
                [(concept, mentions) for concept, mentions in concept_mentions.items() if mentions],
                key=lambda x: len(x[1]),
                reverse=True,
            )

            for concept, mentions in sorted_concepts:
                # Only include concepts with mentions
                f.write(f"- [[{concept}]] - {len(mentions)} mentions")
                if concept in evolution and "first_mention" in evolution[concept]:
                    f.write(f" (first: {evolution[concept]['first_mention']['date']})")
                f.write("\n")

            f.write("\n## Concept Categories\n\n")
            f.write("- [[AI Systems]]\n")
            f.write("- [[Programming Projects]]\n")
            f.write("- [[Data Analysis]]\n")
            f.write("- [[Development Topics]]\n")
            f.write("- [[Security & Privacy]]\n")

            f.write("\n## Dataview Queries\n\n")
            f.write("```dataview\nTABLE concept, mentions, first_mention\nFROM #concept\nSORT mentions DESC\n```\n")

    def generate_dashboard(self, concept_mentions, evolution, output_dir):
        """Generate an Obsidian dashboard for concept tracking with embedded queries."""
        dashboard_path = os.path.join(output_dir, "Concept-Dashboard.md")

        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write("---\ntags:\n  - dashboard\n  - concepts\n---\n\n")
            f.write("# Concept Tracking Dashboard\n\n")

            f.write("## Concept Timeline\n\n")
            f.write("```dataview\nCALENDAR file.cday\nFROM #concept\n```\n\n")

            f.write("## Top Concepts\n\n")
            f.write(
                '```dataview\nTABLE concept, mentions AS "Count"\nFROM #concept\nSORT mentions DESC\nLIMIT 10\n```\n\n'
            )

            f.write("## Recent Updates\n\n")
            f.write(
                '```dataview\nTABLE concept, mentions, last_mention AS "Last Updated"\nFROM #concept\nSORT file.mtime DESC\nLIMIT 5\n```\n\n'
            )

            f.write("## Concept Network\n\n")
            f.write(
                "For a visual network of concept relationships, consider using the Obsidian Graph View filtered to show only concept notes.\n\n"
            )

            f.write("## Concept Categories\n\n")
            # Create a table of concept categories and their counts
            categories = {
                "AI Systems": ["AI", "GPT", "Claude", "LLM", "Language Model"],
                "Programming": ["Python", "JavaScript", "Code", "Programming", "API"],
                "Data & Analysis": ["Data", "Database", "CSV", "JSON", "Analysis"],
                "Development": ["Development", "Software", "Application", "Framework"],
                "Cloud & Infrastructure": ["Cloud", "AWS", "Azure", "Deploy"],
                "Security": ["Security", "Privacy", "Encryption", "Authentication"],
            }

            for category, related_terms in categories.items():
                count = 0
                for concept, mentions in concept_mentions.items():
                    if any(term.lower() in concept.lower() for term in related_terms):
                        count += len(mentions)

                f.write(f"- **{category}**: {count} mentions\n")

    def generate_term_analysis(self, terms, output_dir):
        """Generate a note about additional recurring terms found in titles."""
        terms_path = os.path.join(output_dir, "Recurring-Terms.md")

        with open(terms_path, "w", encoding="utf-8") as f:
            f.write("---\ntags:\n  - terminology\n  - analysis\n---\n\n")
            f.write("# Recurring Terms in Conversations\n\n")
            f.write(
                "These terms appear frequently in your conversation titles and may represent additional concepts to track.\n\n"
            )

            f.write("## Term Frequency\n\n")

            # Sort terms by frequency
            sorted_terms = sorted(terms.items(), key=lambda x: x[1], reverse=True)

            for term, count in sorted_terms:
                f.write(f"- **{term}**: {count} occurrences\n")

            f.write("\n## Suggested New Concepts\n\n")
            f.write("Consider adding these high-frequency terms to your concept tracking system:\n\n")

            # Suggest the top terms as potential concepts
            for term, count in sorted_terms[:10]:
                if count >= 5:  # Only suggest terms with 5+ occurrences
                    f.write(f"- [[{term}]] ({count} occurrences)\n")

    def process(self, input_file, output_dir):
        """Process conversations and generate Obsidian notes."""
        conversations = self.process_conversation_file(input_file)
        concept_mentions = self.extract_concepts(conversations)
        evolution = self.analyze_concept_evolution(concept_mentions, conversations)
        related_concepts = self.find_related_concepts(concept_mentions)

        # Generate Obsidian files
        os.makedirs(output_dir, exist_ok=True)
        self.generate_concept_notes(concept_mentions, evolution, related_concepts, output_dir)
        self.generate_moc(concept_mentions, evolution, output_dir)
        self.generate_dashboard(concept_mentions, evolution, output_dir)

        # Additional analysis
        additional_terms = self.extract_additional_terms(conversations)
        self.generate_term_analysis(additional_terms, output_dir)

        # Calculate orphaned conversations (conversations with no concept matches)
        conversations_with_concepts = set()
        for mentions in concept_mentions.values():
            for conv in mentions:
                conversations_with_concepts.add(conv["id"])

        orphaned_count = len(conversations) - len(conversations_with_concepts)

        return {
            "conversations": len(conversations),
            "orphaned": orphaned_count,
            "concepts": {concept: len(mentions) for concept, mentions in concept_mentions.items()},
            "additional_terms": additional_terms,
        }
