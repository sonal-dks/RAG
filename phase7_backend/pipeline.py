"""
Phase 7 — RAG pipeline: Phase 2 → 3 → 4 → 5 → 6.

Stateless: one user message in, one response + citations out.

Multi-fund strategy: when multiple funds are selected, each fund gets its own
Phase 3→4→5 cycle (dedicated retrieval + dedicated LLM call) so the answer for
each fund is complete and accurate. The per-fund answers are then combined and
run through Phase 6 once.  With Groq latency at ~0.3s per call this stays fast.
"""

from phase2_input_guardrails import process_query as guardrail_process
from phase3_query_processing import process_query as query_process
from phase4_retrieval_engine import process_query as retrieval_process
from phase5_response_generation import process_query as generation_process
from phase6_output_guardrails import process_query as output_guardrail_process

from .config import DEFAULT_CITATION_URL


def run_rag(user_message: str, *, active_funds: list[str] | None = None) -> dict:
    if not user_message or not isinstance(user_message, str):
        return _empty_response()
    text = user_message.strip()
    if not text:
        return _empty_response()

    funds = [f.strip() for f in (active_funds or []) if f and f.strip()]

    # Phase 2 — Input Guardrail (runs once)
    g2 = guardrail_process(text)
    if not g2.get("pass_through", False):
        return {
            "answer": g2.get("canned_response", "I can only answer factual questions about the listed Quant Mutual Funds."),
            "citations": [],
            "citation_url": DEFAULT_CITATION_URL,
        }

    if len(funds) > 1:
        return _run_multi_fund(text, funds)
    elif len(funds) == 1:
        return _run_single_fund(text, funds[0])
    else:
        return _run_no_fund(text)


def _run_single_fund(text: str, fund_name: str) -> dict:
    """Standard path: one fund selected → Phase 3→4→5→6."""
    ctx, source_url = _retrieve_for_fund(fund_name, text)

    q5 = generation_process(
        f"{fund_name}: {text}",
        ctx,
        sufficient=bool(ctx),
    )
    q6 = output_guardrail_process(q5["raw_response"], source_url=source_url)

    citation = q6.get("citation_url") or source_url
    return {
        "answer": q6["validated_response"],
        "citations": [citation] if citation else [],
        "citation_url": citation,
    }


def _run_multi_fund(text: str, funds: list[str]) -> dict:
    """One LLM call per fund → combine per-fund answers → Phase 6."""
    per_fund_answers: list[str] = []
    all_citations: list[str] = []

    for fund_name in funds:
        ctx, source_url = _retrieve_for_fund(fund_name, text)
        if source_url:
            all_citations.append(source_url)

        q5 = generation_process(
            f"{fund_name}: {text}",
            ctx,
            sufficient=bool(ctx),
        )
        raw = (q5.get("raw_response") or "").strip()
        if raw:
            per_fund_answers.append(f"**{fund_name}:** {raw}")

    if not per_fund_answers:
        return {
            "answer": "I don't have enough information to answer that for the selected funds.",
            "citations": [],
            "citation_url": None,
        }

    combined = "\n\n".join(per_fund_answers)

    primary_url = all_citations[0] if all_citations else DEFAULT_CITATION_URL
    q6 = output_guardrail_process(combined, source_url=primary_url)

    deduped = list(dict.fromkeys(all_citations))
    return {
        "answer": q6["validated_response"],
        "citations": deduped,
        "citation_url": deduped[0] if deduped else None,
    }


def _run_no_fund(text: str) -> dict:
    """No fund context — Phase 3 tries to resolve from the query text."""
    q3 = query_process(text)
    if not q3.get("fund_resolved", False):
        return {
            "answer": q3.get("clarification_message", "Please specify which Quant fund you're asking about."),
            "citations": [],
            "citation_url": None,
        }

    q4 = retrieval_process(
        q3["enriched_query"],
        q3["canonical_name"],
        section_filter=q3.get("section_filter"),
    )
    source_url = (
        q3.get("url")
        or (q4["chunks"][0]["source_url"] if q4.get("chunks") else None)
        or DEFAULT_CITATION_URL
    )

    q5 = generation_process(text, q4["retrieved_context"], sufficient=q4.get("sufficient", False))
    q6 = output_guardrail_process(q5["raw_response"], source_url=source_url)

    citation = q6.get("citation_url") or source_url
    return {
        "answer": q6["validated_response"],
        "citations": [citation] if citation else [],
        "citation_url": citation,
    }


def _retrieve_for_fund(fund_name: str, query_text: str) -> tuple[str, str]:
    """Phase 3 + 4 for one fund. Returns (context_str, source_url)."""
    enriched = f"{fund_name}: {query_text}"
    q3 = query_process(enriched)
    if not q3.get("fund_resolved", False):
        return "", DEFAULT_CITATION_URL

    q4 = retrieval_process(
        q3["enriched_query"],
        q3["canonical_name"],
        section_filter=q3.get("section_filter"),
    )
    source_url = (
        q3.get("url")
        or (q4["chunks"][0]["source_url"] if q4.get("chunks") else None)
        or DEFAULT_CITATION_URL
    )
    return q4.get("retrieved_context", ""), source_url


def _empty_response() -> dict:
    return {
        "answer": "I can only answer factual questions about the listed Quant Mutual Funds.",
        "citations": [],
        "citation_url": None,
    }
