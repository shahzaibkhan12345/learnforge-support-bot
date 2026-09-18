# Applied AI/LLM Engineer — Take-Home Assignment

> **Candidate:** [Tumhara Naam]
> **Role:** Applied AI/LLM Engineer
> **Company:** Edversity Institute (Private) Limited
> **Deadline:** 11 PM, Sunday, Sep 20, 2026

---

## The Problem

Design an AI-powered customer support assistant for an ed-tech company that answers user questions using the company's internal knowledge base (course FAQs, help-center docs, past support tickets). It should reduce hallucination, handle multi-turn conversations, and escalate to a human when it's not confident.

Sample data is attached to this email — use it to build and test your prototype.

---

## What to Submit

Public Git repo with your working prototype (retrieval + generation loop). Include a README covering:

- **Failure handling** — low-confidence answers, stale data, bad retrieval
- **Eval plan** — how you'd measure answer quality / hallucination rate
- **Trade-offs section** — what you'd change with more time/budget, and why you chose X over Y

Also include:

- **Data schema** — how documents/chunks/metadata are stored (e.g., vector DB record or table structure)
- **System design diagram** — high-level architecture and how a query flows end-to-end through the system

---

## Constraints

- **Deadline:** Submit by 11 PM, Sunday, Sep 20, 2026
- We expect **~4–6 hours** of effective work — please don't overinvest.
- **Data:** Sample data is attached to this email — please use it to build and test your prototype.
- **Models:** Use any free-tier LLM API (e.g., Groq, Gemini, OpenRouter). No cost to you, and rate limits don't matter — we're evaluating design quality, not scale.

---

## How We'll Evaluate

1. Soundness of the architecture and whether it addresses the stated requirements (scale, freshness, hallucination, escalation).
2. Quality of reasoning in the trade-offs section — we care more about *why* than about a "correct" answer.
3. Whether the prototype actually runs and reflects the design.
4. Clarity of communication — could an engineer on our team pick this up and understand the plan?

---

## 📌 Meri Approach (Explanation ke saath)

### 1. Architecture — kya aur kyun?

**RAG (Retrieval-Augmented Generation)** use karunga kyunki:

| Requirement | RAG kaise solve karta hai |
|---|---|
| Hallucination kam karna | LLM ko sirf retrieved context se jawab dena hai, apni knowledge se nahi |
| Freshness (stale data) | Documents update karo → re-index → naya jawab |
| Multi-turn conversation | Conversation history + session memory |
| Escalation | Similarity score threshold + LLM confidence check |

**Kyun RAG aur na Fine-tuning?**
- Fine-tuning mehnga hai, data change hone par dobara train karna padta hai
- RAG mein sirf vector DB update karo, turant fresh jawab
- Ed-tech FAQs roz badalte hain → RAG zyada suitable hai

---

### 2. System Design Diagram

**Kahan banani hai:** [draw.io](https://app.diagrams.net) (free, browser-based)

**Diagram mein ye flow hoga:**
User Query
↓
FastAPI /chat endpoint
↓
Session Memory (multi-turn history)
↓
Query Embedding (sentence-transformers)
↓
Vector DB Search (Chroma — top-k=5)
↓
Confidence Check (similarity score)
↓
┌─────────────┬──────────────────┐
│ LOW │ HIGH │
│ ↓ │ ↓ │
│ Escalate │ LLM Generation │
│ to Human │ (Groq Llama 3) │
└─────────────┴──────────────────┘
↓
Answer + Citations
↓
User Response

**Explanation (interview mein bolne ke liye):**
> "Query pehle embedding mein convert hoti hai, phir vector DB mein top-5 relevant chunks retrieve hote hain. Agar similarity score threshold se kam hai, to system human ko escalate kar deta hai. Warna LLM ko context ke saath prompt bheja jata hai jo cited answer generate karta hai."

---

### 3. Data Schema

**Kyun ye schema?**
- Har chunk ka **source** hona chahiye (citation ke liye)
- **Metadata** se filtering ho sake (e.g., sirf "policies" mein search)
- **Timestamp** se freshness track ho

**Chroma Vector DB Record:**

```json
{
  "id": "faq_001_chunk_2",
  "embedding": [0.12, -0.45, ...],
  "document": "Refund policy ke mutabiq...",
  "metadata": {
    "source": "faqs.json",
    "doc_type": "faq",
    "title": "Refund Policy",
    "chunk_index": 2,
    "total_chunks": 5,
    "last_updated": "2026-09-15",
    "language": "en"
  }
}