# Evaluation Report

**Question:** when the AI sorts a review into a topic, does it agree with a human (Arnav) who read the same review?

## Setup
- **Golden set:** 60 reviews: 2 apps (Kuku FM, Kuku TV) × 5 star levels × 6 reviews each. They were sampled at random within each group, with a fixed seed.
- **Blind labelling:** Arnav labelled all 60 by hand **before** seeing any AI output.
- **Classifier:** `claude-haiku-5-5`, with the prompt built from `taxonomy.yaml` v1 (11 topics).
- **Unclear rule:** a review is marked unclear if the AI picks "unclear" **or** its confidence is below 0.6.
- **Severity:** fixed per topic (autopay 3, technical 2, rest 1, praise none), so it isn't evaluated separately.

## v1 results (against Arnav's blind labels)

| Metric | Result |
|---|---|
| **Overall topic agreement** | **80% (48/60)** |
| Agreement on the 26 reviews that were not praise or autopay | ~62% (16/26) |
| Agreement when the AI did not say "unclear" | 78% (40/51) |
| Reviews the AI sent to unclear | 9 (7 by its own choice, 2 below the 0.6 cut-off). Arnav labelled 12 as unclear. |
| Classifier failures (bad JSON etc.) | 0 |
| Cost of the run | ~$0.002 (8.2k input / 2.9k output tokens) |

### Per topic
*Precision* = when the AI says this topic, how often Arnav agreed. *Recall* = when Arnav said this topic, how often the AI agreed.

| Topic | Arnav | AI | Agree | Precision | Recall |
|---|---|---|---|---|---|
| autopay | 12 | 12 | 12 | 1.00 | 1.00 |
| praise | 22 | 22 | 20 | 0.91 | 0.91 |
| unclear | 12 | 9 | 8 | 0.89 | 0.67 |
| ads | 4 | 5 | 4 | 0.80 | 1.00 |
| suggestion | 3 | 6 | 2 | 0.33 | 0.67 |
| technical | 1 | 4 | 1 | 0.25 | 1.00 |
| quality | 1 | 2 | 1 | 0.50 | 1.00 |
| unique_problems | 4 | 0 | 0 | — | 0.00 |
| other | 1 | 0 | 0 | — | 0.00 |
| customer_support, language | 0 | 0 | 0 | — | — |

The full confusion matrix is in `eval/results_v1.json`.

### Where they disagreed (12 reviews)
- **unique_problems (4):** Arnav used this label more broadly than its written definition, which lists only "TV subscription switched to FM" and "no free episodes". The AI chose praise, quality, suggestion or technical instead.
- **"Can't install / won't open" (2):** Arnav said unclear; the AI said technical.
- **Very short or emoji-only reviews (2):** the line between praise and unclear isn't defined.
- **Suggestion vs. the underlying topic (3):** for example, "reduce the ads" (suggestion or ads?) and "subscription too expensive, please change it" (praise or suggestion?).
- **An episode-length request (1):** Arnav said other; the AI said suggestion.

Every disagreement is listed side by side in `eval/disagreements_v1.csv`.

## Checkpoint E: human review of the disagreements
For each disagreement, Arnav chose one verdict: AI wrong / I was wrong / taxonomy ambiguous.

**Result: all 12 were judged "I was wrong".** No taxonomy rule was changed.

- Arnav's original labels are kept unchanged (`my_topic`). The corrected labels are in a separate column (`my_topic_corrected`).
- Scored against the corrected labels, v1 is 100%, but **only by construction**, because the corrections are the AI's own answers. That number is not evidence of accuracy, and it isn't used as the headline.

## v2
**Not run.** Arnav decided to skip v2 and move on (see DECISIONS.md).

- With no taxonomy changes, re-running against the corrected labels would only repeat the 100%.
- A fresh blind set of 30 reviews was offered as an alternative and not chosen.
- The plan capped tuning at 2 rounds anyway, because tuning to 60 reviews risks overfitting.

## Honest limitations
1. **Small sample:** 60 reviews, and several topics have 0–4 examples. Per-topic precision and recall for small topics are not reliable.
2. **Not a real-world mix:** the golden set is balanced by star rating, so it has far more 2–4★ reviews than the real data. Real data is mostly 1★ autopay complaints and 5★ praise, which the AI gets right almost every time. So real-world agreement is probably **higher** than 80%, while agreement on nuanced reviews is **lower** (~62%).
3. **Anchoring risk:** Arnav accepted the AI's answer on all 12 disagreements after reading its reasons. Some of those cases had more than one defensible answer.
4. **Topics with no evidence:** after the corrections, the golden set contains no unique_problems, other, customer_support or language reviews. The AI's behaviour on those topics is untested.
5. **One labeller:** there's no second human to measure how often two people would agree with each other.
6. **The LLM isn't deterministic:** a re-run can change a few borderline labels, especially near the 0.6 confidence cut-off.

## What would make this stronger
- Label a fresh blind set of 30–50 reviews that was never used for tuning.
- Add a second human labeller and measure human-to-human agreement as a ceiling.
- Write explicit rules for suggestion vs. underlying topic, and for emoji-only reviews.
- Run the classifier twice on the same set to measure how many labels change.
