"""
app.py — Step 5: the dashboard.

Run:  streamlit run app.py      (then open the link it prints, usually http://localhost:8501)

What's on it:
  - Header: the problem in one line + headline numbers
  - App filter (All / Kuku FM / Kuku TV)
  - Tab "What to fix first": ranked topics (Arnav's formula) + bar chart + real example reviews
  - Tab "Compare apps": topic share for Kuku FM vs Kuku TV side by side
  - Tab "Unclear": reviews the tool refused to guess on
  - Tab "How we checked the AI": evaluation results vs Arnav's hand labels
It only READS files made by the other scripts — it never calls the AI.
"""
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from analyse import rank_topics

st.set_page_config(page_title="App Review Analyser", page_icon="📊", layout="wide")

# Chart colours (validated colour-blind-safe palette): one fixed colour per app
APP_COLOURS = {"Kuku FM": "#2a78d6", "Kuku TV": "#eb6834"}
BAR_COLOUR = "#2a78d6"
EXCLUDED = ["praise", "other", "unclear"]   # not ranked (Arnav: "do not consider")


@st.cache_data
def load_data():
    reviews = pd.read_csv("data/reviews_classified.csv")
    with open("eval/results_v1.json", encoding="utf-8") as f:
        eval_v1 = json.load(f)
    return reviews, eval_v1


def chart_style(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      barcornerradius=4, bargap=0.35)
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", zeroline=False)
    fig.update_yaxes(showgrid=False)
    return fig


reviews, eval_v1 = load_data()

# ---------------- Header ----------------
st.title("App Review Analyser — Kuku FM & Kuku TV")
st.markdown("**Problem:** teams can't read thousands of app reviews, so common complaints get "
            "missed. This tool sorts every review into a topic with AI and ranks what to fix first.")

app_choice = st.radio("App", ["All apps", "Kuku FM", "Kuku TV"], horizontal=True)
data = reviews if app_choice == "All apps" else reviews[reviews["app"] == app_choice]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Reviews analysed", f"{len(data):,}")
c2.metric("Apps", data["app"].nunique())
c3.metric("% unclear (tool refused to guess)", f"{(data['final_topic'] == 'unclear').mean():.0%}")
c4.metric("AI vs human agreement", f"{eval_v1['overall_agreement']:.0%}",
          help="On 60 reviews hand-labelled blind by Arnav (see 'How we checked the AI').")
st.caption(f"Google Play, newest reviews, {data['date'].min()} to {data['date'].max()}. "
           "Model: claude-haiku-5-5.")

tab_fix, tab_compare, tab_unclear, tab_eval = st.tabs(
    ["What to fix first", "Compare apps", "Unclear", "How we checked the AI"])

# ---------------- What to fix first ----------------
with tab_fix:
    ranking = rank_topics(data, app_choice)
    st.subheader("What to fix first")
    st.caption("Priority score = number of reviews × severity (autopay 3, technical 2, "
               "everything else 1). Praise, other and unclear are not ranked.")

    left, right = st.columns([1.4, 1])
    with left:
        st.dataframe(
            ranking[["rank", "topic", "count", "share_of_all_reviews_pct", "avg_severity",
                     "priority_score"]].rename(columns={
                "share_of_all_reviews_pct": "% of all reviews", "avg_severity": "severity",
                "priority_score": "priority score"}),
            hide_index=True, use_container_width=True)
    with right:
        fig = px.bar(ranking.sort_values("priority_score"), x="priority_score", y="topic",
                     orientation="h", text="priority_score",
                     labels={"priority_score": "Priority score", "topic": ""},
                     hover_data={"count": True, "avg_severity": True})
        fig.update_traces(marker_color=BAR_COLOUR, textposition="outside", cliponaxis=False)
        st.plotly_chart(chart_style(fig, 320), use_container_width=True)

    st.markdown("#### Real reviews behind each topic")
    st.caption("Click a topic to see 5 real reviews. Within a topic severity is the same, "
               "so the reviews most other users agreed with (👍) are shown first.")
    for _, row in ranking.iterrows():
        topic_reviews = (data[data["final_topic"] == row["topic"]]
                         .sort_values(["thumbs_up", "rating", "date"],
                                      ascending=[False, True, False]).head(5))
        with st.expander(f"#{row['rank']}  {row['topic']} — {row['count']} reviews "
                         f"(severity {row['avg_severity']})"):
            for _, r in topic_reviews.iterrows():
                st.markdown(f"**{'★' * int(r['rating'])}{'☆' * (5 - int(r['rating']))}** · "
                            f"{r['app']} · {r['date']} · 👍 {r['thumbs_up']}  \n"
                            f"> {r['text']}  \n"
                            f"<span style='opacity:0.6'>AI reason: {r['ai_reason']}</span>",
                            unsafe_allow_html=True)

# ---------------- Compare apps ----------------
with tab_compare:
    st.subheader("Topic share: Kuku FM vs Kuku TV")
    st.caption("% of each app's reviews that fall into each topic (all topics, including praise "
               "and unclear). The app filter above does not apply here.")
    share = (reviews.groupby("app")["final_topic"].value_counts(normalize=True)
             .mul(100).round(1).rename("pct").reset_index())
    order = (share.groupby("final_topic")["pct"].max().sort_values().index.tolist())
    fig = px.bar(share, x="pct", y="final_topic", color="app", barmode="group",
                 orientation="h", color_discrete_map=APP_COLOURS,
                 category_orders={"final_topic": order[::-1]},
                 labels={"pct": "% of that app's reviews", "final_topic": "", "app": "App"})
    fig = chart_style(fig, 480)
    fig.update_layout(margin=dict(t=40),
                      legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0))
    st.plotly_chart(fig, use_container_width=True)
    table = share.pivot(index="final_topic", columns="app", values="pct").fillna(0)
    table = table.sort_values(table.columns[0], ascending=False)
    st.dataframe(table, use_container_width=True)

# ---------------- Unclear ----------------
with tab_unclear:
    unclear = data[data["final_topic"] == "unclear"]
    st.subheader(f"Reviews the tool refused to guess on ({len(unclear)})")
    st.caption("A review goes here if the AI chose 'unclear' itself, or its confidence was "
               "below 0.6 (Arnav's rule). These are left out of the ranking.")
    by_threshold = (unclear["ai_topic"] != "unclear").sum()
    st.write(f"{len(unclear) - by_threshold} chosen as unclear by the AI · "
             f"{by_threshold} sent here because confidence < 0.6")
    st.dataframe(
        unclear[["app", "rating", "date", "text", "ai_topic", "ai_confidence", "ai_reason"]]
        .rename(columns={"ai_topic": "AI's first guess", "ai_confidence": "confidence"}),
        hide_index=True, use_container_width=True)

# ---------------- How we checked the AI ----------------
with tab_eval:
    st.subheader("How we checked the AI")
    st.markdown(
        "Arnav hand-labelled **60 reviews** (2 apps × 5 star levels × 6) **before** seeing any "
        "AI output. The AI then labelled the same 60, and we compared them.")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Overall agreement", f"{eval_v1['overall_agreement']:.0%}",
              help=f"{round(eval_v1['overall_agreement'] * eval_v1['n_reviews'])}"
                   f"/{eval_v1['n_reviews']} reviews")
    e2.metric("When AI didn't say unclear", f"{eval_v1['agreement_when_ai_not_unclear']:.0%}")
    e3.metric("AI sent to unclear", eval_v1["ai_unclear_total"],
              help=f"Arnav labelled {eval_v1['arnav_unclear_total']} as unclear")
    e4.metric("Classifier failures", eval_v1["classifier_failures"])

    st.markdown("**v1 vs v2:** only v1 was run. Arnav reviewed all 12 disagreements and judged "
                "each one 'I was wrong', so no taxonomy rule needed changing, and he chose to skip "
                "v2. Scored against those corrected labels v1 would be 100%, but only because the "
                "corrections are the AI's own answers, so the honest number is the 80% above. "
                "On the harder reviews (not praise or autopay) agreement was about 62%.")

    st.markdown("#### Per-topic precision and recall")
    st.caption("Precision: when the AI says X, how often Arnav agreed. "
               "Recall: when Arnav said X, how often the AI agreed.")
    st.dataframe(pd.DataFrame(eval_v1["per_topic"]), hide_index=True, use_container_width=True)

    st.markdown("#### Confusion matrix (rows = Arnav, columns = AI)")
    st.dataframe(pd.DataFrame(eval_v1["confusion_matrix"]).fillna(0).astype(int),
                 use_container_width=True)

    st.markdown("#### 3 example disagreements")
    for d in eval_v1["disagreements"][:3]:
        st.markdown(f"> {d['text']}  \n**Arnav:** {d['my_topic']} · **AI:** {d['final_topic']} "
                    f"(confidence {d['ai_confidence']}) · *AI reason:* {d['ai_reason']}")
    st.caption("All 12 disagreements: eval/disagreements_v1.csv · Full write-up: eval/EVAL_REPORT.md")
