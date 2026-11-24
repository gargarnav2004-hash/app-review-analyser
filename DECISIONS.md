# Decisions Log

Every product and evaluation decision in this project was made by Arnav. Each entry records the options considered, what was chosen, and the reason in Arnav's own words.

---

## CHECKPOINT A — Which apps, how many reviews, which sort, any filters

**Options presented:**
1. *Apps:* (a) Kuku FM + Pocket FM + Headfone — all Indian audio-drama apps, same business model; (b) Kuku + Pocket + Audible + Storytel — adds global audiobook apps with a different model; (c) all five.
2. *Volume:* 500 / 1,000 / 2,000 reviews per app.
3. *Sort:* "Newest" (current complaints, shorter reviews) vs "Most relevant" (richer text, but spans years).
4. *Star filter:* none (true mix, can measure share of unhappy users) vs 1–3 stars only (complaint-focused).
5. *Short reviews:* keep everything vs drop very short ones.

**Decision:**
1. Apps: **Kuku FM (`com.vlv.aravali`), Pocket FM (`com.radio.pocketfm`), Headfone (`com.headfone.www.headfone`)**
2. Volume: **500 reviews per app** (after cleaning)
3. Sort: **Newest**
4. Star filter: **None**
5. Short reviews: **Drop reviews under 2 words** (i.e. one-word reviews like "bad" are removed)

**Reason (Arnav's words):**
1. "i want to first cover indian market and focus on kukus competitor"
2. "for beginner analysing 500 reviews are enough"
3.
4.
5.

---

## CHECKPOINT A (revised) — Switch to Kuku's own two apps

**What changed:** After the first scrape, Arnav changed the app list from Kuku FM + Pocket FM + Headfone (all audio) to **Kuku FM (`com.vlv.aravali`) + Kuku TV (`com.vlv.aravali.reels`)**.

**Options presented:** (a) Kuku TV + microdrama competitors (ReelShort, DramaBox, Story TV/QuickTV); (b) Kuku TV + Kuku FM — Kuku's own audio and video apps; (c) Kuku TV only.

**Decision:** **Kuku TV + Kuku FM.** All other Checkpoint A settings unchanged: 500 newest reviews per app, no star filter, drop reviews under 2 words. Total ≈ 1,000 reviews.

**Reason (Arnav's words):** "it will be better if we use kuku tv reviews because they only give microdramas episode as input so i think we should make app review maker of both kuku tv and kuku fm"

**Consequences:** the Pocket FM / Headfone data was archived to `data/archive_v0_audio_apps/` (not deleted). The golden set was rebuilt from the new reviews. The cross-app view now compares Kuku's audio app with its video app, not Kuku against competitors.

---

## Golden set sampling (Phase 2)

**Options presented:** (a) Balanced by rating — 20 per app, 4 reviews at each star level 1–5, so plenty of hard mixed/mid-star cases; (b) Real-world mix — 20 per app matching each app's actual rating split, so accuracy reflects real data but few 2–4★ reviews.

**Decision:** **Balanced by rating.** Originally 3 apps × 5 star levels × 4 reviews; after the switch to two apps, **2 apps × 5 star levels × 6 reviews = 60**.

**Reason (Arnav's words):**

**Consequence to remember:** because the golden set over-represents 2–4★ reviews compared with the real data, the agreement score measures performance on a harder-than-average mix. It is not a direct estimate of accuracy on the full 1,500.

---

## CHECKPOINT B — Topic taxonomy (in progress)

**Starting point offered:** 7 empty slots (pricing, content, audio_quality, language, app_bugs, other, unclear).

**What Arnav did:** read negative reviews himself and grouped the complaints into his own categories: **Money related, Technical issue, "Review", Quality**. These replace the original slots. His notes are copied into `taxonomy.yaml` word for word (lightly cleaned for spelling).

**Questions asked and Arnav's answers (his words in quotes):**

| Question | Arnav's answer |
|---|---|
| What is the "Review" group called; separate or merged into money? | "unique problems" → topic `unique_problems`, kept separate |
| "Customer support poor": stay in money or own topic? | "own topic" → `customer_support` |
| "Payment done but not able to login": money or technical? | "technical" |
| Keep a language topic? | "keep it" |
| Ads (found in the live test: "add bht zyada hai" was misread as a price complaint) | "new one" → `ads` |
| What goes in other / unclear? | "do not consider" → kept as buckets (the classifier needs somewhere to put them) but **left out of the rankings** |
| Example reviews per topic? | "no" → no examples in the prompt |
| Praise | "you can add praise its upto you" |
| Everything else | "rest i am leaving upto you whatever you find suitable you can do it" |

**Rename:** after labelling, Arnav renamed `money` to **`autopay`** ("if possible change money to autopay"). His labels were renamed the same way. His untouched original sheet is kept at `data/golden_labels_original_by_arnav.csv`.

**Final topics (v1):** autopay, technical, unique_problems, quality, customer_support, ads, language, praise, other, unclear.

**Who wrote what:**
- *Arnav:* the topic list; the contents of money, technical, unique_problems and quality (from his own reading of negative reviews); the decisions to split out customer_support, ads and language; the login → technical rule.
- *Claude, delegated by Arnav:* the wording of praise, ads, customer_support, language, other and unclear; all boundary rules (e.g. "should be free" with no wrong charge → unique_problems; vague "not good" → unclear; money + bad support → money); and the rule for reviews with two complaints ("choose the one the user is most upset about"). Arnav should review these before the v2 round, since he will be asked about them.

**Effect seen in the 20-review live test (non-golden reviews):** "add bht zyada hai" moved from money (wrong) to ads; "free hona chaiye" moved from unclear to unique_problems; "now kuku tv is not good" moved from quality to unclear.

---

## CHECKPOINT C — Severity

**Options presented:** a 1–3 rubric that Arnav defines, judged by the AI review by review.

**Decision (Arnav's words):** "praise does not get severity, payment related issues severity 3, technical 2 rest severity 1"

So severity is a **fixed rule per topic**, not a per-review judgement: autopay = 3, technical = 2, unique_problems / quality / customer_support / ads / language = 1, praise = none. other and unclear also get none, because they are not considered.

**How it's built:** the rule lives in `taxonomy.yaml` (`severity_by_topic`). Severity is looked up in plain code after the topic is decided; Claude no longer outputs a severity. The golden sheet no longer has a `my_severity` column, because severity follows from the topic.

**Consequences to be ready to discuss:**
- Severity is perfectly consistent and explainable, but it can't tell a mild money complaint ("price thoda zyada hai") from a severe one ("₹2,495 deducted without permission"). Both get 3.
- Because severity follows from topic, "severity agreement" in the evaluation is no longer a separate test. If the topic matches, severity matches.
- In the priority ranking, severity now acts as a **topic weight** (autopay counts 3×, technical 2×).

**Reason (Arnav's words):**

## CHECKPOINT D — The "unclear" rule

**Options presented:**
1. *Claude decides* — unclear only when Claude picks the "unclear" topic. Simple, but models tend to be overconfident.
2. *Confidence cut-off* — unclear whenever Claude's self-reported confidence is below a chosen number. One adjustable dial, but the confidence is Claude's own estimate, not a true probability.
3. *Both* — unclear if Claude picks "unclear" OR confidence is below the cut-off. Safest against wrong guesses; more reviews drop out of the rankings.

**Decision:** **Both, with a confidence cut-off of 0.6.** Set in `classify.py` (`UNCLEAR_RULE = "both"`, `CONFIDENCE_THRESHOLD = 0.6`).

**Reason (Arnav's words):**

**Revisit:** at CHECKPOINT E, check how many golden-set reviews the 0.6 cut-off sends to unclear, and whether those were ones the AI would have got wrong.

## CHECKPOINT E — Disagreement review and taxonomy v2

**v1 result (against Arnav's original blind labels):** 80% agreement (48/60), 0 classifier failures. On the 26 reviews that were not praise or autopay, agreement was about 62%. Saved in `eval/results_v1.json`.

**Options presented for each of the 12 disagreements:** A = the AI was wrong · M = I (Arnav) was wrong · T = the taxonomy is ambiguous.

**Decision:** **All 12 marked M, "I was wrong".** Saved in the `verdict` column of `eval/disagreements_v1.csv`. Because there were no A or T verdicts, there is no taxonomy rule to change from this round.

**What was done with the labels:** Arnav's original blind labels are kept untouched in `my_topic`. A second column, `my_topic_corrected`, takes the AI's label for those 12 reviews. `evaluate.py --labels` can score against either column.

**Caution to be ready to discuss:** scored against the corrected labels, v1 is 100% by construction, because the corrections *are* the AI's answers. That number says nothing new about accuracy. The honest accuracy figure is the **80% against the blind labels**. Accepting every AI answer after seeing it also risks *anchoring*: a confident AI reason can make a defensible human label look wrong. #4 (praise vs. a pricing suggestion) and #12 (suggestion vs. ads) were cases where both answers were arguable.

**Reason (Arnav's words):**

### v2 round

**Options presented:** (a) label 30 fresh reviews blind and score the AI on them, for a clean second accuracy number; (b) skip v2 and move on to the full run; (c) another variant, such as re-labelling the 12 disputed reviews from scratch.

**Decision:** **Skip v2, move on.** No `eval/results_v2.json` was produced. The evaluation rests on v1 (80% against blind labels) plus the verdict review. See `eval/EVAL_REPORT.md`.

**Reason (Arnav's words):**

## CHECKPOINT F — Priority formula

**Options presented:**
1. *Count × severity.* Simple and follows the severity rule; autopay is likely to dominate.
2. *Count × severity, with thumbs-up weight.* Each review counts as 1 + its 👍 votes. Reflects shared pain, but viral reviews can dominate.
3. *Count × severity, 1–2★ reviews only.* Focuses on unhappy users, but ignores suggestions from happy ones.

**Decision:** **Count × severity.** `priority_score = number of reviews in the topic × the topic's severity`. It lives in one function, `priority_score()` in `analyse.py`. praise, other and unclear are left out of the ranking, because they have no severity ("do not consider").

**Consequence:** with 326 autopay reviews × 3, autopay ranks first overall by a wide margin. Ties between severity-1 topics are decided purely by how many reviews they have.

**Reason (Arnav's words):**

## CHECKPOINT G — Dashboard layout

**Question:** what would a Kuku PM want to see first?

**Options presented:**
1. *Keep as built:* header numbers → app filter → "What to fix first" (ranking, chart, example reviews), with Compare apps, Unclear and How we checked the AI behind tabs.
2. *Compare apps first:* lead with how Kuku FM and Kuku TV differ.
3. *Trust check up front:* agreement and "how we checked" directly under the headline numbers.
4. *Custom order.*

**Decision:** **Option 1, keep as built.** The ranking is the first thing a PM sees.

**Reason (Arnav's words):**

**Related build choice:** within a topic every review has the same severity, so example reviews are ordered by most 👍 first, rather than "highest severity first".

---

## What I'd do with more time
_(Arnav to write. Possible starting points from the build: a fresh blind test set; a second human labeller; per-review severity instead of per-topic; Hindi-locale scraping; tracking topics week by week; deploying the dashboard.)_
