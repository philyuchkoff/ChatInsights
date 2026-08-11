"""
Unit tests for the ConceptTracker.
"""

import os

from chatinsights.tracker import ConceptTracker


def make_titles_file(tmp_path, titles):
    path = os.path.join(str(tmp_path), "conversation_titles.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\ntags:\n  - test\n---\n\n\n")
        for i, title in enumerate(titles, 1):
            f.write(f"{i}. {title}_01_01_2025_10_00_00.txt\n")
    return path


def test_process_conversation_file(tmp_path):
    path = make_titles_file(tmp_path, ["Python Coding", "Data Analysis"])
    tracker = ConceptTracker()
    conversations = tracker.process_conversation_file(path)
    assert len(conversations) == 2
    assert conversations[0]["title"] == "Python Coding"
    assert conversations[0]["date"] == "01/01/2025"
    assert conversations[0]["clean_filename"] == "Python Coding_01_01_2025_10_00_00"


def test_extract_concepts(tmp_path):
    path = make_titles_file(tmp_path, ["Python Coding", "Data Analysis", "Something Else"])
    tracker = ConceptTracker()
    conversations = tracker.process_conversation_file(path)
    mentions = tracker.extract_concepts(conversations)
    assert len(mentions["Programming"]) == 1
    assert len(mentions["Data"]) == 1


def test_extract_additional_terms(tmp_path):
    path = make_titles_file(
        tmp_path,
        ["ChatGPT Review", "ChatGPT Tips", "Obsidian Vault", "Obsidian Vault"],
    )
    tracker = ConceptTracker()
    conversations = tracker.process_conversation_file(path)
    terms = tracker.extract_additional_terms(conversations, min_occurrences=2)
    assert "Obsidian" in terms
    assert "ChatGPT" in terms  # not part of any core concept name, so it stays
    assert "Vault" in terms
    assert "Review" not in terms  # appears only once


def test_analyze_concept_evolution(tmp_path):
    path = make_titles_file(
        tmp_path,
        ["Python Coding", "Data Analysis", "Python Scripts"],
    )
    tracker = ConceptTracker()
    conversations = tracker.process_conversation_file(path)
    mentions = tracker.extract_concepts(conversations)
    evolution = tracker.analyze_concept_evolution(mentions, conversations)
    assert evolution["Programming"]["total_mentions"] == 2
    assert evolution["Programming"]["monthly_trend"] == {"2025-01": 2}


def test_find_related_concepts(tmp_path):
    path = make_titles_file(
        tmp_path,
        ["Python Coding", "Python Coding", "Data Analysis", "Python Data"],
    )
    tracker = ConceptTracker()
    conversations = tracker.process_conversation_file(path)
    mentions = tracker.extract_concepts(conversations)
    related = tracker.find_related_concepts(mentions, threshold=0.0)
    assert "Programming" in related


def test_process_generates_notes(tmp_path):
    path = make_titles_file(tmp_path, ["Python Coding", "Data Analysis", "Python Data"])
    tracker = ConceptTracker()
    out_dir = os.path.join(str(tmp_path), "vault")
    results = tracker.process(path, out_dir)

    assert results["conversations"] == 3
    assert os.path.exists(os.path.join(out_dir, "Programming.md"))
    assert os.path.exists(os.path.join(out_dir, "Data.md"))
    assert os.path.exists(os.path.join(out_dir, "Concepts-MOC.md"))
    assert os.path.exists(os.path.join(out_dir, "Concept-Dashboard.md"))
    assert os.path.exists(os.path.join(out_dir, "Recurring-Terms.md"))


def test_process_orphaned_count(tmp_path):
    path = make_titles_file(tmp_path, ["Python Coding", "Unrelated Topic", "Other Stuff"])
    tracker = ConceptTracker()
    results = tracker.process(path, str(tmp_path))
    assert results["orphaned"] == 2
