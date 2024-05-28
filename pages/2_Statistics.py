# Import libraries 
import streamlit as st
import pandas as pd

from io import BytesIO

import plotly.graph_objects as go
import plotly.express as px

from skbio.diversity.alpha import shannon, simpson
from skbio.diversity import beta_diversity
from skbio.stats.ordination import pcoa



# Allow the content to be spread across the whole page
st.set_page_config(layout="wide")


# Function for loading data from .tsv file
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


# Function to plot differential heatmap
def plotDifferentialHeatmap(selected_dataset, nTopRows):
    """Takes selected DataFrame, calculates Difference column and shows heatmap based on this column.

    Args:
        selected_dataset (DataFrame): Selected DataFrame for differential expression
        nTopRows (int): Number of top rows to be selected 
    """

    # Calculate Difference column
    selected_dataset["Difference"] = abs(selected_dataset[str(first_sample)] - selected_dataset[str(second_sample)])

    # Sort descending by Difference column
    selected_dataset = selected_dataset.sort_values(by="Difference", ascending=False)

    # Select number of top rows
    top_rows = selected_dataset.head(nTopRows)

    # Reverse sort order for the heatmap plotting 
    top_rows = top_rows.iloc[::-1]
        
    # Create heatmap 
    fig = go.Figure(data=go.Heatmap(
                z=top_rows.values,
                y=top_rows.index,
                x=top_rows.columns,
                hoverongaps=False,
                colorscale="sunset",
            ))
    fig.layout.height = 1000

    # Display heatmap
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
uploaded_files = st.sidebar.file_uploader("Select TSV file to upload", accept_multiple_files=True, type=["tsv", "csv"])

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

    # Define session state variables for each statistical analysis
    if "metadata" not in st.session_state:
        st.session_state.metadata = None
    
    if "metadata_uploaded" not in st.session_state:
        st.session_state.metadata_uploaded = False

    # Print title of the page
    st.title("Statistics")

    # Create tabs for each statistical analysis
    alpha_tab, beta_tab, differential_tab = st.tabs(["Alpha Diversity", "Beta Diversity", "Differential Expression"])

    ################################### Alpha diversity ###################################
    # Tab for alpha diversity analysis
    with alpha_tab:
        # Condition to upload metadata if no metadata uploaded
        if st.session_state.metadata_uploaded == False:
            st.markdown("### Alpha and beta analysis requires metadata file. Please upload it below:")
            metadata_file = st.file_uploader("Upload metadata:")

            # Condition to process loaded metadata
            if metadata_file:
                bytes_metadata = metadata_file.getvalue()
                
                if ".tsv" in metadata_file.name:
                    metadata_df = pd.read_csv(BytesIO(bytes_metadata), sep="\t", index_col=0)
                if ".csv" in metadata_file.name:
                    metadata_df = pd.read_csv(BytesIO(bytes_metadata), sep=",", index_col=0)
                
                st.session_state.metadata = metadata_df
                st.session_state.metadata_uploaded = True
                st.rerun()

        # After metadata uploaded, create plots for statistical analysis        
        elif st.session_state.metadata_uploaded == True:
            
            st.markdown("## Alpha diversity")
            
            if "pathcoverage" not in select_file:
                alpha_menu = st.columns(3)

                with alpha_menu[0]:
                    if "metaphlan" in select_file:

                        # Select box for selecting taxonomic level
                        alpha_taxonomy_level = st.selectbox("Select taxonomic level:", 
                                                    options=["Taxonomic Level 1 (Kingdom)", "Taxonomic Level 2 (Phylum)", "Taxonomic Level 3 (Class)", "Taxonomic Level 4 (Order)", "Taxonomic Level 5 (Family)", "Taxonomic Level 6 (Genus)", "Taxonomic Level 7 (Species)", "Taxonomic Level 8 (All)"],
                                                    help="Show alpha diversity for specific taxonomic level.")
                        # Include only rows with selected taxonomic level
                        alpha_dataset = metaphlanTaxonomy(dataset, alpha_taxonomy_level)

                    elif "pathabundance" in select_file:
                        # Select box for selecting taxonomic level
                        alpha_taxonomy_level = st.selectbox("Select taxonomic level:", 
                                                    options=["Taxonomic Level 1"],help="Show alpha diversity for specific taxonomic level.")
                        # Include only rows with selected taxonomic level
                        alpha_dataset = pathabundaceTaxonomy(dataset, alpha_taxonomy_level)

                    elif "genefamilies" in select_file:
                    
                        # Select box for selecting taxonomic level
                        alpha_taxonomy_level = st.selectbox("Select taxonomic level:", 
                                                        options=["Taxonomic Level 1", "Taxonomic Level 2 (Genus & Species)"], help="Show alpha diversity for specific taxonomic level.")
                        # Include only rows with selected taxonomic level
                        alpha_dataset = genefamiliesTaxonomy(dataset, alpha_taxonomy_level)
                    
                    
                        
                        
                with alpha_menu[1]:
                    # Select feature to group samples by
                    feature_selection = st.selectbox("Select feature to group by:", options=st.session_state.metadata.columns, help="Features from metadata to group by.")
                    
                with alpha_menu[2]:
                    # Select alpha diversity measure 
                    measure = st.selectbox("Select measure to calculate alpha diversity:", options=["Shannon", "Simpson"], help="Select preferred alpha diversity measure.")


                diversity_indexes = {}
                if measure == "Shannon":
                    # Calculate shannon index for all samples
                    for column in alpha_dataset:
                        diversity_indexes[column.split("_")[0]] = shannon(alpha_dataset[column])
                
                elif measure == "Simpson":
                    # Calculate simpson index for all samples
                    for column in alpha_dataset:
                        diversity_indexes[column.split("_")[0]] = simpson(alpha_dataset[column])


                # Select feature for sample splitting 
                unique_values = st.session_state.metadata[[feature_selection]]

                # Add alpha diversity indexes to selected feature dataframe
                unique_values["DiversityIndex"] = unique_values.index.map(diversity_indexes)
                
                # Create violin plot for alpha diversity 
                fig = go.Figure()

                for seqKit in unique_values[feature_selection].unique():
                    fig.add_trace(go.Violin(x=unique_values[feature_selection][unique_values[feature_selection] == seqKit],
                                            y=unique_values["DiversityIndex"][unique_values[feature_selection] == seqKit],
                                            name=seqKit,
                                            box_visible=True,
                                            meanline_visible=True,
                                            points="all"))
                
                # Show violin plot
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown("## Please select different file.")



    ################################### Beta diversity ###################################
    # Tab for beta diversity analysis
    with beta_tab:
        # Condition to upload metadata if no metadata uploaded
        if st.session_state.metadata_uploaded == False:
            st.markdown("### Alpha and beta analysis requires metadata file. Please upload it below:")
            metadata_file = st.file_uploader("Upload metadata:", key="Beta")

            # Condition to process loaded metadata
            if metadata_file:
                bytes_metadata = metadata_file.getvalue()
                
                if ".tsv" in metadata_file.name:
                    metadata_df = pd.read_csv(BytesIO(bytes_metadata), sep="\t", index_col=0)
                if ".csv" in metadata_file.name:
                    metadata_df = pd.read_csv(BytesIO(bytes_metadata), sep=",", index_col=0)
                
                st.session_state.metadata = metadata_df
                st.session_state.metadata_uploaded = True
                st.rerun()
                
        elif st.session_state.metadata_uploaded == True:
            
            st.markdown("## Beta diversity")

            # Condition to exclude pathcoverage 
            if "pathcoverage" not in select_file:
                beta_menu = st.columns(3)

                with beta_menu[0]:
                    if "metaphlan" in select_file:

                        # Select box for selecting taxonomy level
                        beta_taxonomy_level = st.selectbox("Select taxonomic level:", 
                                                    options=["Taxonomic Level 1 (Kingdom)", "Taxonomic Level 2 (Phylum)", "Taxonomic Level 3 (Class)", "Taxonomic Level 4 (Order)", "Taxonomic Level 5 (Family)", "Taxonomic Level 6 (Genus)", "Taxonomic Level 7 (Species)", "Taxonomic Level 8 (All)"],
                                                    key="Beta", help="Show beta diversity for specific taxonomic level.")
                        # Include only rows with selected taxonomic level
                        beta_dataset = metaphlanTaxonomy(dataset, beta_taxonomy_level)

                    elif "pathabundance" in select_file:
                        # Select box for selecting taxonomy level
                        beta_taxonomy_level = st.selectbox("Select taxonomic level:", 
                                                    options=["Taxonomic Level 1"],
                                                    key="Beta", help="Show beta diversity for specific taxonomic level.")
                        # Include only rows with selected taxonomic level
                        beta_dataset = pathabundaceTaxonomy(dataset, beta_taxonomy_level)

                    elif "genefamilies" in select_file:
                    
                        # Select box for selecting taxonomy level
                        beta_taxonomy_level = st.selectbox("Select taxonomic level:", 
                                                        options=["Taxonomic Level 1", "Taxonomic Level 2 (Genus & Species)"],
                                                        key="Beta", help="Show beta diversity for specific taxonomic level.")
                        # Include only rows with selected taxonomic level
                        beta_dataset = genefamiliesTaxonomy(dataset, beta_taxonomy_level)
                    
                        
                    
                with beta_menu[2]:
                    # Select beta diversity measure 
                    measure = st.selectbox("Select measure to calculate beta diversity:", options=["Braycurtis", "Jaccard"], help="Select preferred beta diversity measure.")

                # Condition to exclude samples (columns) with zero in all rows
                if any(beta_dataset[col].eq(0).all() for col in beta_dataset.columns):
                    all_zero_columns = beta_dataset.columns[(beta_dataset==0).all()]
                    beta_dataset = beta_dataset.drop(columns=all_zero_columns)

                    # Print the excluded samples
                    all_zero_list = ", ".join(list(all_zero_columns))
                
                    st.markdown(f"<span style='color:red'>Column dropped due zero abundance values: {all_zero_list}.</span>", unsafe_allow_html=True)

                # Transpose DataFrame
                beta_dataset = beta_dataset.T
                
                # Calculate beta diversity 
                if measure == "Braycurtis":
                    distance_matrix = beta_diversity(metric="braycurtis", counts=beta_dataset)
                    title_heatmap = 'Heatmap of Bray-Curtis Distance Matrix (0 - max. similarity, 1 - max. dissimilarity)'
                    title_3D = '3D PCoA of Bray-Curtis Distance Matrix'

                elif measure == "Jaccard":
                    distance_matrix = beta_diversity(metric="jaccard", counts=beta_dataset)
                    title_heatmap = 'Heatmap of Jaccard Distance Matrix (0 - max. dissimilarity, 1 - max. similarity)'
                    title_3D = '3D PCoA of Jaccard Distance Matrix'

                # Calculate PCOA
                distance_df = pd.DataFrame(distance_matrix.data, index=distance_matrix.ids, columns=distance_matrix.ids)
                pcoa_results = pcoa(distance_matrix)

                pcoa_df = pcoa_results.samples
                pcoa_df.reset_index(inplace=True)
                pcoa_df.rename(columns={'index': 'Sample'}, inplace=True)

                # Create heatmap for beta diversity 
                beta_heatmap = go.Figure(data=go.Heatmap(
                    z=distance_df.values,
                    x=distance_df.columns,
                    y=distance_df.index,
                    colorscale='Sunset'
                ))


                beta_heatmap.update_layout(
                    title=title_heatmap,
                    xaxis_title='Samples',
                    yaxis_title='Samples'
                )

                # Show heatmap for beta diversity 
                st.plotly_chart(beta_heatmap, use_container_width=True)  

                # Create 3D scatter plot for PCoA
                fig = px.scatter_3d(pcoa_df, x='PC1', y='PC2', z='PC3', text='Sample', title=title_3D,
                    labels = {
                            'PC1': f'PC1 ({pcoa_results.proportion_explained.iloc[0]*100:.2f}%)',
                            'PC2': f'PC2 ({pcoa_results.proportion_explained.iloc[1]*100:.2f}%)',
                            'PC3': f'PC3 ({pcoa_results.proportion_explained.iloc[2]*100:.2f}%)'
                                }
                                )
                # Update the layout for better readability
                fig.update_traces(marker=dict(size=5), selector=dict(mode='markers+text'))
                fig.update_layout(autosize=False, width=800, height=600,
                                margin=dict(l=50, r=50, b=50, t=50))
                
                # Show 3D scatter plot for PCoA
                st.plotly_chart(fig, use_container_width=True)
            else:
                # If pathcoverage file is selected, show this message
                st.markdown("## Please select different file.")


    ################################### Differential expression ###################################
   # Tab for differential analysis 
    with differential_tab:

        # Load currently selected dataset to session state variable 
        st.session_state.differential_dataset = dataset

        # Columns for buttons
        differential_menu = st.columns(3)

        with differential_menu[0]:
            # Select first sample
            first_sample = st.selectbox("Select first sample:", options=st.session_state.differential_dataset.columns, placeholder="-----", help="Select first sample to calculate difference.")
        
        with differential_menu[1]:
            # Select second sample
            second_sample = st.selectbox("Select second sample:", options=st.session_state.differential_dataset.columns, placeholder="-----", help="Select second sample to calculate difference.")
        
        with differential_menu[2]:
            # Select number of top rows
            n_top_rows = st.selectbox("Select number of top rows:", options=[10, 25, 50], help="Number of top rows from difference column ordered descending.")

        # If sample names are the same, show this message
        if first_sample == second_sample:
            st.markdown("## Please select two different columns")

        else:
            if "metaphlan" in select_file:

                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomic level:", 
                                            options=["Taxonomic Level 1 (Kingdom)", "Taxonomic Level 2 (Phylum)", "Taxonomic Level 3 (Class)", "Taxonomic Level 4 (Order)", "Taxonomic Level 5 (Family)", "Taxonomic Level 6 (Genus)", "Taxonomic Level 7 (Species)", "Taxonomic Level 8 (All)"],
                                            key="diff", help="Select taxonomic level to calculate difference on.")
                
                # Include only rows with selected taxonomic level
                differential_dataset = metaphlanTaxonomy(dataset,taxonomy_level)

                # Include only selected columns
                selected_dataset = differential_dataset[[str(first_sample), str(second_sample)]]

                # Create and show heatmap
                plotDifferentialHeatmap(selected_dataset, n_top_rows)

            elif "pathabundance" in select_file:
                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomic level:", 
                                            options=["Taxonomic Level 1"],
                                            key="diff", help="Select taxonomic level to calculate difference on.")
                
                # Include only rows with selected taxonomic level
                differential_dataset = pathabundaceTaxonomy(dataset, taxonomy_level)

                # Include only selected columns
                selected_dataset = differential_dataset[[str(first_sample), str(second_sample)]]

                # Create and show heatmap
                plotDifferentialHeatmap(selected_dataset, n_top_rows)

            elif "genefamilies" in select_file:
            
                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomic level:", 
                                                options=["Taxonomic Level 1", "Taxonomic Level 2 (Genus & Species)"],
                                                key="diff", help="Select taxonomic level to calculate difference on.")
                
                # Include only rows with selected taxonomic level
                differential_dataset = genefamiliesTaxonomy(dataset, taxonomy_level)

                # Include only selected columns
                selected_dataset = differential_dataset[[str(first_sample), str(second_sample)]]

                # Create and show heatmap
                plotDifferentialHeatmap(selected_dataset, n_top_rows)
    
            else:
                # If pathcoverage file is selected, show this message
                st.markdown("## Please select different file.")
            
            
else:
    # If no file is loaded display this title
    st.title("Please upload data in the sidebar")