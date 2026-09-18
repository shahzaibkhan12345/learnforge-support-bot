from learnforge_support.retrieval import KnowledgeBase, SearchResult
from learnforge_support.models import DocumentChunk


def make_result(document_id: str, score: float, stale: bool) -> SearchResult:
    return SearchResult(
        chunk=DocumentChunk(
            chunk_id=document_id.lower(),
            text="content",
            source="policies.md",
            document_type="policy",
            document_id=document_id,
            title=document_id,
            chunk_index=0,
            last_updated=None,
            effective_date=None,
            contains_stale_reference=stale,
        ),
        relevance_score=score,
    )


def test_current_policy_is_ranked_before_stale_policy_reference() -> None:
    results = KnowledgeBase._prefer_current_policy(
        [make_result("POLICY-02", 0.95, True), make_result("POLICY-01", 0.70, False)]
    )

    assert [result.chunk.document_id for result in results] == ["POLICY-01", "POLICY-02"]
