from pathlib import Path

from learnforge_support.ingestion import load_corpus, parse_markdown


DATA_DIR = Path(__file__).parents[1] / "data"


def test_load_corpus_finds_all_knowledge_entries() -> None:
    chunks = load_corpus(DATA_DIR)

    assert len(chunks) == 40
    assert {chunk.document_type for chunk in chunks} == {"faq", "policy", "ticket"}
    assert {chunk.source for chunk in chunks} == {"faqs.md", "policies.md", "tickets.md"}


def test_parser_preserves_citation_metadata_and_detects_stale_language() -> None:
    chunks = parse_markdown(DATA_DIR / "policies.md")
    subscription_policy = next(chunk for chunk in chunks if chunk.document_id == "POLICY-01")
    refund_policy = next(chunk for chunk in chunks if chunk.document_id == "POLICY-02")

    assert subscription_policy.title == "Subscription Plans and Billing"
    assert subscription_policy.last_updated == "February 2026"
    assert subscription_policy.effective_date == "February 2026"
    assert refund_policy.contains_stale_reference is True
    assert refund_policy.chunk_id.startswith("policy-02_")


def test_assignment_document_is_not_treated_as_knowledge() -> None:
    assert parse_markdown(DATA_DIR / "Assignment.md") == []
