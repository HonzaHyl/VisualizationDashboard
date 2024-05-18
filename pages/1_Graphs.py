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


# Function to create normalized dataset
def normalize_dataset(table):
    for column in table.columns:
        table[column] = (table[column]/table[column].sum())*100
    return table


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

        if "heatmap_dataset" not in st.session_state:
                st.session_state.barplot_dataset = dataset

        st.session_state.barplot_dataset = dataset
        
        if "metaphlan" in select_file:

            # Select box for selecting taxonomy level
            taxonomy_level = st.selectbox("Select taxonomy level:", 
                                          options=["Taxonomy Level 1", "Taxonomy Level 2", "Taxonomy Level 3", "Taxonomy Level 4", "Taxonomy Level 5", "Taxonomy Level 6", "Taxonomy Level 7", "Taxonomy Level 8"])
            
            # Switch statement for selecting taxonomy level and filtering dataframe
            match taxonomy_level:
                case "Taxonomy Level 1":
                    barplot_df = st.session_state.barplot_dataset[st.session_state.barplot_dataset.index.str.contains("k__") & ~st.session_state.barplot_dataset.index.str.contains("p__")]
                case "Taxonomy Level 2":
                    barplot_df = st.session_state.barplot_dataset[st.session_state.barplot_dataset.index.str.contains("k__") & ~st.session_state.barplot_dataset.index.str.contains("c__")]
                case "Taxonomy Level 3":
                    barplot_df = st.session_state.barplot_dataset[st.session_state.barplot_dataset.index.str.contains("k__") & ~st.session_state.barplot_dataset.index.str.contains("o__")]
                case "Taxonomy Level 4":
                    barplot_df = st.session_state.barplot_dataset[st.session_state.barplot_dataset.index.str.contains("k__") & ~st.session_state.barplot_dataset.index.str.contains("f__")]
                case "Taxonomy Level 5":
                    barplot_df = st.session_state.barplot_dataset[st.session_state.barplot_dataset.index.str.contains("k__") & ~st.session_state.barplot_dataset.index.str.contains("g__")]
                case "Taxonomy Level 6":
                    barplot_df = st.session_state.barplot_dataset[st.session_state.barplot_dataset.index.str.contains("k__") & ~st.session_state.barplot_dataset.index.str.contains("s__")]
                case "Taxonomy Level 7":
                    barplot_df = st.session_state.barplot_dataset[st.session_state.barplot_dataset.index.str.contains("k__") & ~st.session_state.barplot_dataset.index.str.contains("t__")]
                case "Taxonomy Level 8":
                    barplot_df = st.session_state.barplot_dataset
            
            # Sort barplot dataframe by index (descending)
            barplot_df = barplot_df.sort_index(ascending=False)

            # Normalize barplot dataframe
            normalized_barplot_df = normalize_dataset(barplot_df)

            # Get index names
            index_names = normalized_barplot_df.index.tolist()

            # Get column names
            column_names = normalized_barplot_df.columns.tolist()

            # Initialize figure
            fig = go.Figure()

            # Add trace for each taxa 
            for index, index_name in enumerate(index_names):
                fig.add_trace(go.Bar(x=column_names, y=normalized_barplot_df.loc[index_name], name=index_name))
    

            fig.update_layout(barmode='stack', 
                                xaxis={'categoryorder':'category ascending', 'type':'category'},
                                autosize=False,
                                height=1000,
                                showlegend=True,
                                legend=dict(
                                    
                                    yanchor="top",
                                    y=5,  # Adjust this value to position the legend lower or higher
                                    xanchor="center",
                                    x=0.5
                                ),
                                margin=dict(b=0)
                            )
            st.plotly_chart(fig, use_container_width=True)