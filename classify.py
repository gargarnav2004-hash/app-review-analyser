"""
classify.py — Step 2: ask Claude to put each review into a topic.

How it works, in plain English:
  1. Reads Arnav's taxonomy.yaml and turns it into the instructions for Claude.
     (Edit taxonomy.yaml -> the instructions change -> the classifier changes.)
  2. Sends reviews to Claude in batches of 20.
  3. Claude returns, per review: topic, confidence (0-1), short reason.
  4. Checks each answer is valid. If a batch comes back broken, retries once.
     If it fails again, logs it to data/classify_failures.log and moves on (never crashes).
  5. Applies Arnav's "unclear" rule (CHECKPOINT D), then looks up severity from the topic
     using Arnav's fixed rule in taxonomy.yaml (CHECKPOINT C: money=3, technical=2, rest=1).
     Claude does NOT judge severity — it is plain code, so it is always consistent.
  6. Caches every answer, so re-running costs nothing and resumes after a crash.
     The cache file name includes the taxonomy version AND a fingerprint of the exact
     instructions (e.g. data/cache/llm_cache_v1_3f9a1c2b.json). So if even one word of
     taxonomy.yaml changes, reviews are re-classified with the new rules — no stale answers.

Run:
  python classify.py --input data/reviews_raw.csv --output data/reviews_classified.csv
  python classify.py --input data/reviews_raw.csv --output data/test.csv --limit 20 --exclude-golden
"""
import argparse
import hashlib
import json
import os

import anthropic
import pandas as pd
import yaml
from dotenv import load_dotenv

load_dotenv()  # reads ANTHROPIC_API_KEY from .env (never printed)

MODEL = "claude-haiku-5-5"
BATCH_SIZE = 20
TAXONOMY_FILE = "taxonomy.yaml"
CACHE_DIR = "data/cache"
FAILURE_LOG = "data/classify_failures.log"
GOLDEN_FILE = "data/golden_sample.csv"

# ---- Arnav's "unclear" rule (CHECKPOINT D, see DECISIONS.md) ----
# "model"     = only when Claude itself picks the "unclear" topic
# "threshold" = whenever Claude's confidence is below CONFIDENCE_THRESHOLD
# "both"      = either of the above   <- Arnav chose this
UNCLEAR_RULE = "both"
CONFIDENCE_THRESHOLD = 0.6
# -----------------------------------------------------------------


# ---------- 1. Build the prompt from taxonomy.yaml ----------

def load_taxonomy():
    with open(TAXONOMY_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_system_prompt(tax):
    """Turn taxonomy.yaml into instructions for Claude, word for word."""
    lines = [
        "You classify Google Play reviews of Kuku's two apps: Kuku FM (audio stories and audiobooks) "
        "and Kuku TV (short vertical video microdramas).",
        "Reviews may be in English, Hindi, Hinglish (Hindi in Latin letters) or other Indian languages. "
        "Read them in their own language. Do not translate them. Write your 'reason' in short English.",
        "",
        "Assign each review exactly ONE topic from the list below, using these definitions:",
        "",
    ]
    for name, t in tax["topics"].items():
        lines.append(f"## Topic: {name}")
        lines.append(f"Definition: {t.get('definition') or '(no definition given)'}")
        for ex in t.get("examples") or []:
            lines.append(f"Example review: \"{ex}\"")
        if t.get("boundary"):
            lines.append(f"Boundary rules: {t['boundary']}")
        lines.append("")

    if tax.get("multiple_complaints_rule"):
        lines.append(f"## If a review has more than one complaint\n{tax['multiple_complaints_rule']}")
        lines.append("")
    lines.append(
        "For each review also give 'confidence': a number from 0 to 1 for how sure you are "
        "about the topic, and 'reason': one short sentence explaining your choice."
    )
    return "\n".join(lines)


def topic_names(tax):
    return list(tax["topics"].keys())


# ---------- 2. Call Claude for one batch ----------

def output_schema(topics):
    """The exact JSON shape Claude must return."""
    item = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "topic": {"type": "string", "enum": topics},
            "confidence": {"type": "number"},
            "reason": {"type": "string"},
        },
        "required": ["id", "topic", "confidence", "reason"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {"results": {"type": "array", "items": item}},
        "required": ["results"],
        "additionalProperties": False,
    }


def call_claude(client, system_prompt, topics, batch):
    """Send one batch. Reviews get short ids (r1, r2, ...) so Claude can't mistype long review IDs."""
    numbered = "\n\n".join(f"[r{i+1}] {text}" for i, text in enumerate(batch["text"]))
    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=system_prompt,
        output_config={
            "effort": "low",
            "format": {"type": "json_schema", "schema": output_schema(topics)},
        },
        messages=[{"role": "user", "content": f"Classify these {len(batch)} reviews:\n\n{numbered}"}],
    )
    text = next((b.text for b in response.content if b.type == "text"), "")
    return text, response.usage


def validate(raw_text, batch, topics):
    """Check Claude's answer. Returns {review_id: result} or raises ValueError."""
    data = json.loads(raw_text)
    by_short_id = {r["id"]: r for r in data["results"]}
    out = {}
    for i, review_id in enumerate(batch["review_id"]):
        r = by_short_id.get(f"r{i+1}")
        if r is None:
            raise ValueError(f"missing result for r{i+1}")
        if r["topic"] not in topics:
            raise ValueError(f"bad topic {r['topic']!r}")
        if not 0 <= float(r["confidence"]) <= 1:
            raise ValueError(f"bad confidence {r['confidence']!r}")
        out[review_id] = {
            "ai_topic": r["topic"],
            "ai_confidence": round(float(r["confidence"]), 2),
            "ai_reason": r["reason"].strip(),
        }
    return out


def classify_batch(client, system_prompt, topics, batch):
    """Try once, retry once on bad output. Never raises — returns {} on failure."""
    for attempt in (1, 2):
        try:
            raw, usage = call_claude(client, system_prompt, topics, batch)
            return validate(raw, batch, topics), usage
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, anthropic.APIError) as e:
            with open(FAILURE_LOG, "a", encoding="utf-8") as log:
                log.write(f"attempt {attempt} failed for {list(batch['review_id'])}: "
                          f"{type(e).__name__}: {e}\n")
    return {}, None


# ---------- 3. The "unclear" rule ----------

def finalise(result, severity_by_topic):
    """Final topic (unclear rule, CHECKPOINT D) + severity looked up from it (CHECKPOINT C)."""
    out = apply_unclear_rule(result)
    out["severity"] = severity_by_topic.get(out["final_topic"])
    return out


def apply_unclear_rule(result):
    """Decides the final topic. Rule comes from CHECKPOINT D."""
    final = result["ai_topic"]
    low_conf = (CONFIDENCE_THRESHOLD is not None
                and result["ai_confidence"] < CONFIDENCE_THRESHOLD)
    if UNCLEAR_RULE == "threshold" and low_conf:
        final = "unclear"
    elif UNCLEAR_RULE == "both" and (final == "unclear" or low_conf):
        final = "unclear"
    # "model" (or not decided yet): keep Claude's own choice
    return {**result, "final_topic": final}


# ---------- 4. Cache ----------

def cache_path(version):
    return os.path.join(CACHE_DIR, f"llm_cache_{version}.json")


def load_cache(version):
    if os.path.exists(cache_path(version)):
        with open(cache_path(version), encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache, version):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path(version), "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)


# ---------- 5. Main ----------

def classify_dataframe(df, quiet=False):
    """Classify every review in df. Used by this script and by evaluate.py."""
    tax = load_taxonomy()
    topics = topic_names(tax)
    system_prompt = build_system_prompt(tax)
    # fingerprint = short code that changes whenever the instructions or model change
    fingerprint = hashlib.sha1((MODEL + system_prompt).encode()).hexdigest()[:8]
    version = f"{tax.get('version', 'v1')}_{fingerprint}"
    cache = load_cache(version)

    todo = df[~df["review_id"].isin(cache)]
    batches = [todo.iloc[i:i + BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
    if not quiet:
        print(f"Taxonomy {version}: {len(df) - len(todo)} cached, {len(todo)} to classify "
              f"in {len(batches)} batches")

    client = anthropic.Anthropic() if batches else None
    tokens_in = tokens_out = 0
    for n, batch in enumerate(batches, 1):
        results, usage = classify_batch(client, system_prompt, topics, batch)
        cache.update(results)
        save_cache(cache, version)            # save after every batch -> resumable
        if usage:
            tokens_in += usage.input_tokens
            tokens_out += usage.output_tokens
        if not quiet:
            done = int(30 * n / len(batches))
            print(f"\r[{'#' * done}{'.' * (30 - done)}] batch {n}/{len(batches)}", end="", flush=True)
    if batches and not quiet:
        print(f"\nTokens used: {tokens_in:,} in / {tokens_out:,} out")

    rows = []
    for _, r in df.iterrows():
        res = cache.get(r["review_id"])
        if res is None:
            rows.append({**r.to_dict(), "ai_topic": None, "ai_confidence": None,
                         "ai_reason": "FAILED", "final_topic": None, "severity": None})
        else:
            rows.append({**r.to_dict(), **finalise(res, tax["severity_by_topic"])})
    return pd.DataFrame(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/reviews_raw.csv")
    p.add_argument("--output", default="data/reviews_classified.csv")
    p.add_argument("--limit", type=int, help="only classify the first N reviews (for testing)")
    p.add_argument("--exclude-golden", action="store_true",
                   help="skip the hand-label reviews (keeps Arnav's labelling blind)")
    args = p.parse_args()

    df = pd.read_csv(args.input)
    if args.exclude_golden and os.path.exists(GOLDEN_FILE):
        golden_ids = set(pd.read_csv(GOLDEN_FILE)["review_id"])
        df = df[~df["review_id"].isin(golden_ids)]
    if args.limit:
        df = df.head(args.limit)

    out = classify_dataframe(df)
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    failed = out["final_topic"].isna().sum()
    print(f"Saved {len(out)} rows to {args.output} ({failed} failed — see {FAILURE_LOG})")


if __name__ == "__main__":
    main()
