import streamlit as st
import pandas as pd
import numpy as np

import plotly.graph_objects as go
from io import BytesIO

# Allow the content to be spread across the whole page
st.set_page_config(layout="wide")

# Function for loading data from .tsv file
@st.cache_data(show_spinner=False)
def load_data(file, file_name):
    if "metaphlan" in file_name:
        dataset = pd.read_csv(BytesIO(file), sep="\t", index_col=0, skiprows=1)
        dataset.index.name = "Taxas"
    else:
        dataset = pd.read_csv(BytesIO(file), sep="\t", index_col=0)
    return dataset

# Function to sort dataset by Mean Abundance 
def sort_by_mean_abundance(dataframe):
    dataframe = dataframe.assign(Mean_Abundance=dataframe.mean(axis=1))
    dataframe = dataframe.sort_values("Mean_Abundance", ascending=False)
    dataframe = dataframe.drop(columns="Mean_Abundance")
    return dataframe

# Initialize the session state dictionary if not already present
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

# Widget to upload single file
uploaded_files = st.sidebar.file_uploader("Select TSV file to upload", accept_multiple_files=True)

# Upload multiple files and save the to dictionary
if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in st.session_state.uploaded_files:
            st.session_state.uploaded_files[uploaded_file.name] = uploaded_file.getvalue()
    
    
# Files are uploaded and one file is selected
if st.session_state.uploaded_files:
    file_names = list(st.session_state.uploaded_files.keys())
    with st.sidebar:
        select_file = st.selectbox("Select file:", options=file_names)


    file = st.session_state.uploaded_files[select_file]
    dataset = load_data(file, select_file)

    if "heatmap_dataset" not in st.session_state:
        st.session_state.heatmap_dataset = dataset

    st.session_state.heatmap_dataset = dataset

    st.title("Graph View")
    tab1, tab2 = st.tabs(["Heatmap", "Barplot"])

    with tab1:
        top_menu = st.columns(2)
        with top_menu[0]:
            topN = st.selectbox("Select number of top taxa:",
                            (10, 25, 50, "all"))
        
        df = st.session_state.heatmap_dataset[st.session_state.heatmap_dataset.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED")==False]
        df = sort_by_mean_abundance(df)


        if topN == 10:
            topTaxa = df.iloc[:10]
        elif topN == 25:
            topTaxa = df.iloc[:25]
        elif topN == 50:
            topTaxa = df.iloc[:50]
        elif topN == "all":
            topTaxa = df

        fig = go.Figure(data=go.Heatmap(
        z = topTaxa.values.tolist()[::-1],
        x = topTaxa.columns,
        y = list(topTaxa.index)[::-1],
        colorscale="hot_r",
        hoverongaps = False,
        ))

        fig.layout.autosize = False
        fig.layout.height = 1200
        fig.layout.margin = dict(b=200, l=50, r=50)

        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        pass