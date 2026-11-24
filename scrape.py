"""
scrape.py — Step 1: download public Google Play reviews.

Settings below come from CHECKPOINT A in DECISIONS.md.
Output: data/reviews_raw.csv with columns
    review_id, app, rating, date, text, thumbs_up

Run:  python scrape.py
"""
import pandas as pd
from google_play_scraper import reviews, Sort

# ---- Arnav's choices (CHECKPOINT A) ----
APPS = {
    "Kuku FM": "com.vlv.aravali",          # audio stories
    "Kuku TV": "com.vlv.aravali.reels",    # short video microdramas
}
REVIEWS_PER_APP = 500   # kept reviews per app, after cleaning
SORT = Sort.NEWEST
MIN_WORDS = 2           # drop reviews with fewer than 2 words
# -----------------------------------------

OUTPUT = "data/reviews_raw.csv"


def fetch_app(app_name, package_id):
    """Pull reviews page by page until we have enough clean ones."""
    kept, seen_ids, seen_texts = [], set(), set()
    token = None
    while len(kept) < REVIEWS_PER_APP:
        batch, token = reviews(package_id, lang="en", country="in",
                               sort=SORT, count=200, continuation_token=token)
        if not batch:
            break
        for r in batch:
            text = (r.get("content") or "").strip()
            if len(text.split()) < MIN_WORDS:
                continue                      # empty or too short
            if r["reviewId"] in seen_ids or text.lower() in seen_texts:
                continue                      # duplicate
            seen_ids.add(r["reviewId"])
            seen_texts.add(text.lower())
            kept.append({
                "review_id": r["reviewId"],
                "app": app_name,
                "rating": r["score"],
                "date": r["at"].strftime("%Y-%m-%d"),
                "text": text,
                "thumbs_up": r.get("thumbsUpCount", 0),
            })
            if len(kept) >= REVIEWS_PER_APP:
                break
        if token is None:
            break
    print(f"{app_name}: kept {len(kept)} reviews")
    return kept


def main():
    rows = []
    for name, pid in APPS.items():
        rows.extend(fetch_app(name, pid))
    df = pd.DataFrame(rows).drop_duplicates(subset="review_id")
    df.to_csv(OUTPUT, index=False)
    print(f"Saved {len(df)} reviews to {OUTPUT}")


if __name__ == "__main__":
    main()
