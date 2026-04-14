import math
import pandas as pd
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config  # [1](https://github.com/ChrisDelClea/streamlit-agraph)[2](https://pypi.org/project/streamlit-agraph/)

st.set_page_config(page_title="Stakeholder Map", layout="wide")
st.title("Multidimensional Stakeholder Mapping (Force-Directed)")

# ----------------------------
# 1) Example data model
# ----------------------------
# Replace this with your own source (CSV upload, database, MS Graph, etc.)
# Columns:
# - source, target: stakeholder IDs or names
# - freq: contact frequency (integer/float)
# - sentiment: numeric score (e.g., -1..+1) or categorical
example_edges = pd.DataFrame(
    [
        {"source": "Eelco", "target": "Tor", "freq": 18, "sentiment": 0.6},
        {"source": "Eelco", "target": "Aravinda", "freq": 12, "sentiment": 0.2},
        {"source": "Tor", "target": "Aravinda", "freq": 5, "sentiment": -0.3},
        {"source": "Eelco", "target": "Marco", "freq": 8, "sentiment": 0.9},
        {"source": "Marco", "target": "Aravinda", "freq": 3, "sentiment": 0.0},
    ]
)

example_nodes = pd.DataFrame(
    [
        {"id": "Eelco", "label": "Eelco", "group": "ERP", "influence": 0.8},
        {"id": "Tor", "label": "Tor", "group": "Leadership", "influence": 0.9},
        {"id": "Aravinda", "label": "Aravinda", "group": "Service Delivery", "influence": 0.7},
        {"id": "Marco", "label": "Marco", "group": "ERP", "influence": 0.6},
    ]
)

# ----------------------------
# 2) Sidebar controls
# ----------------------------
st.sidebar.header("Controls")
min_freq = st.sidebar.slider("Min frequency (filter edges)", 0, int(example_edges["freq"].max()), 0)
sentiment_mode = st.sidebar.selectbox("Sentiment scale", ["-1..+1", "0..1"], index=0)
edge_scale = st.sidebar.slider("Edge thickness scale", 0.1, 5.0, 1.0, 0.1)
show_labels = st.sidebar.checkbox("Show edge labels (freq)", value=True)

edges_df = example_edges[example_edges["freq"] >= min_freq].copy()

# ----------------------------
# 3) Helper functions
# ----------------------------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def sentiment_to_color(s):
    """
    Map sentiment to color:
    - red for negative, gray for neutral, green for positive
    """
    if sentiment_mode == "-1..+1":
        s = clamp(float(s), -1.0, 1.0)
        # threshold bands
        if s < -0.2:
            return "#E74C3C"  # red
        elif s > 0.2:
            return "#2ECC71"  # green
        else:
            return "#95A5A6"  # gray
    else:
        # 0..1 scale
        s = clamp(float(s), 0.0, 1.0)
        if s < 0.4:
            return "#E74C3C"
        elif s > 0.6:
            return "#2ECC71"
        else:
            return "#95A5A6"

def freq_to_width(freq, fmin, fmax):
    """
    Map frequency to line width with a gentle non-linear scaling.
    """
    if fmax == fmin:
        return 1.0 * edge_scale
    # normalize 0..1
    t = (float(freq) - fmin) / (fmax - fmin)
    # sqrt gives nicer visual distribution
    return (0.5 + 4.5 * math.sqrt(t)) * edge_scale

# ----------------------------
# 4) Build Node + Edge objects
# ----------------------------
# Create nodes
nodes = []
for _, r in example_nodes.iterrows():
    # Node size can represent influence or any other dimension
    size = 10 + 30 * float(r.get("influence", 0.5))
    nodes.append(
        Node(
            id=str(r["id"]),
            label=str(r.get("label", r["id"])),
            size=size,
            group=str(r.get("group", "Default")),  # group drives color in many configs
            title=f"{r.get('label', r['id'])}<br>Group: {r.get('group','-')}<br>Influence: {r.get('influence','-')}"
        )
    )

# Create edges
edges = []
fmin, fmax = float(edges_df["freq"].min()), float(edges_df["freq"].max()) if len(edges_df) else (0.0, 1.0)

for _, r in edges_df.iterrows():
    width = freq_to_width(r["freq"], fmin, fmax)
    color = sentiment_to_color(r["sentiment"])
    label = str(r["freq"]) if show_labels else ""

    # streamlit-agraph Edge supports **kwargs; these are passed to the underlying vis config
    edges.append(
        Edge(
            source=str(r["source"]),
            target=str(r["target"]),
            label=label,
            color=color,
            width=width,
        )
    )

# ----------------------------
# 5) Graph config (force-directed)
# ----------------------------
config = Config(
    width="100%",
    height=750,
    directed=False,
    physics=True,          # enables force-directed layout [1](https://github.com/ChrisDelClea/streamlit-agraph)[2](https://pypi.org/project/streamlit-agraph/)
    hierarchical=False,
    # You can tune more via ConfigBuilder in streamlit-agraph if desired [1](https://github.com/ChrisDelClea/streamlit-agraph)[2](https://pypi.org/project/streamlit-agraph/)
)

# ----------------------------
# 6) Render
# ----------------------------
if len(edges) == 0:
    st.warning("No edges after filtering. Lower the min frequency.")
else:
    st.caption("Edge thickness = frequency of contact; edge color = sentiment.")
    return_value = agraph(nodes=nodes, edges=edges, config=config)
    st.write("Selected / interacted item:", return_value)
