import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import dash_bio
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

def createBarplot(barplot_df):
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

def metaphlanTaxonomy(dataframe, taxonomy_level):
    match taxonomy_level:
        case "Taxonomy Level 1":
            selection = dataframe[dataframe.index.str.contains("k__") & ~dataframe.index.str.contains("p__")]
        case "Taxonomy Level 2":
            selection = dataframe[dataframe.index.str.contains("p__") & ~dataframe.index.str.contains("c__")]
        case "Taxonomy Level 3":
            selection = dataframe[dataframe.index.str.contains("c__") & ~dataframe.index.str.contains("o__")]
        case "Taxonomy Level 4":
            selection = dataframe[dataframe.index.str.contains("o__") & ~dataframe.index.str.contains("f__")]
        case "Taxonomy Level 5":
            selection = dataframe[dataframe.index.str.contains("f__") & ~dataframe.index.str.contains("g__")]
        case "Taxonomy Level 6":
            selection = dataframe[dataframe.index.str.contains("g__") & ~dataframe.index.str.contains("s__")]
        case "Taxonomy Level 7":
            selection = dataframe[dataframe.index.str.contains("s__") & ~dataframe.index.str.contains("t__")]
        case "Taxonomy Level 8":
            selection = dataframe
    
    return selection

def genefamiliesTaxonomy(dataframe, taxonomy_level):
    match taxonomy_level:
        case "Taxonomy Level 1":
            selection = dataframe[dataframe.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED") == False]
        case "Taxonomy Level 2":
            selection = dataframe[dataframe.index.str.contains("g__")]
    
    return selection

def pathabundaceTaxonomy(dataframe, taxonomy_level):
    match taxonomy_level:
        case "Taxonomy Level 1":
            selection = dataframe[dataframe.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED") == False]
    return selection


# Initialize the session state dictionary if not already present
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

# Widget to upload single file
uploaded_files = st.sidebar.file_uploader("Select TSV file to upload", accept_multiple_files=True, type=["tsv"])

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

    st.title("Graph View")
    tab1, tab2 = st.tabs(["Heatmap", "Barplot"])

    with tab1:
        top_menu = st.columns(2)
        with top_menu[0]:
            topN = st.selectbox("Select number of top taxa:",
                            (10, 25, 50, "all"))
        
        df = dataset[dataset.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED")==False]
        df = sort_by_mean_abundance(df)

        if topN == 10:
            topTaxa = df.iloc[:10]
        elif topN == 25:
            topTaxa = df.iloc[:25]
        elif topN == 50:
            topTaxa = df.iloc[:50]
        elif topN == "all":
            topTaxa = df

        
        fig = dash_bio.Clustergram(
            data=topTaxa,
            row_labels=list(range(1, len(topTaxa.index)+1)),
            column_labels=list(topTaxa.columns),
            height=1200,
            color_map="sunset",
        )

        st.plotly_chart(fig, use_container_width=True)

        st.write("### Legend:")
        index_names = topTaxa.index
        ordered_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(index_names)])
        st.markdown(ordered_list)
      
    with tab2:
        
        if "metaphlan" in select_file:

            # Select box for selecting taxonomy level
            taxonomy_level = st.selectbox("Select taxonomy level:", 
                                          options=["Taxonomy Level 1", "Taxonomy Level 2", "Taxonomy Level 3", "Taxonomy Level 4", "Taxonomy Level 5", "Taxonomy Level 6", "Taxonomy Level 7", "Taxonomy Level 8"])
            
            barplot_df = metaphlanTaxonomy(dataset, taxonomy_level)
            

            createBarplot(barplot_df)


        elif "pathabundance" in select_file:
            # Select box for selecting taxonomy level
            taxonomy_level = st.selectbox("Select taxonomy level:", 
                                          options=["Taxonomy Level 1"])
            
            barplot_df = pathabundaceTaxonomy(dataset, taxonomy_level)

            createBarplot(barplot_df)
        
        elif "genefamilies" in select_file:
            
            barplot_menu = st.columns(3)

            with barplot_menu[0]:
                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomy level:", 
                                            options=["Taxonomy Level 1"])
            with barplot_menu[1]:
                select_column = st.selectbox("Select column:", options=dataset.columns)
            
            with barplot_menu[2]:
                n_rows = st.selectbox("Select number of top rows:", options=[10, 25, 50, 100])
            
            barplot_df = genefamiliesTaxonomy(dataset, taxonomy_level)
                        
            barplot_df = barplot_df.loc[:, [select_column]]
            barplot_df = barplot_df.sort_values(by= select_column,ascending=False)
            barplot_df = barplot_df.head(n_rows)
            createBarplot(barplot_df)
        else:
            st.markdown("## Please select different file.")

            
        
else:
    # If no file is loaded display this title
    st.title("Please upload data in the sidebar")