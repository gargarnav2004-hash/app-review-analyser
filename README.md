# App Review Analyser: Kuku FM & Kuku TV

**Live dashboard:** https://kuku-review-analyser.streamlit.app/

**Problem:** teams can't read thousands of app reviews, so common complaints get missed.

**What this does:** it pulls public Google Play reviews of Kuku FM (audio stories) and Kuku TV (video microdramas). Claude sorts each review into a topic, the topics are ranked by how often they come up and how serious they are, and real reviews are shown as evidence. Reviews it can't read clearly are marked "unclear" instead of guessed, and the AI's labels are checked against a hand-labelled sample.

Every product and evaluation decision, and the reasoning behind it, is in [DECISIONS.md](DECISIONS.md).

## How it works

```
 Google Play                         taxonomy.yaml  (Arnav's topics + rules)
     │                                     │
     ▼                                     ▼
 scrape.py ──► data/reviews_raw.csv ──► classify.py ──► data/reviews_classified.csv
 (500 newest    (1,000 reviews)          Claude Haiku,           │
  per app)                               20 reviews per call,    │
                                         cached, retries once    │
                                                                  ▼
 make_golden.py ──► data/golden_sample.csv ──► evaluate.py   analyse.py
 (60 reviews)       (Arnav labels by hand,     (AI vs human)  (count × severity)
                     before seeing AI output)       │              │
                                                    ▼              ▼
                                         eval/results_v1.json  data/topic_ranking.csv
                                                    │              │
                                                    └──► app.py ◄──┘
                                                      (Streamlit dashboard)
```

1. **Scrape:** the 500 newest reviews per app. One-word and duplicate reviews are dropped.
2. **Classify:** the prompt is built straight from `taxonomy.yaml`, so editing the taxonomy changes the classifier. For each review, Claude returns a topic, a confidence (0–1) and a short reason. It reads Hindi, Hinglish and other Indian languages as they are, without translating.
3. **Unclear rule:** a review is "unclear" if Claude picks unclear itself **or** its confidence is below 0.6.
4. **Severity:** fixed per topic: autopay 3, technical 2, everything else 1. Praise, other and unclear get none.
5. **Rank:** priority score = number of reviews × severity. Praise, other and unclear are left out.
6. **Check:** compare the AI with 60 hand-labelled reviews.

## How to run it (3 commands)

First, copy `.env.example` to `.env` and put your Anthropic API key in it: `ANTHROPIC_API_KEY=sk-ant-...`.

```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
```
```bash
./venv/bin/python scrape.py && ./venv/bin/python classify.py && ./venv/bin/python analyse.py
```
```bash
./venv/bin/streamlit run app.py
```

Optional: `./venv/bin/python evaluate.py --run v1` re-runs the accuracy check against the hand labels.

Re-runs are free: every AI answer is cached. The cache resets automatically if `taxonomy.yaml` or the model changes.

**Swapping the model:** change `MODEL` at the top of `classify.py`. Everything else stays the same.

## Results (1,000 reviews, 13 Aug–21 Nov 2026)

**What to fix first (all apps):**

| Rank | Topic | Reviews | Severity | Priority score |
|---|---|---|---|---|
| 1 | autopay | 326 (33%) | 3 | 978 |
| 2 | technical | 39 (4%) | 2 | 78 |
| 3 | ads | 57 (6%) | 1 | 57 |
| 4 | quality | 32 (3%) | 1 | 32 |
| 5 | suggestion | 25 (3%) | 1 | 25 |

- **Autopay dominates both apps:** surprise ₹499/₹699 deductions after a ₹1 trial, trouble cancelling, refunds not received. It's 44% of all Kuku FM reviews and 21% of Kuku TV's.
- **The apps differ at #2:** technical issues for Kuku FM, **ads** for Kuku TV (9% of its reviews, against 2% for FM).
- 22% of reviews were marked unclear (very short or vague) and left out of the ranking.

**How accurate is it?** On 60 reviews hand-labelled blind, the AI agreed with the human **80%** of the time (48/60). On the harder reviews, excluding obvious praise and autopay complaints, it was about **62%**. Details are in [eval/EVAL_REPORT.md](eval/EVAL_REPORT.md).

**Cost:** about **$0.04 per 1,000 reviews** with `claude-haiku-5-5`. The full run cost $0.037.

## Limitations
- **Small evaluation set:** 60 reviews, one human labeller, and only one round (v2 was skipped). Several topics had 0–4 examples, so their accuracy is untested. After the disagreement review, every disagreement was judged a human error, which carries an anchoring risk.
- **Only recent reviews:** the 500 newest per app. Kuku TV's cover about 5 weeks, Kuku FM's about 3 months. This is a snapshot, not a trend.
- **Google Play only:** no App Store, social media or support tickets. People who leave reviews are mostly the very happy and the very angry.
- **The scraper uses the English locale:** many reviews written in Hindi script were probably never downloaded.
- **Severity is per topic, not per review:** a mild price comment and a ₹2,495 unauthorised charge both count as 3.
- **The LLM isn't deterministic:** re-running can change a few borderline labels, especially near the 0.6 confidence cut-off.
- **One topic per review:** a review with two complaints is filed under the one the user seems most upset about.
- **22% unclear:** many reviews are too short to act on, and the tool doesn't guess on them.
