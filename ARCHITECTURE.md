# Architecture: what every file does

Written for someone who doesn't code. The files run in this order: **scrape → classify → analyse → dashboard**. Evaluation runs alongside them to check the AI.

## The scripts (run in this order)

| File | What it does |
|---|---|
| `scrape.py` | Downloads the newest public Google Play reviews for Kuku FM and Kuku TV (500 each). Throws away one-word reviews and duplicates. Saves them to `data/reviews_raw.csv`. The app list and settings are at the top of the file. |
| `make_golden.py` | Picks the 60 reviews for hand-labelling: 6 per app per star rating, chosen at random with a fixed seed so the pick can be reproduced. Saves `data/golden_sample.csv` with an empty `my_topic` column. Refuses to overwrite the file once it exists, so the labels are never lost. |
| `classify.py` | The AI step. Turns `taxonomy.yaml` into instructions for Claude, sends reviews 20 at a time, and gets back a topic, a confidence and a reason for each. Checks every answer and retries a broken batch once, and logs failures instead of crashing. It then applies the "unclear" rule (confidence below 0.6 → unclear) and looks up the severity from the topic. Saves every answer in a cache so re-runs are free. |
| `evaluate.py` | The accuracy check. Runs the classifier on the 60 hand-labelled reviews and compares it with Arnav's labels. Reports overall agreement, per-topic precision and recall, and a confusion matrix, and lists every disagreement. Saves `eval/results_<run>.json` and `eval/disagreements_<run>.csv`. |
| `analyse.py` | The ranking. Counts reviews per topic and applies Arnav's formula, `priority_score()` = count × severity, for all apps and for each app. Praise, other and unclear are left out. Saves `data/topic_ranking.csv`. |
| `app.py` | The Streamlit dashboard. Only reads the files above and never calls the AI. Has an app filter and four tabs: What to fix first, Compare apps, Unclear, and How we checked the AI. |

## The rules file

| File | What it does |
|---|---|
| `taxonomy.yaml` | Arnav's topics (autopay, technical, unique_problems, quality, customer_support, ads, language, suggestion, praise, other, unclear). Each has a definition and boundary rules, and there's a fixed severity per topic. **This is the classifier's brain:** edit a definition here and the AI's behaviour changes on the next run. |

## Data (`data/`)

| File | What it is |
|---|---|
| `reviews_raw.csv` | The 1,000 scraped reviews: review_id, app, rating, date, text, thumbs_up. |
| `golden_sample.csv` | The 60 hand-labelled reviews. `my_topic` holds Arnav's original blind labels; `my_topic_corrected` holds them after the disagreement review. |
| `golden_labels_original_by_arnav.csv` | An untouched copy of the sheet exactly as Arnav saved it, for honesty. |
| `reviews_classified.csv` | Every review plus the AI's topic, confidence, reason, final topic (after the unclear rule) and severity. |
| `topic_ranking.csv` | The ranked topics, overall and per app. |
| `cache/` | Saved AI answers, one file per taxonomy version. This is why re-runs cost nothing and a crash loses nothing. |
| `archive_v0_audio_apps/` | The first scrape (Kuku FM, Pocket FM, Headfone), kept from before the switch to Kuku FM + Kuku TV. |
| `classify_failures.log` | Created only if an AI batch fails twice. It didn't happen in the final runs. |

## Evaluation (`eval/`)

| File | What it is |
|---|---|
| `results_v1.json` | All the v1 accuracy numbers, plus every prediction on the 60 reviews. |
| `disagreements_v1.csv` | The 12 reviews where the AI and Arnav disagreed, side by side, with Arnav's verdict on each. |
| `EVAL_REPORT.md` | A plain-English write-up of the evaluation: results, verdicts, why v2 was skipped, and limitations. |

## Documents

| File | What it is |
|---|---|
| `README.md` | The overview: problem, how it works, how to run it, results, limitations. |
| `DECISIONS.md` | Every checkpoint: the options, what Arnav chose, and his reasons. |
| `INTERVIEW_QA.md` | Tough interview questions, with hints. Answers to be written by Arnav. |
| `PLAN.md` | The build checklist with time estimates. |

## Setup files

| File | What it is |
|---|---|
| `requirements.txt` | The Python packages the project needs: google-play-scraper, anthropic, pandas, streamlit, plotly, pyyaml, python-dotenv. |
| `.env` | Holds the Anthropic API key. **Never shared:** it's listed in `.gitignore`. |
| `.env.example` | A template showing what `.env` should look like, with no real key. |
| `.gitignore` | Tells git never to upload `.env`, the cache or the Python environment. |
| `venv/` | The project's own copy of Python and its packages, so nothing clashes with the rest of the computer. |
| `.claude/launch.json` | Lets Claude Code start the dashboard in its preview browser. Not needed to run the project yourself. |
