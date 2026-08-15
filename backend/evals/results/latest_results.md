# ShipIT AI Matching Evaluation Report

- **Generated:** 2026-08-11T19:58:57+00:00
- **Mode:** comparison (used: `deterministic (78% top-1) vs llm (78% top-1)`)
- **Note:** No LLM_API_KEY / LLM_PROVIDER configured — LLM mode fell back to the deterministic heuristic. Set LLM_PROVIDER=openrouter (or openai) and LLM_API_KEY in backend/.env to benchmark real LLM re-ranking.
- **Dataset:** `D:\shipit-adv\shipit1\project\backend\evals\data\matching_eval.json` v1.0.0
- **Test cases:** 40
- **Embedding:** deterministic (text-embedding-3-small, dim 1536)
- **Ranking:** heuristic (meta-llama/llama-3.1-8b-instruct)

## Metrics

| Metric | Value |
|--------|-------|
| Top-1 Accuracy | 77.5% (31/40) |
| Top-3 Accuracy | 100.0% |
| Mean Reciprocal Rank (MRR) | 0.887 |
| Average Match Score (top-1) | 0.72 |
| Expected driver retrieved | 100.0% |

## Latency

| Phase | Average |
|-------|---------|
| Retrieval (embed + pgvector/HNSW) | 12.3 ms |
| Ranking | 0.1 ms |
| Total pipeline | 12.5 ms |
| Candidates retrieved | 4.03 |

## Deterministic vs LLM Re-ranking

| Mode | Top-1 | Top-3 | MRR | Avg Match Score | Avg Total Latency |
|------|-------|-------|-----|-----------------|-------------------|
| Deterministic | 77.5% | 100.0% | 0.887 | 0.72 | 12.5 ms |
| LLM Re-rank | 77.5% | 100.0% | 0.887 | 0.72 | 12.3 ms |

## Per-Case Results

| Case | Scenario | Expected | Top-1 | Top-3 | RR | Latency |
|------|----------|----------|-------|-------|-----|---------|
| eval-001 | Noida Sector 62 to Vaishali | D101 | :white_check_mark: | :white_check_mark: | 1.000 | 20.3 ms |
| eval-002 | Connaught Place to Gurgaon Cyber City | D201 | :white_check_mark: | :white_check_mark: | 1.000 | 15.3 ms |
| eval-003 | Greater Noida to Noida Sector 18 (reversed route distractor) | D301 | :x: | :white_check_mark: | 0.500 | 13.3 ms |
| eval-004 | Faridabad to Lajpat Nagar | D401 | :white_check_mark: | :white_check_mark: | 1.000 | 13.3 ms |
| eval-005 | Gurgaon Sector 14 to Dwarka | D501 | :x: | :white_check_mark: | 0.500 | 13.2 ms |
| eval-006 | Karol Bagh to Rohini | D601 | :white_check_mark: | :white_check_mark: | 1.000 | 13.7 ms |
| eval-007 | Noida Sector 137 to Faridabad | D701 | :white_check_mark: | :white_check_mark: | 1.000 | 13.3 ms |
| eval-008 | Ghaziabad to Connaught Place | D801 | :white_check_mark: | :white_check_mark: | 1.000 | 11.9 ms |
| eval-009 | Dwarka to Gurgaon MG Road | D901 | :x: | :white_check_mark: | 0.500 | 12.1 ms |
| eval-010 | Saket to Noida Sector 62 (near-tie corridor) | D1001 | :white_check_mark: | :white_check_mark: | 1.000 | 12.3 ms |
| eval-011 | Delhi to Agra (long haul) | D1101 | :white_check_mark: | :white_check_mark: | 1.000 | 12.4 ms |
| eval-012 | Delhi to Chandigarh (long haul) | D1201 | :x: | :white_check_mark: | 0.500 | 11.6 ms |
| eval-013 | Delhi to Jaipur (long haul) | D1301 | :white_check_mark: | :white_check_mark: | 1.000 | 12.2 ms |
| eval-014 | Delhi to Dehradun (long haul) | D1401 | :white_check_mark: | :white_check_mark: | 1.000 | 11.2 ms |
| eval-015 | Noida to Delhi Airport (IGI) | D1501 | :white_check_mark: | :white_check_mark: | 1.000 | 12.5 ms |
| eval-016 | Gurgaon to Noida Sector 18 | D1601 | :white_check_mark: | :white_check_mark: | 1.000 | 11.7 ms |
| eval-017 | Indirapuram to Noida Sector 18 | D1701 | :white_check_mark: | :white_check_mark: | 1.000 | 12.0 ms |
| eval-018 | Vaishali to Saket | D1801 | :white_check_mark: | :white_check_mark: | 1.000 | 11.6 ms |
| eval-019 | Faridabad to Gurgaon | D1901 | :white_check_mark: | :white_check_mark: | 1.000 | 12.0 ms |
| eval-020 | Rohini to Janakpuri | D2001 | :white_check_mark: | :white_check_mark: | 1.000 | 12.1 ms |
| eval-021 | Lajpat Nagar to Noida Sector 62 (hard tie) | D2101 | :x: | :white_check_mark: | 0.500 | 12.1 ms |
| eval-022 | Noida Sector 62 to Connaught Place (hard reverse) | D2201 | :x: | :white_check_mark: | 0.500 | 12.5 ms |
| eval-023 | Connaught Place to Faridabad (900 kg truck) | D2301 | :white_check_mark: | :white_check_mark: | 1.000 | 11.6 ms |
| eval-024 | Connaught Place to Gurgaon (urgent 4h) | D2401 | :x: | :white_check_mark: | 0.500 | 12.4 ms |
| eval-025 | Ghaziabad to Greater Noida | D2501 | :x: | :white_check_mark: | 0.500 | 11.7 ms |
| eval-026 | Greater Noida to Faridabad | D2601 | :white_check_mark: | :white_check_mark: | 1.000 | 13.9 ms |
| eval-027 | Connaught Place to Noida Sector 137 | D2701 | :white_check_mark: | :white_check_mark: | 1.000 | 11.6 ms |
| eval-028 | Gurgaon to Faridabad | D2801 | :white_check_mark: | :white_check_mark: | 1.000 | 12.1 ms |
| eval-029 | Saket to Gurgaon MG Road (hard near-tie) | D2901 | :x: | :white_check_mark: | 0.500 | 11.8 ms |
| eval-030 | Dwarka to Karol Bagh | D3001 | :white_check_mark: | :white_check_mark: | 1.000 | 11.8 ms |
| eval-031 | Noida Sector 18 to Ghaziabad (light bicycle parcel) | D3101 | :white_check_mark: | :white_check_mark: | 1.000 | 12.6 ms |
| eval-032 | Janakpuri to Rohini (intra-city) | D3201 | :white_check_mark: | :white_check_mark: | 1.000 | 12.0 ms |
| eval-033 | Agra to Delhi (long-haul reverse, hard) | D3301 | :white_check_mark: | :white_check_mark: | 1.000 | 11.9 ms |
| eval-034 | Chandigarh to Delhi (long haul) | D3401 | :white_check_mark: | :white_check_mark: | 1.000 | 11.4 ms |
| eval-035 | Delhi to Lucknow (long haul) | D3501 | :white_check_mark: | :white_check_mark: | 1.000 | 12.5 ms |
| eval-036 | Lucknow to Kanpur (regional) | D3601 | :white_check_mark: | :white_check_mark: | 1.000 | 11.7 ms |
| eval-037 | Jaipur to Delhi (long haul) | D3701 | :white_check_mark: | :white_check_mark: | 1.000 | 11.6 ms |
| eval-038 | Noida Sector 62 to Noida Sector 137 (intra-Noida) | D3801 | :white_check_mark: | :white_check_mark: | 1.000 | 11.8 ms |
| eval-039 | Dehradun to Delhi (hard reverse long haul) | D3901 | :white_check_mark: | :white_check_mark: | 1.000 | 11.1 ms |
| eval-040 | Connaught Place to Ghaziabad | D4001 | :white_check_mark: | :white_check_mark: | 1.000 | 12.7 ms |

## Successes

eval-035 (Delhi to Lucknow (long haul)), eval-011 (Delhi to Agra (long haul)), eval-013 (Delhi to Jaipur (long haul)), eval-001 (Noida Sector 62 to Vaishali), eval-033 (Agra to Delhi (long-haul reverse, hard))

## Failures

eval-003 (Greater Noida to Noida Sector 18 (reversed route distractor)), eval-005 (Gurgaon Sector 14 to Dwarka), eval-022 (Noida Sector 62 to Connaught Place (hard reverse)), eval-024 (Connaught Place to Gurgaon (urgent 4h)), eval-009 (Dwarka to Gurgaon MG Road)

## Interview-Ready Examples (Explainability)

### Example 1 — Noida Sector 62 to Vaishali

**Parcel:** Noida Sector 62, Uttar Pradesh → Vaishali, Ghaziabad, Uttar Pradesh

**Expected Driver:** D101
**Acceptable Drivers:** D104

**Predicted Ranking:**

1. D101 (0.77)
2. D104 (0.76)
3. D102 (0.74)
4. D105 (0.67)
5. D103 (0.51)

**Reason** (top match):

- Route overlap: 58%
- Pickup detour: 0.0 km
- Delivery deadline: 24.0h away
- Vehicle capacity sufficient (5.0kg of 60kg)
- Driver reliability: 4.9/5
- On-time rate: 96%

*Verdict: top-1 prediction is **correct**.*

### Example 2 — Delhi to Agra (long haul)

**Parcel:** Karol Bagh, New Delhi → Agra, Uttar Pradesh

**Expected Driver:** D1101
**Acceptable Drivers:** D1104

**Predicted Ranking:**

1. D1101 (0.79)
2. D1104 (0.78)
3. D1103 (0.74)
4. D1102 (0.74)

**Reason** (top match):

- Route overlap: 44%
- Pickup detour: 0.0 km
- Delivery deadline: 48.0h away
- Vehicle capacity sufficient (300.0kg of 1200kg)
- Driver reliability: 4.7/5
- On-time rate: 92%

*Verdict: top-1 prediction is **correct**.*

### Example 3 — Delhi to Jaipur (long haul)

**Parcel:** Karol Bagh, New Delhi → Jaipur, Rajasthan

**Expected Driver:** D1301
**Acceptable Drivers:** D1303

**Predicted Ranking:**

1. D1301 (0.78)
2. D1304 (0.76)
3. D1303 (0.76)
4. D1302 (0.72)

**Reason** (top match):

- Route overlap: 47%
- Pickup detour: 0.0 km
- Delivery deadline: 40.0h away
- Vehicle capacity sufficient (220.0kg of 1200kg)
- Driver reliability: 4.7/5
- On-time rate: 91%

*Verdict: top-1 prediction is **correct**.*

### Example 4 — Agra to Delhi (long-haul reverse, hard)

**Parcel:** Agra, Uttar Pradesh → Karol Bagh, New Delhi

**Expected Driver:** D3301
**Acceptable Drivers:** D3302

**Predicted Ranking:**

1. D3301 (0.76)
2. D3304 (0.76)
3. D3302 (0.70)
4. D3303 (0.70)

**Reason** (top match):

- Route overlap: 42%
- Pickup detour: 0.0 km
- Delivery deadline: 40.0h away
- Vehicle capacity sufficient (250.0kg of 1200kg)
- Driver reliability: 4.7/5
- On-time rate: 92%

*Verdict: top-1 prediction is **correct**.*

### Example 5 — Delhi to Lucknow (long haul)

**Parcel:** Karol Bagh, New Delhi → Lucknow, Uttar Pradesh

**Expected Driver:** D3501
**Acceptable Drivers:** D3504

**Predicted Ranking:**

1. D3501 (0.81)
2. D3503 (0.78)
3. D3502 (0.78)
4. D3504 (0.70)

**Reason** (top match):

- Route overlap: 49%
- Pickup detour: 0.0 km
- Delivery deadline: 50.0h away
- Vehicle capacity sufficient (500.0kg of 1200kg)
- Driver reliability: 4.7/5
- On-time rate: 92%

*Verdict: top-1 prediction is **correct**.*

## Recommendations

- Deterministic mode is fully offline, zero-cost, and reproducible — keep it as the production default for cost-sensitive or air-gapped deployments.
- LLM re-ranking only adds value on the ambiguous / near-tie cases; gate it to the top retrieval results so cost stays bounded (retrieval-first keeps the LLM call small).
- Route embeddings are refreshed on creation only. Periodically re-embed (POST /routes/me/embed) after drivers update their routes.
- The pickup-detour signal currently falls back to token-overlap when GPS is absent. Adding geocoded waypoints should improve the tie-break cases.
- Track match outcomes (accept/reject per ranked driver) in production to build a labeled feedback loop that this offline dataset cannot capture.

## Reproducibility

```
python backend/evals/evaluate_matching.py --mode comparison
```

The dataset is version-controlled and seeded into a disposable `shipit_eval` database with a fixed deterministic embedding; reruns are bit-for-bit reproducible in deterministic mode.