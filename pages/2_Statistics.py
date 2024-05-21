import streamlit as st
import pandas as pd

from io import BytesIO
import plotly.graph_objects as go
from skbio.diversity.alpha import shannon, simpson


# Allow the content to be spread across the whole page
st.set_page_config(layout="wide")


# Function for loading data from .tsv file
def load_data(file, file_name):
    if "metaphlan" in file_name:
        dataset = pd.read_csv(BytesIO(file), sep="\t", index_col=0, skiprows=1)
        dataset.index.name = "Taxas"
    else:
        dataset = pd.read_csv(BytesIO(file), sep="\t", index_col=0)
    return dataset


# Function to plot differential heatmap
def plotDifferentialHeatmap(selected_dataset):
        
    selected_dataset["Difference"] = selected_dataset[str(first_sample)] - selected_dataset[str(second_sample)]
    
    selected_dataset = selected_dataset.sort_values(by="Difference", ascending=False)
    top_rows = selected_dataset.head(n_top_rows)
    top_rows = top_rows.iloc[::-1]
        
    fig = go.Figure(data=go.Heatmap(
                z=top_rows.values,
                y=top_rows.index,
                x=top_rows.columns,
                hoverongaps=False,
                colorscale="sunset",
            ))
    fig.layout.height = 1000
    st.plotly_chart(fig, use_container_width=True)



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
    if "differential_dataset" not in st.session_state:
        st.session_state.differential_dataset = dataset
    
    if "alpha_dataset" not in st.session_state:
        st.session_state.alpha_dataset = dataset
    
    if "beta_dataset" not in st.session_state:
        st.session_state.beta_dataset = dataset
    
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
        if st.session_state.metadata_uploaded == False:
            st.markdown("### Alpha and beta analysis requires metadata file. Please upload it below:")
            metadata_file = st.file_uploader("Upload metadata:")
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
            
            st.markdown("## Alpha diversity")

            alpha_menu = st.columns(3)

            with alpha_menu[0]:
                if "metaphlan" in select_file:

                    # Select box for selecting taxonomy level
                    taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                options=["Taxonomy Level 1", "Taxonomy Level 2", "Taxonomy Level 3", "Taxonomy Level 4", "Taxonomy Level 5", "Taxonomy Level 6", "Taxonomy Level 7", "Taxonomy Level 8"])
                    
                    # Switch statement for selecting taxonomy level and filtering dataframe
                    match taxonomy_level:
                        case "Taxonomy Level 1":
                            alpha_dataset = st.session_state.alpha_dataset[st.session_state.alpha_dataset.index.str.contains("k__") & ~st.session_state.alpha_dataset.index.str.contains("p__")]
                        case "Taxonomy Level 2":
                            alpha_dataset = st.session_state.alpha_dataset[st.session_state.alpha_dataset.index.str.contains("p__") & ~st.session_state.alpha_dataset.index.str.contains("c__")]
                        case "Taxonomy Level 3":
                            alpha_dataset = st.session_state.alpha_dataset[st.session_state.alpha_dataset.index.str.contains("c__") & ~st.session_state.alpha_dataset.index.str.contains("o__")]
                        case "Taxonomy Level 4":
                            alpha_dataset = st.session_state.alpha_dataset[st.session_state.alpha_dataset.index.str.contains("o__") & ~st.session_state.alpha_dataset.index.str.contains("f__")]
                        case "Taxonomy Level 5":
                            alpha_dataset = st.session_state.alpha_dataset[st.session_state.alpha_dataset.index.str.contains("f__") & ~st.session_state.alpha_dataset.index.str.contains("g__")]
                        case "Taxonomy Level 6":
                            alpha_dataset = st.session_state.alpha_dataset[st.session_state.alpha_dataset.index.str.contains("g__") & ~st.session_state.alpha_dataset.index.str.contains("s__")]
                        case "Taxonomy Level 7":
                            alpha_dataset = st.session_state.alpha_dataset[st.session_state.alpha_dataset.index.str.contains("s__") & ~st.session_state.alpha_dataset.index.str.contains("t__")]
                        case "Taxonomy Level 8":
                            alpha_dataset = st.session_state.alpha_dataset


                elif "pathabundance" in select_file:
                    # Select box for selecting taxonomy level
                    taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                options=["Taxonomy Level 1"])
                    match taxonomy_level:
                        case "Taxonomy Level 1":
                            alpha_dataset = st.session_state.alpha_dataset[st.session_state.alpha_dataset.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED") == False]
        

                elif "genefamilies" in select_file:
                
                    # Select box for selecting taxonomy level
                    taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                    options=["Taxonomy Level 1", "Taxonomy Level 2"])

                    match taxonomy_level:
                        case "Taxonomy Level 1":
                            alpha_dataset = st.session_state.alpha_dataset[st.session_state.alpha_dataset.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED") == False]
                        case "Taxonomy Level 2":
                            alpha_dataset = st.session_state.alpha_dataset[st.session_state.alpha_dataset.index.str.contains("g__")]

                with alpha_menu[1]:
                    metric_selection = st.selectbox("Select metric to group by:", options=st.session_state.metadata.columns)
                
                with alpha_menu[2]:
                    measure = st.selectbox("Select measure to calculate alpha diversity:", options=["Shannon", "Simpson"])
                
                if measure == "Shannon":

                    # Calculate shannon index for all samples
                    diversity_indexes = {}
                    for column in alpha_dataset:
                        diversity_indexes[column.split("_")[0]] = shannon(alpha_dataset[column])
                
                elif measure == "Simpson":
                    # Calculate simpson index for all samples
                    diversity_indexes = {}
                    for column in alpha_dataset:
                       diversity_indexes[column.split("_")[0]] = simpson(alpha_dataset[column])


            # Select metric for sample splitting 
            unique_values = st.session_state.metadata[[metric_selection]]

            # Add alpha diversity indexes to selected metric dataframe
            unique_values["DiversityIndex"] = unique_values.index.map(diversity_indexes)
            
            # Create violin plot for alpha diversity 
            fig = go.Figure()

            for seqKit in unique_values[metric_selection].unique():
                fig.add_trace(go.Violin(x=unique_values[metric_selection][unique_values[metric_selection] == seqKit],
                                        y=unique_values["DiversityIndex"][unique_values[metric_selection] == seqKit],
                                        name=seqKit,
                                        box_visible=True,
                                        meanline_visible=True,
                                        points="all"))
            
            st.plotly_chart(fig, use_container_width=True)



    ################################### Beta diversity ###################################
    # Tab for beta diversity analysis
    with beta_tab:
        pass

    ################################### Differential expression ###################################
   # Tab for differential analysis 
    with differential_tab:

        # Load currently selected dataset to session state variable 
        st.session_state.differential_dataset = dataset

        differential_menu = st.columns(3)

        with differential_menu[0]:
            first_sample = st.selectbox("Select first sample:", options=st.session_state.differential_dataset.columns, placeholder="-----")
        
        with differential_menu[1]:
            second_sample = st.selectbox("Select second sample:", options=st.session_state.differential_dataset.columns, placeholder="-----")
        
        with differential_menu[2]:
            n_top_rows = st.selectbox("Select number of top rows:", options=[10, 25, 50])


        if first_sample == second_sample:
            st.markdown("## Please select two different columns")

        else:
            if "metaphlan" in select_file:

                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomy level:", 
                                            options=["Taxonomy Level 1", "Taxonomy Level 2", "Taxonomy Level 3", "Taxonomy Level 4", "Taxonomy Level 5", "Taxonomy Level 6", "Taxonomy Level 7", "Taxonomy Level 8"])
                
                # Switch statement for selecting taxonomy level and filtering dataframe
                match taxonomy_level:
                    case "Taxonomy Level 1":
                        differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("p__")]
                    case "Taxonomy Level 2":
                        differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("c__")]
                    case "Taxonomy Level 3":
                        differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("o__")]
                    case "Taxonomy Level 4":
                        differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("f__")]
                    case "Taxonomy Level 5":
                        differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("g__")]
                    case "Taxonomy Level 6":
                        differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("s__")]
                    case "Taxonomy Level 7":
                        differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("t__")]
                    case "Taxonomy Level 8":
                        differential_dataset = st.session_state.differential_dataset

                selected_dataset = differential_dataset[[str(first_sample), str(second_sample)]]
        
                plotDifferentialHeatmap(selected_dataset)

            elif "pathabundance" in select_file:
                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomy level:", 
                                            options=["Taxonomy Level 1"])
                match taxonomy_level:
                    case "Taxonomy Level 1":
                        differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED") == False]
        
                selected_dataset = differential_dataset[[str(first_sample), str(second_sample)]]
        
                plotDifferentialHeatmap(selected_dataset)

            elif "genefamilies" in select_file:
            
                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                options=["Taxonomy Level 1"])

                match taxonomy_level:
                    case "Taxonomy Level 1":
                        differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED") == False]

                selected_dataset = differential_dataset[[str(first_sample), str(second_sample)]]
        
                plotDifferentialHeatmap(selected_dataset)
    
            else:
                st.markdown("## Please select different file.")
            
            
else:
    # If no file is loaded display this title
    st.title("Please upload data in the sidebar")