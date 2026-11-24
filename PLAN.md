# Build Plan (3-hour budget)

Cut order if behind: cross-app comparison view → severity → polish. **Evaluation is never cut.**

- [x] **Phase 1 — Setup & scraping (20 min)** ✅ done (~15 min)
  - [x] venv, requirements.txt, .gitignore (.env ignored)
  - [x] Verify Play Store package IDs
  - [x] CHECKPOINT A — Arnav picks apps / volume / sort / filters
  - [x] scrape.py → data/reviews_raw.csv (1,500 reviews)
  - [x] REVISED: switched to Kuku FM + Kuku TV → 1,000 reviews; old data archived
  - [x] Show 10 random reviews + stats
- [x] **Phase 2 — Taxonomy & blind label set (30 min)** ✅
  - [x] CHECKPOINT B — taxonomy.yaml topics (11 topics incl. suggestion; Arnav + delegated drafts)
  - [x] CHECKPOINT C — severity fixed per topic (autopay 3, technical 2, rest 1, praise none)
  - [x] Live API test passed (20 non-golden reviews, 0 failures)
  - [x] Arnav hand-labels golden_sample.csv (my_topic only)
  - [x] data/golden_sample.csv (60 reviews, unlabelled, balanced by rating)
  - [x] classify.py (prompt built from taxonomy.yaml, batched, cached, validated)
  - [x] CHECKPOINT D — "unclear" rule (both, cut-off 0.6)
- [x] **Phase 3 — Evaluation (35 min)** ✅
  - [x] evaluate.py → eval/results_v1.json (v1: 80% agreement, 48/60)
  - [x] Every disagreement shown side by side (12)
  - [x] CHECKPOINT E — Arnav judged all 12 "I was wrong"; no taxonomy change
  - [x] v2 skipped (Arnav's decision); eval/EVAL_REPORT.md written
- [x] **Phase 4 — Full run & prioritisation (20 min)** ✅
  - [x] Cost estimate shown before running (~$0.04)
  - [x] Full classification: 1,000 reviews, 0 failures, actual cost $0.037
  - [x] CHECKPOINT F — count × severity (analyse.py, priority_score())
  - [x] data/topic_ranking.csv (overall + per app)
- [x] **Phase 5 — Dashboard (35 min)** ✅
  - [x] app.py (Streamlit) — all 4 tabs + app filter checked in browser
  - [x] CHECKPOINT G — option 1 (keep as built)
- [x] **Phase 6 — Interview docs (15 min)** ✅
  - [x] README.md, ARCHITECTURE.md, DECISIONS.md, INTERVIEW_QA.md
