# Interview Q&A prep

Answers are for Arnav to write in his own words. Hints point to where the facts are.

---

### 1. Why did you choose this taxonomy? Why these topics and not others?
*Hint:* you built it by reading negative reviews yourself (DECISIONS.md, Checkpoint B), then added topics after the live test (ads) and after labelling (suggestion). Which topics came from your reading, and which did you delegate?

**My answer:**

---

### 2. How do you know the AI is accurate?
*Hint:* 60 reviews labelled blind before seeing AI output; 80% agreement; ~62% on the harder reviews. Why does the blind order matter? See eval/EVAL_REPORT.md.

**My answer:**

---

### 3. You marked all 12 disagreements as "I was wrong". Couldn't the AI have just persuaded you?
*Hint:* anchoring. Why is the 100% on corrected labels not a real result? Which cases (#4, #12) were genuinely arguable? What would you do differently, for example a fresh blind set or a second labeller?

**My answer:**

---

### 4. Why Claude Haiku and not a bigger model?
*Hint:* cost ($0.04 per 1,000 reviews), speed, and a simple single-label task. How would you test whether a bigger model is worth it? (Change `MODEL` in classify.py and re-run evaluate.py.)

**My answer:**

---

### 5. What does it cost per 1,000 reviews? What about 1 million?
*Hint:* full run = $0.037 for 1,000 (135k input / 46k output tokens). Scale it linearly, and mention caching and the batch API.

**My answer:**

---

### 6. What biases are in the scraped data?
*Hint:* newest only (FM covers ~3 months, TV ~5 weeks); Play Store only; reviewers skew very angry or very happy; the English-locale scrape misses Hindi-script reviews; dropping one-word reviews.

**My answer:**

---

### 7. How does it handle Hindi, Hinglish and other languages?
*Hint:* the prompt tells Claude to read reviews in their own language without translating. The live test handled Hinglish, Hindi and Tamil. What's untested? (No language-specific accuracy check.)

**My answer:**

---

### 8. What happens when a review has two complaints?
*Hint:* one topic per review: "the one the user is most upset about". What's lost? How would multi-label work, and how would it change the counts?

**My answer:**

---

### 9. Why is severity fixed per topic instead of judged per review?
*Hint:* your Checkpoint C rule. Trade-off: consistent and explainable vs. treating a mild price comment and a ₹2,495 unauthorised charge the same. Why technical (2) above ads (1)?

**My answer:**

---

### 10. Why count × severity for priority? Doesn't autopay just always win?
*Hint:* 978 vs 78. What would the thumbs-up or low-star variants have changed? Is a formula that confirms the obvious still useful? (It shows the gap and the #2 issue per app.)

**My answer:**

---

### 11. 22% of reviews went to "unclear". Isn't that a lot?
*Hint:* the "both" rule with a 0.6 cut-off; 54 were sent there by the cut-off alone. Most are very short ("poor app", "waste app"). What's the trade-off between coverage and accuracy?

**My answer:**

---

### 12. Why did you switch from Pocket FM / Headfone to Kuku TV?
*Hint:* DECISIONS.md, revised Checkpoint A, in your own words. Microdramas are where Kuku's work is going.

**My answer:**

---

### 13. Your evaluation set is only 60 reviews. Is that enough?
*Hint:* several topics have 0–4 examples; the set is balanced by rating, not the real-world mix; one labeller; one round. Why did you cap tuning at 2 rounds (overfitting to 60)?

**My answer:**

---

### 14. How would you put this into production at Kuku?
*Hint:* a weekly scheduled scrape, cached classification, trend lines per topic, alerts when a topic spikes, a route to the owning team (autopay → payments team), and periodic re-labelling to keep checking accuracy. Who is the human in the loop?

**My answer:**

---

### 15. What would you do with more time? What's the biggest weakness?
*Hint:* EVAL_REPORT.md, "What would make this stronger", and the README limitations. Pick the one you'd fix first and say why.

**My answer:**
