"""
make_golden.py — builds the 60-review hand-label set.

Sampling (Arnav's decision): balanced by rating —
2 apps x 5 star levels x 6 reviews = 60.
my_topic is left EMPTY (severity follows from topic, so no severity column) for Arnav to fill in by hand.

Run once:  python make_golden.py   (refuses to overwrite an existing file)
"""
import os
import pandas as pd

PER_CELL = 6          # reviews per (app, star rating) -> 2 apps x 5 stars x 6 = 60
SEED = 42             # fixed so the sample is reproducible
OUTPUT = "data/golden_sample.csv"

if os.path.exists(OUTPUT):
    raise SystemExit(f"{OUTPUT} already exists — not overwriting your labels.")

df = pd.read_csv("data/reviews_raw.csv")
# Shuffle everything, then take the first PER_CELL reviews in each (app, rating) group
shuffled = df.sample(frac=1, random_state=SEED)
sample = shuffled.groupby(["app", "rating"]).head(PER_CELL)
sample["my_topic"] = ""
sample[["review_id", "app", "rating", "date", "text", "my_topic"]] \
    .to_csv(OUTPUT, index=False, encoding="utf-8-sig")  # utf-8-sig so Excel shows Hindi correctly
print(f"Saved {len(sample)} reviews to {OUTPUT}")
print(sample.groupby(["app", "rating"]).size().unstack().to_string())
