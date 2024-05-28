# Import libraries
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
    """Converts loaded file from bytes format to  Pandas DataFrame. 

    Args:
        file (bytes): Loaded file from file_uploader 
        file_name (str): Name of uploaded file

    Returns:
        DataFrame: Loaded file in the form of DataFrame
    """
    if "metaphlan" in file_name:
        dataset = pd.read_csv(BytesIO(file), sep="\t", index_col=0, skiprows=1)
        dataset.index.name = "Taxa"
    else:
        dataset = pd.read_csv(BytesIO(file), sep="\t", index_col=0)
    return dataset


# Function to create normalized dataset
def normalize_dataset(table):
    """Whole input table is normalized to percentage by columns.

    Args:
        table (DataFrame): Whole uploaded table (file)

    Returns:
        DataFrame: Normalized table
    """
    for column in table.columns:
        table[column] = (table[column]/table[column].sum())*100
    return table


# Function to sort dataset by Mean Abundance 
def sort_by_mean_abundance(dataframe):
    """Takes whole DataFrame, adds column with mean abundance per row. Sorts DataFrame by this column.
    Drops the mean abundance column.

    Args:
        dataframe (DataFrame): Selected DataFrame

    Returns:
        DataFrame: Sorted DataFrames by mean abundance 
    """
    dataframe = dataframe.assign(Mean_Abundance=dataframe.mean(axis=1))
    dataframe = dataframe.sort_values("Mean_Abundance", ascending=False)
    dataframe = dataframe.drop(columns="Mean_Abundance")
    return dataframe

def createBarplot(barplot_df, y_title):
    """Function that creates stacked barplot and prints it on the page.

    Args:
        barplot_df (DataFrame): Selected DataFrame to create barplots 
        y_title (str): Label for y axis 
    """
    # Sort barplot dataframe by index (descending)
    barplot_df = barplot_df.sort_index(ascending=False)

    

    # Get index names
    index_names = barplot_df.index.tolist()

    # Get column names
    column_names = barplot_df.columns.tolist()

    # Initialize figure
    fig = go.Figure()

    # Add trace for each taxa 
    for index, index_name in enumerate(index_names):
        fig.add_trace(go.Bar(x=column_names, y=barplot_df.loc[index_name], name=index_name))
    

    fig.update_layout(barmode='stack', 
                        xaxis={'categoryorder':'category ascending', 'type':'category'},
                        autosize=False,
                        height=1000,
                        showlegend=True,
                        yaxis=dict(title=y_title),
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
    """Function selects rows based on taxonomic level.

    Args:
        dataframe (DataFrame): Whole table (file)
        taxonomy_level (str): Selected taxonomic level

    Returns:
        DataFrame: DataFrame with only rows on selected taxonomic level.
    """
    match taxonomy_level:
        case "Taxonomic Level 1 (Kingdom)":
            selection = dataframe[dataframe.index.str.contains("k__") & ~dataframe.index.str.contains("p__")]
        case "Taxonomic Level 2 (Phylum)":
            selection = dataframe[dataframe.index.str.contains("p__") & ~dataframe.index.str.contains("c__")]
        case "Taxonomic Level 3 (Class)":
            selection = dataframe[dataframe.index.str.contains("c__") & ~dataframe.index.str.contains("o__")]
        case "Taxonomic Level 4 (Order)":
            selection = dataframe[dataframe.index.str.contains("o__") & ~dataframe.index.str.contains("f__")]
        case "Taxonomic Level 5 (Family)":
            selection = dataframe[dataframe.index.str.contains("f__") & ~dataframe.index.str.contains("g__")]
        case "Taxonomic Level 6 (Genus)":
            selection = dataframe[dataframe.index.str.contains("g__") & ~dataframe.index.str.contains("s__")]
        case "Taxonomic Level 7 (Species)":
            selection = dataframe[dataframe.index.str.contains("s__") & ~dataframe.index.str.contains("t__")]
        case "Taxonomic Level 8 (All)":
            selection = dataframe
    
    return selection

def genefamiliesTaxonomy(dataframe, taxonomy_level):
    """Function selects rows based on taxonomic level.

    Args:
        dataframe (DataFrame): Whole table (file)
        taxonomy_level (str): Selected taxonomic level

    Returns:
        DataFrame: DataFrame with only rows on selected taxonomic level.
    """
    match taxonomy_level:
        case "Taxonomic Level 1":
            selection = dataframe[dataframe.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED") == False]
        case "Taxonomic Level 2 (Genus & Species)":
            selection = dataframe[dataframe.index.str.contains("g__")]
    
    return selection

def pathabundaceTaxonomy(dataframe, taxonomy_level):
    """Function selects rows based on taxonomic level.

    Args:
        dataframe (DataFrame): Whole table (file)
        taxonomy_level (str): Selected taxonomic level

    Returns:
        DataFrame: DataFrame with only rows on selected taxonomic level.
    """
    match taxonomy_level:
        case "Taxonomic Level 1":
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

    st.title("Graphs")

    # Create tabs for heatmap and barplots 
    tab1, tab2 = st.tabs(["Heatmap", "Barplots"])

    #################################### Heatmap ####################################
    with tab1:
        # Condition to exclude pathcoverage 
        if "pathcoverage" not in select_file:
            # Columns for buttons
            top_menu = st.columns(2)
            # Button to select number of top taxa
            with top_menu[0]:
                topN = st.selectbox("Select number of top taxa:",
                                (10, 25, 50, "all"), help="Number of top taxa from ordered descending mean abundance (per row) column.")
            # Button to select distance metric
            with top_menu[1]:
                metrics = st.selectbox("Select distance metric for clustering:", options=["Euclidean", "Correlation", "Jaccard"], 
                                    help="Distance metric for calculating the dendrograms and distance between features.")
            
            # Drop all unwanted rows in DataFrame
            df = dataset[dataset.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED")==False]
            # Sort table by mean abundance 
            df = sort_by_mean_abundance(df)

            # Take only given number of taxa
            if topN == 10:
                topTaxa = df.iloc[:10]
            elif topN == 25:
                topTaxa = df.iloc[:25]
            elif topN == 50:
                topTaxa = df.iloc[:50]
            elif topN == "all":
                topTaxa = df
            
            
            # Create figure for the heatmap (clustergram)
            fig = dash_bio.Clustergram(
                data=topTaxa,
                row_labels=list(range(1, len(topTaxa.index)+1)),
                column_labels=list(topTaxa.columns),
                height=1200,
                color_map="sunset",
                row_dist=metrics.lower(),
                col_dist=metrics.lower()

            )
            
            # Plot the figure
            st.plotly_chart(fig, use_container_width=True)

            # Create legend for the heatmap (clustergram)
            st.write("### Legend:")
            index_names = topTaxa.index
            ordered_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(index_names)])
            st.markdown(ordered_list)
        else:
            st.markdown("## Please select different file.")
    
    #################################### Barplots ####################################
    with tab2:
        
        if "metaphlan" in select_file:

            # Select box for selecting taxonomy level
            taxonomy_level = st.selectbox("Select taxonomic level:", 
                                          options=["Taxonomic Level 1 (Kingdom)", "Taxonomic Level 2 (Phylum)", "Taxonomic Level 3 (Class)", "Taxonomic Level 4 (Order)", "Taxonomic Level 5 (Family)", "Taxonomic Level 6 (Genus)", "Taxonomic Level 7 (Species)"],
                                          help="Show barplot for specific taxonomic level.")
            
            # Include only rows with selected taxonomic level
            barplot_df = metaphlanTaxonomy(dataset, taxonomy_level)
            
            # Create and show barplot
            createBarplot(barplot_df, "Relativní abundance [%]")


        elif "pathabundance" in select_file:
            # Select box for selecting taxonomy level
            taxonomy_level = st.selectbox("Select taxonomic level:", 
                                          options=["Taxonomic Level 1"],
                                          help="Show barplot for specific taxonomic level.")
            
            # Include only rows with selected taxonomic level
            barplot_df = pathabundaceTaxonomy(dataset, taxonomy_level)

            # Normalize selected dataset
            normalized_dataset = normalize_dataset(barplot_df)

            # Create and show barplot
            createBarplot(normalized_dataset, "Relativní abundance [%]")
        
        elif "genefamilies" in select_file:
            
            # Columns for buttons
            barplot_menu = st.columns(3)

            with barplot_menu[0]:

                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomic level:", 
                                            options=["Taxonomic Level 1", "Taxonomic Level 2 (Genus & Species)"],
                                            help="Show barplot for specific taxonomic level.")
            with barplot_menu[1]:
                # Select columns to plot
                select_column = st.selectbox("Select column:", options=dataset.columns, help="Select column from genefamilies table (cannot show all columns at once due to extremely large table).")
            
            with barplot_menu[2]:
                # Select number of top taxa in the column
                n_rows = st.selectbox("Select number of top rows:", options=[10, 25, 50, 100], help="Select number of top rows form selected column order descending.")
            
            # Include only rows with selected taxonomic level
            barplot_df = genefamiliesTaxonomy(dataset, taxonomy_level)

            # Take only selected column            
            barplot_df = barplot_df.loc[:, [select_column]]
            # Sort descending by selected column
            barplot_df = barplot_df.sort_values(by= select_column,ascending=False)
            # Take only selected number of top taxa
            barplot_df = barplot_df.head(n_rows)
            # Create and show barplot
            createBarplot(barplot_df, "Absolutní abundance [RPKs]")
        else:
            # If pathcoverage file is selected, show this message
            st.markdown("## Please select different file.")

            
        
else:
    # If no file is loaded display this title
    st.title("Please upload data in the sidebar")