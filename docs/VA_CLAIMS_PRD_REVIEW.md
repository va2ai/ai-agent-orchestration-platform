# VA Claims AI Accelerator - PRD Review

## Executive Summary

This document reviews the "VA Claims AI Accelerator" PRD to identify gaps and required work. The current document is **a strategic vision and portfolio positioning guide** rather than a complete PRD. It excels at communicating value proposition but lacks the technical depth needed for implementation.

**Overall Assessment:** The document provides excellent strategic direction but requires significant elaboration to become implementation-ready.

---

## What the Document Does Well

| Strength | Evidence |
|----------|----------|
| Clear value proposition | "Compliance-safe, human-in-the-loop AI system" |
| Portfolio positioning | Explicit differentiation from "chatbot-style tools" |
| Demo narrative | 5-step flow is clear and compelling |
| Safety-first mindset | "System refuses to generate unsupported claims" |
| Evidence grounding contract | JSON schema for traceability |
| Failure mode awareness | OCR misreads, sparse evidence, model drift |

---

## Critical Missing Sections

### 1. Technical Specifications

**Status:** Not present

**Required:**

```
- Technology stack (LLM provider, embedding model, vector DB, OCR engine)
- Database schema for evidence store
- API specifications (REST/GraphQL endpoints)
- Data models (Pydantic/TypeScript schemas)
- Infrastructure requirements (cloud provider, compute needs)
- Authentication/authorization mechanism
```

**Questions to Answer:**
- Which LLM? (GPT-4, Claude, open-source?)
- Which OCR engine? (Tesseract, AWS Textract, Azure Document Intelligence?)
- Which vector database? (Pinecone, Weaviate, Chroma, pgvector?)
- Deployment target? (AWS, GCP, Azure, on-prem?)

---

### 2. Functional Requirements

**Status:** High-level only (5-step demo flow)

**Required:**

| Feature | Missing Details |
|---------|-----------------|
| Document Upload | File size limits, supported formats (PDF, DOCX, images?), batch upload? |
| OCR Pipeline | Multi-column handling, handwriting support, table extraction |
| PII Redaction | What constitutes PII? SSN, DOB, addresses? Configurable rules? |
| Evidence Search | Full-text vs semantic? Hybrid? Filters (date, type, source)? |
| Claim Intelligence | Rule-based vs ML? How are "presumptive conditions" detected? |
| Strength Scoring | Scale (1-5? Low/Med/High?)? Weighted factors? Calibration data? |
| Draft Generation | Template-based vs freeform? Max length? Formatting requirements? |
| Human Review | Approval workflow? Multi-reviewer? Role-based permissions? |
| Export | Formats (PDF, Word, plain text?)? Watermarking? |
| Audit Log | What events are logged? Retention period? Tamper-proof? |

---

### 3. User Stories & Acceptance Criteria

**Status:** Not present

**Required Examples:**

```gherkin
Feature: Evidence Upload
  As a VA disability consultant
  I want to upload a veteran's C-file
  So that I can analyze their medical records

  Scenario: Successful PDF upload
    Given I am logged in as an accredited consultant
    When I upload a 50-page PDF C-file
    Then the system should extract text via OCR
    And redact detected PII
    And create searchable evidence corpus
    And display page count and extraction confidence

  Scenario: Unsupported file type
    Given I am logged in
    When I upload a .exe file
    Then the system should reject the upload
    And display "Unsupported file type" error
```

---

### 4. Non-Functional Requirements

**Status:** Not present

**Required:**

| Category | Requirement |
|----------|-------------|
| Performance | OCR processing time per page (target: <2s) |
| Performance | Search latency (target: <500ms) |
| Performance | Draft generation time (target: <30s) |
| Scalability | Concurrent users (target: 50? 500? 5000?) |
| Availability | Uptime SLA (99.9%?) |
| Storage | Document retention period |
| Security | Encryption at rest and in transit |
| Security | Access control model (RBAC? ABAC?) |
| Compliance | HIPAA? VA-specific regulations? |

---

### 5. Compliance & Regulatory Framework

**Status:** Mentioned but not specified

**Required:**

- [ ] Identify applicable regulations (HIPAA, 38 CFR, VA privacy rules)
- [ ] Define data handling procedures for PHI/PII
- [ ] Specify audit requirements and log retention
- [ ] Document consent/authorization requirements
- [ ] Define breach notification procedures
- [ ] Specify data residency requirements (US-only?)
- [ ] Document BAA requirements if using cloud LLMs

**Critical Questions:**
- Does processing medical records require HIPAA compliance?
- What VA-specific regulations apply to accredited agents?
- Can data be sent to external LLM APIs (OpenAI, Anthropic)?
- What happens if the system provides incorrect advice?

---

### 6. Data Architecture

**Status:** Conceptual only

**Required:**

```
Evidence Store Schema:
├── documents
│   ├── id (UUID)
│   ├── session_id
│   ├── filename
│   ├── upload_timestamp
│   ├── file_hash (SHA-256)
│   ├── page_count
│   ├── ocr_confidence
│   └── status (processing, ready, error)
│
├── pages
│   ├── id (UUID)
│   ├── document_id (FK)
│   ├── page_number
│   ├── raw_text
│   ├── redacted_text
│   ├── ocr_confidence
│   └── embedding_vector
│
├── evidence_chunks
│   ├── id (UUID)
│   ├── page_id (FK)
│   ├── chunk_text
│   ├── chunk_type (medical, legal, admin)
│   ├── detected_entities
│   └── embedding_vector
│
├── claims
│   ├── id (UUID)
│   ├── session_id
│   ├── condition_name
│   ├── claim_type (primary, secondary, presumptive)
│   ├── strength_score
│   ├── strength_rationale
│   └── evidence_ids (array)
│
├── drafts
│   ├── id (UUID)
│   ├── claim_id (FK)
│   ├── draft_type (lay_statement, nexus, appeal)
│   ├── content
│   ├── version
│   ├── evidence_citations
│   └── status (draft, reviewed, approved)
│
└── audit_log
    ├── id (UUID)
    ├── timestamp
    ├── user_id
    ├── action_type
    ├── entity_type
    ├── entity_id
    ├── before_state
    ├── after_state
    └── ip_address
```

---

### 7. Error Handling & Edge Cases

**Status:** Partial (mentions failure modes but no handling details)

**Required:**

| Scenario | Expected Behavior |
|----------|-------------------|
| OCR confidence < 70% | Flag page for manual review, don't include in auto-analysis |
| No extractable text | Display error, suggest re-scanning at higher quality |
| PII redaction failure | Block processing, alert user, log for review |
| Insufficient evidence for claim | Refuse to generate draft, explain what's missing |
| Conflicting evidence | Present both sides, flag for human review |
| Model API timeout | Retry 3x with exponential backoff, then graceful degradation |
| Rate limiting | Queue requests, display estimated wait time |
| Session expiration | Auto-save state, allow resume |

---

### 8. Testing Strategy

**Status:** Not present

**Required:**

```yaml
Testing Levels:
  Unit Tests:
    - OCR text extraction accuracy
    - PII detection coverage
    - Chunk boundary detection
    - Evidence matching logic

  Integration Tests:
    - Upload → OCR → Storage pipeline
    - Search → Retrieval → Citation flow
    - Draft generation → Evidence linking

  Evaluation Tests:
    - Claim intelligence accuracy (precision/recall)
    - Strength scoring calibration
    - Draft quality (human evaluation rubric)
    - Hallucination detection rate

  Adversarial Tests:
    - Malformed documents
    - Injection attempts in uploaded text
    - Prompt injection via document content
    - Edge case claim types

  Compliance Tests:
    - PII detection coverage
    - Audit log completeness
    - Access control enforcement
```

---

### 9. Monitoring & Observability

**Status:** Not present

**Required:**

- [ ] Application metrics (request latency, error rates)
- [ ] LLM-specific metrics (token usage, response quality)
- [ ] Business metrics (claims processed, approval rates)
- [ ] Alerting thresholds and escalation paths
- [ ] Dashboard requirements
- [ ] Log aggregation strategy

---

### 10. Success Metrics & KPIs

**Status:** Not present

**Required:**

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Time savings per claim | >50% reduction | Before/after comparison |
| Evidence retrieval precision | >90% | Human evaluation sample |
| Draft acceptance rate | >80% first draft | User approval tracking |
| Hallucination rate | <1% | Automated + human audit |
| User satisfaction | >4.5/5 | In-app feedback |
| System uptime | 99.9% | Monitoring |

---

## Implementation Gaps vs PRD Phases

The PRD mentions 3 phases but lacks detail:

### Phase 1: Ingestion & Evidence Store (2-3 weeks)

**Specified:**
- Ingestion
- Evidence store
- Search + citations

**Missing:**
- [ ] OCR engine selection and configuration
- [ ] PII detection rules and patterns
- [ ] Chunking strategy (size, overlap, boundaries)
- [ ] Embedding model selection
- [ ] Vector store configuration
- [ ] Search ranking algorithm
- [ ] Citation format specification

### Phase 2: Claim Intelligence (2-3 weeks)

**Specified:**
- Claim intelligence heuristics
- Strength scoring with rationale

**Missing:**
- [ ] Condition taxonomy/ontology
- [ ] Primary vs secondary classification rules
- [ ] Presumptive condition database (Agent Orange, Gulf War, etc.)
- [ ] Strength scoring rubric (factors and weights)
- [ ] Missing evidence detection rules
- [ ] Nexus relationship modeling

### Phase 3: Draft Generation (2 weeks)

**Specified:**
- Draft generation with grounding
- Versioning + diff

**Missing:**
- [ ] Draft templates (lay statement, nexus letter, appeal)
- [ ] Grounding enforcement mechanism
- [ ] Confidence threshold for generation
- [ ] Version control implementation
- [ ] Diff visualization approach
- [ ] Export format specifications

---

## Recommended Next Steps

### Immediate (Week 1)

1. **Define technology stack**
   - Select LLM provider (recommendation: start with GPT-4o for quality, add Gemini for cost optimization)
   - Select OCR engine (recommendation: Azure Document Intelligence for medical records)
   - Select vector store (recommendation: pgvector for simplicity, Pinecone for scale)

2. **Create data models**
   - Define Pydantic schemas for all entities
   - Design database schema
   - Define API contracts

3. **Clarify compliance requirements**
   - Consult with VA accreditation requirements
   - Determine if HIPAA applies
   - Define data handling procedures

### Short-term (Weeks 2-3)

4. **Write detailed user stories**
   - Cover all 5 demo flow steps
   - Include edge cases and error scenarios
   - Define acceptance criteria

5. **Design evaluation framework**
   - Define ground truth dataset for testing
   - Create hallucination detection tests
   - Design human evaluation rubrics

### Medium-term (Weeks 4-6)

6. **Implement Phase 1** (per PRD timeline)
   - Build ingestion pipeline
   - Create evidence store
   - Implement search with citations

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM hallucinations in legal context | High | Critical | Evidence grounding, confidence thresholds, human review |
| HIPAA violation from cloud LLM use | Medium | Critical | On-prem deployment or BAA with provider |
| OCR errors in medical records | High | High | Confidence scoring, manual review flags |
| Scope creep from "full automation" requests | High | Medium | Clear "decision support only" positioning |
| Model API costs exceed budget | Medium | Medium | Caching, smaller models for classification, cost monitoring |

---

## Summary Checklist

### What Exists
- [x] Value proposition
- [x] High-level architecture
- [x] Demo narrative
- [x] Evidence grounding concept
- [x] Failure mode awareness
- [x] Phase timeline (rough)

### What's Missing
- [ ] Technology stack specification
- [ ] Detailed functional requirements
- [ ] User stories with acceptance criteria
- [ ] Non-functional requirements
- [ ] Compliance framework details
- [ ] Data architecture/schemas
- [ ] API specifications
- [ ] Error handling procedures
- [ ] Testing strategy
- [ ] Monitoring requirements
- [ ] Success metrics/KPIs
- [ ] Security specifications
- [ ] Deployment architecture

---

## Conclusion

The current document is approximately **30% complete** as a production PRD. It provides excellent strategic direction and portfolio positioning but needs significant technical elaboration before implementation can begin.

**Recommended approach:** Use this document as the "vision" layer and create a separate "technical specification" document with the missing details. The PRD refinement system in this repository could be used to iteratively improve both documents.

---

*Review generated: 2026-02-02*
*Reviewer: Claude (AI-assisted analysis)*
