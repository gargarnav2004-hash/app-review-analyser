"""
analyse.py — Step 4: rank the topics by priority ("what to fix first").

How it works, in plain English:
  1. Reads the classified reviews (data/reviews_classified.csv).
  2. Leaves out topics with no severity: praise, other, unclear (Arnav: "do not consider").
  3. For each topic, counts reviews and computes the priority score with Arnav's formula
     (CHECKPOINT F): count x severity.
  4. Does this for all reviews together AND for each app separately.
  5. Saves data/topic_ranking.csv.

Run:  python analyse.py
"""
import pandas as pd

INPUT = "data/reviews_classified.csv"
OUTPUT = "data/topic_ranking.csv"


def priority_score(count, severity):
    """Arnav's priority formula (CHECKPOINT F): number of reviews x topic severity.
    Severity is fixed per topic in taxonomy.yaml: autopay 3, technical 2, the rest 1."""
    return count * severity


def rank_topics(df, scope_name):
    """Rank topics for one group of reviews (all reviews, or one app)."""
    total_reviews = len(df)
    ranked = df.dropna(subset=["severity"])          # drops praise / other / unclear
    rows = []
    for topic, group in ranked.groupby("final_topic"):
        count = len(group)
        severity = int(group["severity"].iloc[0])     # same for every review in a topic
        rows.append({
            "scope": scope_name,
            "topic": topic,
            "count": count,
            "share_of_all_reviews_pct": round(100 * count / total_reviews, 1),
            "avg_severity": severity,
            "priority_score": priority_score(count, severity),
        })
    out = pd.DataFrame(rows).sort_values(["priority_score", "count"], ascending=False)
    out.insert(1, "rank", range(1, len(out) + 1))
    return out


def main():
    df = pd.read_csv(INPUT)
    tables = [rank_topics(df, "All apps")]
    for app_name, group in df.groupby("app"):
        tables.append(rank_topics(group, app_name))
    result = pd.concat(tables, ignore_index=True)
    result.to_csv(OUTPUT, index=False)
    for scope, t in result.groupby("scope", sort=False):
        print(f"\n=== {scope} ===")
        print(t.drop(columns="scope").to_string(index=False))
    print(f"\nSaved {OUTPUT}")


if __name__ == "__main__":
    main()
