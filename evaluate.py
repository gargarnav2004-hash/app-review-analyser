"""
evaluate.py — Step 3: how often does the AI agree with Arnav's hand labels?

How it works, in plain English:
  1. Loads Arnav's 60 hand-labelled reviews (data/golden_sample.csv, column my_topic).
  2. Runs the classifier on those same 60 reviews (using the current taxonomy.yaml).
  3. Compares AI vs Arnav and reports:
       - overall agreement (% of reviews where the topics match)
       - per-topic precision and recall
       - a confusion matrix (which topics get mixed up with which)
       - severity agreement (note: severity follows from topic, so this mirrors topic agreement)
       - how many reviews went to "unclear", and why
  4. Lists EVERY disagreement side by side: review | Arnav's label | AI label | AI reason.
  5. Saves everything to eval/results_<run>.json and eval/disagreements_<run>.csv
     (the CSV has an empty "verdict" column for CHECKPOINT E).

Run:  python evaluate.py --run v1
"""
import argparse
import json
import os

import pandas as pd

import classify

GOLDEN_FILE = "data/golden_sample.csv"


def per_topic_table(df, topics):
    """Precision = when the AI says X, how often Arnav also said X.
       Recall    = when Arnav said X, how often the AI also said X."""
    rows = []
    for t in topics:
        ai_says = df["final_topic"] == t
        arnav_says = df["my_topic"] == t
        both = (ai_says & arnav_says).sum()
        rows.append({
            "topic": t,
            "arnav_count": int(arnav_says.sum()),
            "ai_count": int(ai_says.sum()),
            "both_agree": int(both),
            "precision": round(both / ai_says.sum(), 2) if ai_says.sum() else None,
            "recall": round(both / arnav_says.sum(), 2) if arnav_says.sum() else None,
        })
    return pd.DataFrame(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, help="name of this run, e.g. v1 or v2")
    p.add_argument("--labels", default="my_topic",
                   help="which label column to compare against: my_topic (Arnav's original "
                        "blind labels) or my_topic_corrected (after CHECKPOINT E)")
    args = p.parse_args()

    golden = pd.read_csv(GOLDEN_FILE)
    golden["my_topic"] = golden[args.labels].str.strip().str.lower()
    print(f"Comparing against label column: {args.labels}")
    tax = classify.load_taxonomy()
    topics = classify.topic_names(tax)
    sev_map = tax["severity_by_topic"]

    df = classify.classify_dataframe(golden)
    failed = df["final_topic"].isna()
    df = df[~failed].copy()
    df["match"] = df["my_topic"] == df["final_topic"]

    # --- headline numbers ---
    n = len(df)
    agreement = df["match"].mean()
    not_unclear = df[df["final_topic"] != "unclear"]
    agreement_when_ai_answers = not_unclear["match"].mean() if len(not_unclear) else None

    # --- unclear breakdown ---
    ai_unclear = df[df["final_topic"] == "unclear"]
    picked_by_model = (ai_unclear["ai_topic"] == "unclear").sum()
    by_threshold = (ai_unclear["ai_topic"] != "unclear").sum()

    # --- severity (derived from topic) ---
    df["my_severity"] = df["my_topic"].map(sev_map)
    sev = df.dropna(subset=["my_severity", "severity"])
    sev_exact = (sev["my_severity"] == sev["severity"]).mean() if len(sev) else None
    sev_within1 = ((sev["my_severity"] - sev["severity"]).abs() <= 1).mean() if len(sev) else None

    table = per_topic_table(df, topics)
    confusion = pd.crosstab(df["my_topic"], df["final_topic"],
                            rownames=["Arnav ↓"], colnames=["AI →"])

    disagreements = df[~df["match"]][["review_id", "app", "rating", "text", "my_topic",
                                      "final_topic", "ai_topic", "ai_confidence", "ai_reason"]]

    # --- print report ---
    print(f"\n===== EVALUATION {args.run}  (taxonomy {tax.get('version')}, model {classify.MODEL}) =====")
    print(f"Reviews compared: {n}   (classifier failures: {int(failed.sum())})")
    print(f"Overall topic agreement: {agreement:.0%}  ({int(df['match'].sum())}/{n})")
    if agreement_when_ai_answers is not None:
        print(f"Agreement when the AI did NOT say unclear: {agreement_when_ai_answers:.0%} "
              f"({int(not_unclear['match'].sum())}/{len(not_unclear)})")
    print(f"AI sent {len(ai_unclear)} reviews to unclear: {picked_by_model} by its own choice, "
          f"{by_threshold} because confidence < {classify.CONFIDENCE_THRESHOLD}. "
          f"(Arnav labelled {int((df['my_topic'] == 'unclear').sum())} as unclear.)")
    if sev_exact is not None:
        print(f"Severity agreement (both sides had a severity, n={len(sev)}): exact {sev_exact:.0%}, "
              f"within ±1 {sev_within1:.0%}  — note: severity is fixed by topic")
    print("\nPer-topic precision / recall:")
    print(table.to_string(index=False))
    print("\nConfusion matrix (rows = Arnav, columns = AI):")
    print(confusion.to_string())
    print(f"\nDisagreements: {len(disagreements)}")

    # --- save ---
    os.makedirs("eval", exist_ok=True)
    out = {
        "run": args.run,
        "model": classify.MODEL,
        "taxonomy_version": tax.get("version"),
        "label_column": args.labels,
        "unclear_rule": classify.UNCLEAR_RULE,
        "confidence_threshold": classify.CONFIDENCE_THRESHOLD,
        "n_reviews": n,
        "classifier_failures": int(failed.sum()),
        "overall_agreement": round(agreement, 3),
        "agreement_when_ai_not_unclear": round(agreement_when_ai_answers, 3) if agreement_when_ai_answers is not None else None,
        "ai_unclear_total": int(len(ai_unclear)),
        "ai_unclear_by_model": int(picked_by_model),
        "ai_unclear_by_threshold": int(by_threshold),
        "arnav_unclear_total": int((df["my_topic"] == "unclear").sum()),
        "severity_exact": round(sev_exact, 3) if sev_exact is not None else None,
        "severity_within_1": round(sev_within1, 3) if sev_within1 is not None else None,
        "per_topic": table.astype(object).where(table.notna(), None).to_dict(orient="records"),
        "confusion_matrix": confusion.to_dict(),
        "disagreements": disagreements.to_dict(orient="records"),
        "all_predictions": df[["review_id", "my_topic", "final_topic", "ai_topic",
                               "ai_confidence", "ai_reason"]].to_dict(orient="records"),
    }
    with open(f"eval/results_{args.run}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
    dis = disagreements.copy()
    dis["verdict"] = ""   # Arnav fills: ai_wrong / i_was_wrong / ambiguous
    dis.to_csv(f"eval/disagreements_{args.run}.csv", index=False, encoding="utf-8-sig")
    print(f"Saved eval/results_{args.run}.json and eval/disagreements_{args.run}.csv")


if __name__ == "__main__":
    main()
