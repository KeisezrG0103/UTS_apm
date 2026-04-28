import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    st.error("Plotly belum terpasang. Jalankan: pip install plotly")
    st.stop()

st.set_page_config(
    page_title="EDA Dataset JSONL",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
DATA_DIR = PROJECT_DIR / "dataset" / "jsonL"
OUTPUT_DIR = APP_DIR / "eda_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILE_IAAA = DATA_DIR / "apm1_iaaa.jsonl"
FILE_TEXTCAT = DATA_DIR / "apm1_iaaa_textcat.jsonl"
FILE_ANNOTATED = DATA_DIR / "db_apm1_genap2526_v2.jsonl"


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 0.75rem 0.9rem;
        box-shadow: 0 2px 18px rgba(15, 23, 42, 0.04);
    }
    .hero {
        padding: 1.15rem 1.25rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #0f172a 0%, #0f766e 100%);
        color: white;
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0;
        font-size: 2rem;
        color: rgba(255, 255, 255, 1);
        line-height: 1.15;
    }
    .hero p {
        margin: 0.45rem 0 0 0;
        color: rgba(255, 255, 255, 1);
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>Exploratory Data Analysis for UTS</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("## Navigasi")
st.sidebar.caption("Gunakan menu ini untuk berpindah antar analisis.")



@st.cache_data(show_spinner=False)
def load_json_any(path_str: str):
    path = Path(path_str)
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        records = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records


def ensure_records(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        return [obj]
    return []


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def df_to_jsonl_bytes(df: pd.DataFrame) -> bytes:
    lines = [json.dumps(row, ensure_ascii=False, default=str) for row in df.to_dict(orient="records")]
    return ("\n".join(lines) + "\n").encode("utf-8")


def get_numeric_categorical_cols(df: pd.DataFrame):
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = [c for c in df.columns if c not in numeric_cols]
    return numeric_cols, categorical_cols


def make_heatmap(df_matrix: pd.DataFrame, title: str, colorscale: str = "Viridis", zmin=None, zmax=None):
    fig = go.Figure(
        data=go.Heatmap(
            z=df_matrix.to_numpy(),
            x=df_matrix.columns.tolist(),
            y=df_matrix.index.tolist(),
            colorscale=colorscale,
            zmin=zmin,
            zmax=zmax,
            hovertemplate="Row=%{y}<br>Col=%{x}<br>Value=%{z}<extra></extra>",
        )
    )
    fig.update_layout(title=title, xaxis_title="", yaxis_title="", height=560)
    return fig


def build_annotation_features(df: pd.DataFrame):
    out = df.copy()

    for col, default in {
        "text": "",
        "tokens": [],
        "spans": [],
        "_annotator_id": "Unknown",
        "_input_hash": "",
        "_task_hash": "",
        "accept": [],
    }.items():
        if col not in out.columns:
            out[col] = default

    out["text"] = out["text"].fillna("").astype(str)
    out["tokens"] = out["tokens"].apply(lambda v: v if isinstance(v, list) else [])
    out["spans"] = out["spans"].apply(lambda v: v if isinstance(v, list) else [])
    out["text_len_char"] = out["text"].str.len()
    out["text_len_word"] = out["text"].str.split().apply(len)
    out["n_tokens"] = out["tokens"].apply(len)
    out["n_spans"] = out["spans"].apply(len)
    out["has_spans"] = out["n_spans"] > 0
    out["annotator_id"] = out["_annotator_id"].fillna("Unknown").astype(str)
    out["input_hash"] = out["_input_hash"].fillna("").astype(str)
    out["task_hash"] = out["_task_hash"].fillna("").astype(str)
    out["span_labels"] = out["spans"].apply(
        lambda spans: [s.get("label") for s in spans if isinstance(s, dict) and s.get("label")]
    )
    out["unique_span_labels"] = out["span_labels"].apply(lambda xs: len(set(xs)))
    out["span_label_text"] = out["span_labels"].apply(lambda xs: ", ".join(sorted(set(xs))) if xs else "No span")
    out["accept_text"] = out["accept"].apply(lambda v: ", ".join(v) if isinstance(v, list) else str(v))
    return out


@st.cache_data(show_spinner=False)
def prepare_data():
    iaaa_obj = load_json_any(str(FILE_IAAA))
    textcat_obj = load_json_any(str(FILE_TEXTCAT))
    annot_obj = load_json_any(str(FILE_ANNOTATED))

    if not isinstance(iaaa_obj, dict):
        raise ValueError("apm1_iaaa.jsonl harus berisi satu objek JSON.")
    if not isinstance(textcat_obj, dict):
        raise ValueError("apm1_iaaa_textcat.jsonl harus berisi satu objek JSON.")

    annot_records = ensure_records(annot_obj)
    df_annot_raw = pd.DataFrame(annot_records)

    iaaa_summary_df = pd.DataFrame([{
        "n_examples": iaaa_obj.get("n_examples"),
        "n_categories": iaaa_obj.get("n_categories"),
        "n_coincident_examples": iaaa_obj.get("n_coincident_examples"),
        "n_single_annotation": iaaa_obj.get("n_single_annotation"),
        "n_annotators": iaaa_obj.get("n_annotators"),
        "avg_raters_per_example": iaaa_obj.get("avg_raters_per_example"),
        "pairwise_f1": iaaa_obj.get("pairwise_f1"),
        "pairwise_recall": iaaa_obj.get("pairwise_recall"),
        "pairwise_precision": iaaa_obj.get("pairwise_precision"),
    }])

    iaaa_metrics_df = (
        pd.DataFrame(iaaa_obj["metrics_per_label"])
        .T.reset_index()
        .rename(columns={"index": "label"})
        [["label", "p", "r", "f1", "support"]]
        .sort_values("support", ascending=False)
        .reset_index(drop=True)
    )

    textcat_rows = []
    for label_name, metrics in textcat_obj.items():
        textcat_rows.append({
            "label_name": label_name,
            "n_examples": metrics.get("n_examples"),
            "n_categories": metrics.get("n_categories"),
            "n_coincident_examples": metrics.get("n_coincident_examples"),
            "n_single_annotation": metrics.get("n_single_annotation"),
            "n_annotators": metrics.get("n_annotators"),
            "avg_raters_per_example": metrics.get("avg_raters_per_example"),
            "percent_agreement": metrics.get("percent_agreement"),
            "kripp_alpha": metrics.get("kripp_alpha"),
            "gwet_ac2": metrics.get("gwet_ac2"),
        })

    df_textcat = pd.DataFrame(textcat_rows).sort_values("label_name").reset_index(drop=True)
    df_textcat["agreement_score"] = (df_textcat["percent_agreement"] + df_textcat["gwet_ac2"]) / 2
    df_textcat["agreement_level"] = np.select(
        [
            (df_textcat["percent_agreement"] >= 0.95) & (df_textcat["gwet_ac2"] >= 0.90),
            (df_textcat["percent_agreement"] >= 0.90) & (df_textcat["gwet_ac2"] >= 0.80),
        ],
        ["High", "Medium"],
        default="Low",
    )

    df_annot = build_annotation_features(df_annot_raw)

    if not df_annot.empty:
        annotator_summary_df = (
            df_annot.groupby("annotator_id", as_index=False)
            .agg(
                n_records=("text", "size"),
                avg_text_len_word=("text_len_word", "mean"),
                avg_text_len_char=("text_len_char", "mean"),
                avg_n_tokens=("n_tokens", "mean"),
                avg_n_spans=("n_spans", "mean"),
                records_with_span=("has_spans", "sum"),
                unique_input_hash=("input_hash", "nunique"),
            )
        )
        annotator_summary_df["pct_with_span"] = annotator_summary_df["records_with_span"] / annotator_summary_df["n_records"]

        span_labels_flat = [label for labels in df_annot["span_labels"] for label in labels]
        span_label_df = (
            pd.Series(span_labels_flat)
            .value_counts()
            .rename_axis("span_label")
            .reset_index(name="count")
        )

        combo_df = (
            df_annot.loc[df_annot["n_spans"] > 0, "span_label_text"]
            .value_counts()
            .rename_axis("span_label_combo")
            .reset_index(name="count")
            .head(20)
        )
    else:
        annotator_summary_df = pd.DataFrame(columns=[
            "annotator_id", "n_records", "avg_text_len_word", "avg_text_len_char",
            "avg_n_tokens", "avg_n_spans", "records_with_span", "unique_input_hash", "pct_with_span"
        ])
        span_label_df = pd.DataFrame(columns=["span_label", "count"])
        combo_df = pd.DataFrame(columns=["span_label_combo", "count"])

    overview_df = pd.DataFrame([
        {
            "dataset": "apm1_iaaa",
            "rows_or_examples": iaaa_summary_df.loc[0, "n_examples"],
            "main_quality_metric": "pairwise_f1",
            "metric_value": iaaa_summary_df.loc[0, "pairwise_f1"],
        },
        {
            "dataset": "apm1_iaaa_textcat",
            "rows_or_examples": len(df_textcat),
            "main_quality_metric": "mean percent_agreement",
            "metric_value": float(df_textcat["percent_agreement"].mean()),
        },
        {
            "dataset": "db_apm1_genap2526_v2",
            "rows_or_examples": int(len(df_annot)),
            "main_quality_metric": "avg_n_spans",
            "metric_value": float(df_annot["n_spans"].mean()) if not df_annot.empty else np.nan,
        },
    ])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    iaaa_summary_df.to_csv(OUTPUT_DIR / "apm1_iaaa_summary.csv", index=False)
    iaaa_metrics_df.to_csv(OUTPUT_DIR / "apm1_iaaa_metrics_per_label.csv", index=False)
    df_textcat.to_csv(OUTPUT_DIR / "apm1_iaaa_textcat_agreement_metrics.csv", index=False)
    annotator_summary_df.to_csv(OUTPUT_DIR / "db_apm1_annotator_summary.csv", index=False)
    span_label_df.to_csv(OUTPUT_DIR / "db_apm1_span_label_distribution.csv", index=False)
    combo_df.to_csv(OUTPUT_DIR / "db_apm1_top_span_combinations.csv", index=False)
    overview_df.to_csv(OUTPUT_DIR / "overview_summary.csv", index=False)

    return (
        iaaa_obj,
        iaaa_summary_df,
        iaaa_metrics_df,
        textcat_obj,
        df_textcat,
        df_annot,
        annotator_summary_df,
        span_label_df,
        combo_df,
        overview_df,
    )


iaaa_obj, iaaa_summary_df, iaaa_metrics_df, textcat_obj, df_textcat, df_annot, annotator_summary_df, span_label_df, combo_df, overview_df = prepare_data()

st.sidebar.markdown("## Menu")
page = st.sidebar.radio(
    "Pilih bagian",
    [
        "Overview",
        "apm1_iaaa",
        "apm1_iaaa_textcat",
        "db_apm1_genap2526_v2",
        "Flexible explorer",
    ],
)




def render_overview():
    st.subheader("Ringkasan Semua Dataset")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("apm1_iaaa examples", f"{int(iaaa_summary_df.loc[0, 'n_examples']):,}")
    c2.metric("IAAA pairwise F1", f"{iaaa_summary_df.loc[0, 'pairwise_f1']:.2f}")
    c3.metric("Textcat label groups", f"{len(df_textcat)}")
    c4.metric("Annotated records", f"{len(df_annot):,}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Unique annotators", f"{df_annot['annotator_id'].nunique():,}" if not df_annot.empty else "0")
    c6.metric("Avg text words", f"{df_annot['text_len_word'].mean():.2f}" if not df_annot.empty else "0")
    c7.metric("Avg tokens", f"{df_annot['n_tokens'].mean():.2f}" if not df_annot.empty else "0")
    c8.metric("Avg spans", f"{df_annot['n_spans'].mean():.2f}" if not df_annot.empty else "0")

    st.markdown("### Tabel Ringkasan")
    st.dataframe(overview_df, use_container_width=True)

    left, right = st.columns([1.15, 0.85])
    with left:
        st.markdown("### Agreement Score per Label Group")
        fig = px.bar(
            df_textcat,
            x="label_name",
            y="agreement_score",
            color="agreement_level",
            color_discrete_map={"High": "#0f766e", "Medium": "#d97706", "Low": "#dc2626"},
            title="Agreement score per label group",
        )
        fig.update_layout(xaxis_title="Label Group", yaxis_title="Agreement Score", template="plotly_white", height=480)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("### Cleaning Hint")
        high_count = int((df_textcat["agreement_level"] == "High").sum())
        medium_count = int((df_textcat["agreement_level"] == "Medium").sum())
        low_count = int((df_textcat["agreement_level"] == "Low").sum())
        st.metric("High-confidence labels", high_count)
        st.metric("Medium-confidence labels", medium_count)
        st.metric("Low-confidence labels", low_count)
        st.caption("Label dengan agreement tinggi lebih aman dipakai untuk dataset bersih. Label rendah sebaiknya direview atau dibuang.")

    # st.markdown("### Download Ringkasan")
    # col_a, col_b, col_c = st.columns(3)
    # col_a.download_button(
    #     "Unduh overview.csv",
    #     data=df_to_csv_bytes(overview_df),
    #     file_name="overview_summary.csv",
    #     mime="text/csv",
    #     use_container_width=True,
    # )
    # col_b.download_button(
    #     "Unduh textcat agreement.csv",
    #     data=df_to_csv_bytes(df_textcat),
    #     file_name="apm1_iaaa_textcat_agreement_metrics.csv",
    #     mime="text/csv",
    #     use_container_width=True,
    # )
    # col_c.download_button(
    #     "Unduh IAAA metrics.csv",
    #     data=df_to_csv_bytes(iaaa_metrics_df),
    #     file_name="apm1_iaaa_metrics_per_label.csv",
    #     mime="text/csv",
    #     use_container_width=True,
    # )


def render_iaaa():
    st.subheader("EDA: apm1_iaaa.jsonl")

    c1, c2, c3 = st.columns(3)
    c1.metric("n_examples", f"{int(iaaa_summary_df.loc[0, 'n_examples']):,}")
    c2.metric("pairwise_precision", f"{iaaa_summary_df.loc[0, 'pairwise_precision']:.2f}")
    c3.metric("pairwise_recall", f"{iaaa_summary_df.loc[0, 'pairwise_recall']:.2f}")

    st.dataframe(iaaa_summary_df, use_container_width=True)
    st.dataframe(iaaa_metrics_df, use_container_width=True)

    top_label = iaaa_metrics_df.loc[iaaa_metrics_df["f1"].idxmax()]
    low_label = iaaa_metrics_df.loc[iaaa_metrics_df["f1"].idxmin()]
    st.info(
        f"Label dengan F1 tertinggi: {top_label['label']} ({top_label['f1']:.3f}). "
        f"Label dengan F1 terendah: {low_label['label']} ({low_label['f1']:.3f})."
    )

    st.markdown("### Confusion Matrix")
    heatmap_mode = st.radio("Tampilan", ["Counts", "Normalized"], horizontal=True)
    labels = iaaa_metrics_df["label"].tolist() + ["Other"]
    matrix = np.array(iaaa_obj["confusion_matrix"]) if heatmap_mode == "Counts" else np.array(iaaa_obj["normalized_confusion_matrix"])
    matrix_df = pd.DataFrame(matrix, index=labels, columns=labels)

    zmin, zmax = (None, None)
    if heatmap_mode == "Normalized":
        zmin, zmax = 0, 1

    fig = make_heatmap(
        matrix_df,
        title=f"apm1_iaaa - {heatmap_mode} Confusion Matrix",
        colorscale="Blues" if heatmap_mode == "Counts" else "Viridis",
        zmin=zmin,
        zmax=zmax,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Precision / Recall / F1")
    melted = iaaa_metrics_df.melt(id_vars="label", value_vars=["p", "r", "f1"], var_name="metric", value_name="score")
    fig = px.bar(
        melted,
        x="label",
        y="score",
        color="metric",
        barmode="group",
        title="Precision / Recall / F1 per label",
    )
    fig.update_layout(yaxis_range=[0, 1], template="plotly_white", height=480)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Support")
    fig = px.bar(
        iaaa_metrics_df,
        x="label",
        y="support",
        title="Support per label",
        color="support",
        color_continuous_scale="Teal",
    )
    fig.update_layout(template="plotly_white", height=420)
    st.plotly_chart(fig, use_container_width=True)

    # st.download_button(
    #     "Unduh IAAA label metrics CSV",
    #     data=df_to_csv_bytes(iaaa_metrics_df),
    #     file_name="apm1_iaaa_metrics_per_label.csv",
    #     mime="text/csv",
    # )


def render_textcat():
    st.subheader("EDA: apm1_iaaa_textcat.jsonl")

    c1, c2, c3 = st.columns(3)
    c1.metric("Label groups", f"{len(df_textcat)}")
    c2.metric("Mean percent agreement", f"{df_textcat['percent_agreement'].mean():.3f}")
    c3.metric("Mean Gwet AC2", f"{df_textcat['gwet_ac2'].mean():.3f}")

    st.dataframe(df_textcat, use_container_width=True)

    left, right = st.columns([1.15, 0.85])
    with left:
        st.markdown("### Agreement Metrics")
        melted = df_textcat.melt(
            id_vars="label_name",
            value_vars=["percent_agreement", "kripp_alpha", "gwet_ac2"],
            var_name="metric",
            value_name="value",
        )
        fig = px.bar(
            melted,
            x="label_name",
            y="value",
            color="metric",
            barmode="group",
            title="Agreement metrics per label group",
        )
        fig.update_layout(template="plotly_white", height=500)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### Agreement Level")
        level_counts = df_textcat["agreement_level"].value_counts().reset_index()
        level_counts.columns = ["agreement_level", "count"]
        fig = px.bar(
            level_counts,
            x="agreement_level",
            y="count",
            color="agreement_level",
            color_discrete_map={"High": "#0f766e", "Medium": "#d97706", "Low": "#dc2626"},
            title="Agreement level counts",
        )
        fig.update_layout(showlegend=False, template="plotly_white", height=500)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Heatmap Agreement")
    heat_df = df_textcat.set_index("label_name")[["percent_agreement", "kripp_alpha", "gwet_ac2"]]
    fig = make_heatmap(
        heat_df,
        title="apm1_iaaa_textcat - Agreement heatmap",
        colorscale="Viridis",
        zmin=0,
        zmax=1,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Rekomendasi Agreement-Based Cleaning")
    with st.expander("Atur threshold dan lihat label yang aman dipakai", expanded=True):
        pa_thr = st.slider("Minimal percent agreement", 0.0, 1.0, 0.90, 0.01)
        gwet_thr = st.slider("Minimal Gwet AC2", 0.0, 1.0, 0.80, 0.01)

        recommended = df_textcat[
            (df_textcat["percent_agreement"] >= pa_thr) &
            (df_textcat["gwet_ac2"] >= gwet_thr)
        ].copy()

        st.write(f"Label yang lolos threshold: {len(recommended)}")
        st.dataframe(recommended, use_container_width=True)

        # st.download_button(
        #     "Unduh label terpilih CSV",
        #     data=df_to_csv_bytes(recommended),
        #     file_name="apm1_iaaa_textcat_recommended_labels.csv",
        #     mime="text/csv",
        # )

    # st.caption("Catatan: Kripp alpha dapat lebih rendah dari pada label yang sangat tidak seimbang. Gunakan bersama percent agreement dan Gwet AC2.")


def render_records():
    st.subheader("EDA: db_apm1_genap2526_v2.jsonl")

    if df_annot.empty:
        st.warning("Dataset kosong atau gagal dibaca.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{len(df_annot):,}")
    c2.metric("Unique annotators", f"{df_annot['annotator_id'].nunique():,}")
    c3.metric("Records with span", f"{int(df_annot['has_spans'].sum()):,}")
    c4.metric("Avg spans / record", f"{df_annot['n_spans'].mean():.2f}")

    st.dataframe(
        df_annot[[
            "text",
            "annotator_id",
            "text_len_word",
            "n_tokens",
            "n_spans",
            "span_label_text",
            "accept_text",
        ]].head(30),
        use_container_width=True,
    )

    st.markdown("### Filter Record")
    search = st.text_input("Cari kata di text")
    annotator_filter = st.multiselect(
        "Filter annotator",
        options=sorted(df_annot["annotator_id"].unique().tolist()),
    )
    span_filter = st.multiselect(
        "Filter span label",
        options=span_label_df["span_label"].tolist() if not span_label_df.empty else [],
    )
    only_spans = st.checkbox("Hanya record yang punya span", value=False)

    min_words = int(df_annot["text_len_word"].min())
    max_words = int(df_annot["text_len_word"].max())
    word_range = st.slider("Range jumlah kata", min_words, max_words, (min_words, max_words))

    sample_limit = st.slider("Jumlah baris yang ditampilkan", 5, max(5, min(500, len(df_annot))), min(50, len(df_annot)))

    filtered = df_annot.copy()

    if search.strip():
        filtered = filtered[filtered["text"].str.contains(search, case=False, na=False)]

    if annotator_filter:
        filtered = filtered[filtered["annotator_id"].isin(annotator_filter)]

    if span_filter:
        selected = set(span_filter)
        filtered = filtered[filtered["span_labels"].apply(lambda labels: bool(selected.intersection(labels)))]

    if only_spans:
        filtered = filtered[filtered["has_spans"]]

    filtered = filtered[filtered["text_len_word"].between(word_range[0], word_range[1])]

    filtered_display = filtered.reset_index(drop=False).rename(columns={"index": "source_row"})

    c5, c6, c7 = st.columns(3)
    c5.metric("Filtered rows", f"{len(filtered_display):,}")
    c6.metric("Unique annotators (filtered)", f"{filtered_display['annotator_id'].nunique():,}" if not filtered_display.empty else "0")
    c7.metric("Mean spans (filtered)", f"{filtered_display['n_spans'].mean():.2f}" if not filtered_display.empty else "0")

    left, right, extra = st.columns(3)
    with left:
        fig = px.histogram(filtered_display, x="text_len_word", nbins=30, title="Distribusi panjang teks (kata)")
        fig.update_layout(template="plotly_white", height=420)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.histogram(filtered_display, x="n_tokens", nbins=30, title="Distribusi jumlah token")
        fig.update_layout(template="plotly_white", height=420)
        st.plotly_chart(fig, use_container_width=True)
    with extra:
        fig = px.histogram(filtered_display, x="n_spans", nbins=30, title="Distribusi jumlah span")
        fig.update_layout(template="plotly_white", height=420)
        st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        filtered_span_counts = pd.Series([label for labels in filtered["span_labels"] for label in labels]).value_counts().reset_index()
        filtered_span_counts.columns = ["span_label", "count"]
        st.markdown("### Distribusi span label (filtered)")
        st.dataframe(filtered_span_counts.head(20), use_container_width=True)
        if not filtered_span_counts.empty:
            fig = px.bar(filtered_span_counts.head(20), x="span_label", y="count", title="Top span labels")
            fig.update_layout(template="plotly_white", height=420)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        filtered_combo = (
            filtered.loc[filtered["n_spans"] > 0, "span_label_text"]
            .value_counts()
            .rename_axis("span_label_combo")
            .reset_index(name="count")
            .head(20)
        )
        st.markdown("### Top kombinasi span label")
        st.dataframe(filtered_combo, use_container_width=True)
        if not filtered_combo.empty:
            fig = px.bar(filtered_combo.sort_values("count"), x="count", y="span_label_combo", orientation="h", title="Top label combinations")
            fig.update_layout(template="plotly_white", height=500)
            st.plotly_chart(fig, use_container_width=True)

    # st.markdown("### Export Data Terfilter")
    # d1, d2 = st.columns(2)
    # d1.download_button(
    #     "Unduh CSV",
    #     data=df_to_csv_bytes(filtered_display),
    #     file_name="db_apm1_genap2526_v2_filtered.csv",
    #     mime="text/csv",
    #     use_container_width=True,
    # )
    # d2.download_button(
    #     "Unduh JSONL",
    #     data=df_to_jsonl_bytes(filtered_display.drop(columns=["source_row"])),
    #     file_name="db_apm1_genap2526_v2_filtered.jsonl",
    #     mime="application/json",
    #     use_container_width=True,
    # )

    st.markdown("### Inspeksi Satu Record")
    if filtered_display.empty:
        st.warning("Tidak ada data setelah filter.")
        return

    row_pos = st.number_input(
        "Pilih nomor baris hasil filter",
        min_value=0,
        max_value=max(0, len(filtered_display) - 1),
        value=0,
        step=1,
    )
    row = filtered_display.iloc[int(row_pos)]

    info_left, info_right = st.columns([1.05, 0.95])
    with info_left:
        st.write("Text")
        st.write(row["text"])
        st.write(
            {
                "source_row": int(row["source_row"]),
                "annotator_id": row["annotator_id"],
                "input_hash": row["input_hash"],
                "task_hash": row["task_hash"],
                "text_len_word": int(row["text_len_word"]),
                "n_tokens": int(row["n_tokens"]),
                "n_spans": int(row["n_spans"]),
                "span_label_text": row["span_label_text"],
            }
        )
        with st.expander("Raw JSON row", expanded=False):
            st.json(json.loads(json.dumps(row.to_dict(), default=str)))

    with info_right:
        tokens = row["tokens"] if isinstance(row["tokens"], list) else []
        spans = row["spans"] if isinstance(row["spans"], list) else []

        st.write("Tokens")
        st.dataframe(pd.DataFrame(tokens), use_container_width=True)

        st.write("Spans")
        st.dataframe(pd.DataFrame(spans), use_container_width=True)


def render_flexible_explorer():
    st.subheader("Flexible 2D / 3D Explorer")

    explorer_sources = {
        "IAAA label metrics": iaaa_metrics_df,
        "IAAA summary": iaaa_summary_df,
        "Textcat agreement": df_textcat,
        "Annotated records": df_annot,
        "Annotator summary": annotator_summary_df,
    }

    source_name = st.selectbox("Pilih dataset sumber", list(explorer_sources.keys()))
    df = explorer_sources[source_name].copy()

    if df.empty:
        st.warning("Dataset yang dipilih kosong.")
        return

    st.dataframe(df.head(20), use_container_width=True)

    numeric_cols, categorical_cols = get_numeric_categorical_cols(df)
    st.caption(
        f"{len(df)} baris | {len(numeric_cols)} kolom numerik | {len(categorical_cols)} kolom kategorikal"
    )

    if len(numeric_cols) < 2:
        st.warning("Dataset ini belum punya cukup kolom numerik untuk scatter 2D/3D.")
        return

    max_points = st.slider("Maksimum titik yang diplot", 10, max(50, len(df)), min(500, max(50, len(df))))
    plot_df = df.sample(n=min(max_points, len(df)), random_state=42) if len(df) > max_points else df.copy()

    tab2d, tab3d, tabdist = st.tabs(["2D Scatter", "3D Scatter", "Distribusi"])

    with tab2d:
        col1, col2, col3 = st.columns(3)
        x_col = col1.selectbox("X", numeric_cols, index=0, key=f"{source_name}_2d_x")
        y_default = 1 if len(numeric_cols) > 1 else 0
        y_col = col2.selectbox("Y", numeric_cols, index=y_default, key=f"{source_name}_2d_y")
        color_col = col3.selectbox("Color", ["(none)"] + df.columns.tolist(), key=f"{source_name}_2d_color")

        hover_cols = st.multiselect(
            "Hover data",
            options=df.columns.tolist(),
            default=[c for c in df.columns.tolist() if c not in {x_col, y_col}][:3],
            key=f"{source_name}_2d_hover",
        )

        size_options = ["(none)"] + numeric_cols
        size_col = st.selectbox("Size", size_options, index=0, key=f"{source_name}_2d_size")

        plot_subset = plot_df.dropna(subset=[x_col, y_col]).copy()
        if plot_subset.empty:
            st.warning("Tidak ada baris valid untuk kombinasi X dan Y yang dipilih.")
        else:
            fig = px.scatter(
                plot_subset,
                x=x_col,
                y=y_col,
                color=None if color_col == "(none)" else color_col,
                size=None if size_col == "(none)" else size_col,
                hover_data=hover_cols,
                title=f"2D Scatter: {x_col} vs {y_col}",
            )
            fig.update_layout(template="plotly_white", height=620)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(plot_subset[[x_col, y_col] + ([size_col] if size_col != "(none)" else [])].describe(), use_container_width=True)

    with tab3d:
        col1, col2, col3 = st.columns(3)
        x3 = col1.selectbox("X", numeric_cols, index=0, key=f"{source_name}_3d_x")
        y3_default = 1 if len(numeric_cols) > 1 else 0
        y3 = col2.selectbox("Y", numeric_cols, index=y3_default, key=f"{source_name}_3d_y")
        z3_default = 2 if len(numeric_cols) > 2 else y3_default
        z3 = col3.selectbox("Z", numeric_cols, index=z3_default, key=f"{source_name}_3d_z")

        color3 = st.selectbox("Color", ["(none)"] + df.columns.tolist(), key=f"{source_name}_3d_color")
        size3 = st.selectbox("Size", ["(none)"] + numeric_cols, index=0, key=f"{source_name}_3d_size")
        hover3 = st.multiselect(
            "Hover data",
            options=df.columns.tolist(),
            default=[c for c in df.columns.tolist() if c not in {x3, y3, z3}][:3],
            key=f"{source_name}_3d_hover",
        )

        plot_subset_3d = plot_df.dropna(subset=[x3, y3, z3]).copy()
        if plot_subset_3d.empty:
            st.warning("Tidak ada baris valid untuk kombinasi X, Y, dan Z yang dipilih.")
        else:
            fig = px.scatter_3d(
                plot_subset_3d,
                x=x3,
                y=y3,
                z=z3,
                color=None if color3 == "(none)" else color3,
                size=None if size3 == "(none)" else size3,
                hover_data=hover3,
                title=f"3D Scatter: {x3}, {y3}, {z3}",
            )
            fig.update_layout(template="plotly_white", height=700)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(plot_subset_3d[[x3, y3, z3] + ([size3] if size3 != "(none)" else [])].describe(), use_container_width=True)

    with tabdist:
        dist_col = st.selectbox("Kolom numerik", numeric_cols, index=0, key=f"{source_name}_dist_col")
        group_col = st.selectbox("Group by (opsional)", ["(none)"] + df.columns.tolist(), key=f"{source_name}_dist_group")
        dist_mode = st.radio("Tipe distribusi", ["Histogram", "Box"], horizontal=True, key=f"{source_name}_dist_mode")

        plot_subset = plot_df.dropna(subset=[dist_col]).copy()
        if plot_subset.empty:
            st.warning("Tidak ada data untuk distribusi kolom yang dipilih.")
        else:
            if dist_mode == "Histogram":
                fig = px.histogram(
                    plot_subset,
                    x=dist_col,
                    color=None if group_col == "(none)" else group_col,
                    nbins=30,
                    title=f"Histogram: {dist_col}",
                )
            else:
                fig = px.box(
                    plot_subset,
                    x=None if group_col == "(none)" else group_col,
                    y=dist_col,
                    color=None if group_col == "(none)" else group_col,
                    title=f"Box plot: {dist_col}",
                )
            fig.update_layout(template="plotly_white", height=540)
            st.plotly_chart(fig, use_container_width=True)


if page == "Overview":
    render_overview()
elif page == "apm1_iaaa":
    render_iaaa()
elif page == "apm1_iaaa_textcat":
    render_textcat()
elif page == "db_apm1_genap2526_v2":
    render_records()
else:
    render_flexible_explorer()
