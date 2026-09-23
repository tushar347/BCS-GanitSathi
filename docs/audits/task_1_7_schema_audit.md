# Task 1.7 Audit — Appendix A.1 Pydantic Event Schema

**Audit ID:** GS-U1-T1.7-AUDIT-001  
**Audit date:** 2026-09-13  
**Owners of audited artifact:** RA2 and RA3  
**Independent auditor:** RA1  
**Audited artifact:** `src/controller/schemas.py`  
**Reference:** `docs/GS_Main_Guide.pdf`, Appendix A.1 and the provenance rule in Appendix A.2  
**Overall verdict:** **Conditional Pass — development record only; revision required before verification or production use**

## Decision

The `Observation` model represents every field shown in the Appendix A.1 development example, accepts the example values, rejects missing required identifiers, and rejects invalid enum values. That is sufficient to continue prototype development.

It does not yet satisfy the complete Appendix A.1 production contract. Consent/data-access metadata, tool version, model revision, and links to relevant facts are absent; extra inputs are silently discarded; timestamps and identifiers are not validated; and the active admission path mutates the captured record. Task 1.7's independent audit is complete, but the implementation remains **Implemented**, not **Verified**.

## Scope and Evidence

Reviewed:

- Appendix A.1's example record and production additions.
- Appendix A.2's requirement to record a student event with immutable provenance.
- `src/controller/schemas.py` and the active observation construction/admission path.
- Schema imports in active and legacy controller modules.
- Existing tests and CI contract checks.

Not claimed by this audit:

- Approval of the broader Task 1.4 contracts for verification results, diagnostic hypotheses, learner claims, or actions.
- Compliance with a deployed consent, retention, privacy, or access-control policy.
- Validation under the project's required Python 3.11 runtime, which is not available locally.

## Appendix A.1 Traceability

| Appendix requirement | Schema evidence | Verdict |
| --- | --- | --- |
| Event, learner, item, family, and independent-evidence identifiers | `schemas.py:70-74` | **Present**, but empty strings are accepted |
| Event type | `schemas.py:75` | **Present** as an unconstrained string with the example default |
| Original and normalized text | `schemas.py:76-77` | **Present** |
| Assistance level | `schemas.py:78`, enum at `22-26` | **Present and enum-constrained** |
| Source type | `schemas.py:79` | **Present** as an unconstrained string |
| Interpretation and mathematical status | `schemas.py:80-81`, enums at `29-39` | **Present and enum-constrained** |
| Verification reason | `schemas.py:82` | **Present**, but may be omitted or empty |
| Candidate causes | `schemas.py:83`, enum at `13-19` | **Present and enum-constrained** |
| Evidence-admission and claim status | `schemas.py:84-85` | **Present**; admission defaults to `true` before admission is evaluated |
| Controller version | `schemas.py:86` | **Present**, but defaults to a release label rather than an exact commit |
| Timestamp for production | `schemas.py:87` | **Present**, but typed as `str`; non-date strings are accepted |
| Consent/data-access metadata | No field | **Missing** |
| Tool version | No distinct field | **Missing** |
| Model revision | No field | **Missing** |
| Links to relevant facts | No field on `Observation` | **Missing** |
| Evaluator-only cause/adjudication labels kept separate | No such evaluator-only fields found on `Observation` | **Pass for current schema** |

## Runtime Validation Evidence

The checks below were run with Python 3.13.3 and Pydantic 2.13.5 installed in an isolated temporary directory. They are supplementary because the project pins Python 3.11.

| Probe | Result |
| --- | --- |
| Instantiate the Appendix A.1 development example plus timestamp | **Accepted** |
| Omit required `event_id` | **Rejected** |
| Supply an invalid assistance enum | **Rejected** |
| Supply `timestamp="not-an-iso-timestamp"` | **Accepted** |
| Supply empty event, learner, and item identifiers | **Accepted** |
| Assign a new `original_text` after construction | **Accepted** |
| Supply unknown `consent_metadata` | **Accepted but silently discarded** |
| Supply hypothesis probability `1.5` | **Accepted** |
| Supply negative probe burden and out-of-range response likelihoods | **Accepted** |
| Import `schemas` and the active `diagnostic_controller` | **Passed** |
| Import legacy `admission`, `belief_model`, and `workspace` | **Failed** because they request removed schema/API names |

No repository files, caches, or bytecode were produced by these probes.

## Findings

### F1 — Production provenance fields are incomplete

**Severity:** High  
**Evidence:** Appendix A.1 explicitly requires timestamp, consent/data-access metadata, tool version, model revision, and links to relevant facts in production. Only a free-form timestamp and `controller_version` are present.

**Required action:** Add explicit, documented fields or nested metadata models for all production additions. Define which fields are mandatory at capture time and which may be nullable for non-model events. **Owner: RA2 + RA3.**

### F2 — Captured observations are mutable

**Severity:** High  
**Evidence:** `Observation` has no frozen model configuration, and assignment after creation succeeds. `src/controller/evidence_admission.py:60-64` changes `evidence_admitted` and appends to `verification_reason` on the same object.

This conflicts with Appendix A.2's immutable-provenance rule and makes the original capture state impossible to distinguish from a later adjudication.

**Required action:** Freeze the captured observation/provenance record. Represent verification, admission, and later adjudication as separate immutable records linked by `event_id`, or return a new versioned object without overwriting captured fields. **Owner: RA3; validator: RA1.**

### F3 — Validation is too weak for an audit record

**Severity:** High  
**Evidence:** Empty identifiers and invalid timestamp strings are accepted. The model also permits an empty verification reason and defaults `evidence_admitted` to `true` before the admission manager has evaluated the event.

**Required action:** Use non-empty constrained identifiers, a timezone-aware datetime type, and explicit pre-admission state or a separate admission result. Add cross-field checks for unresolved/unverifiable observations. **Owner: RA2 + RA3.**

### F4 — Unknown fields are silently discarded

**Severity:** Medium  
**Evidence:** Pydantic's default extra-field behavior is used. A supplied `consent_metadata` field is accepted as input but omitted from the resulting model.

For governance records this can create a false impression that required provenance was retained.

**Required action:** Set and test an explicit extra-field policy. Prefer rejecting unknown fields at contract boundaries; use deliberate schema versioning for forward compatibility. **Owner: RA3.**

### F5 — Controlled vocabularies and numeric bounds are incomplete

**Severity:** Medium  
**Evidence:** `event_type` and `source_type` are unconstrained strings. Related schema values that directly affect diagnostic behavior—hypothesis probabilities, probe likelihoods, and expected burden—have no range or normalization validation.

**Required action:** Define controlled vocabularies where the protocol depends on stable categories; constrain probabilities to `[0, 1]`, validate response distributions, and require non-negative burden. **Owner: RA2 + RA3.**

### F6 — Schema consumers are split across incompatible APIs

**Severity:** High for M1 integration; not a failure of the Appendix example itself  
**Evidence:** The active `diagnostic_controller` imports successfully. `admission.py`, `belief_model.py`, and `workspace.py` fail to import because they reference `ObservationRecord`, `LearnerClaim`, `InstructionalAction`, `BoundedProbeSelector`, or obsolete assistance enum members.

**Required action:** Declare one canonical schema/API surface, migrate consumers, and remove or quarantine superseded modules. **Owner: RA3.**

### F7 — Direct contract tests are absent

**Severity:** Medium  
**Evidence:** Current tests exercise selected controller behavior, but there is no Appendix A.1 fixture round-trip, production-metadata test, immutability test, strict-extra test, or JSON Schema snapshot/equivalence check.

**Required action:** Add positive and negative contract tests, including the exact appendix fixture and every required production field. Run them under Python 3.11 in CI. **Owner: RA2 + RA3; validator: RA1.**

## Conditions for Verification

RA1 can change this verdict to **Pass / Verified** only after all of the following are demonstrated:

1. The exact Appendix A.1 example round-trips without semantic loss.
2. Timestamp, consent/data access, tool version, model revision, and relevant-fact links are retained and validated.
3. Captured provenance cannot be overwritten by admission or later state updates.
4. Empty identifiers, malformed timestamps, invalid enums, out-of-range probabilities, and malformed response models are rejected.
5. The extra-field policy is explicit and tested.
6. One canonical controller path imports and passes its contract tests under Python 3.11.

## Sign-Off

**RA1 audit conclusion:** Conditional Pass for development use. The schema faithfully covers the illustrative Appendix A.1 record but is not a complete, immutable, production-grade event contract.  
**RA2/RA3 response:** Pending.  
**Supervisor acknowledgement:** Pending.  
**Verification status:** Pending corrective changes and RA1 retest.
