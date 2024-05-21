import streamlit as st
import pandas as pd

from io import BytesIO
import plotly.graph_objects as go


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

# Function to split dataset for pagination
def split_frame(input_df, rows):
    split_df = [input_df.iloc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return split_df

# Function to create normalized dataset
def normalize_dataset(table):
    for column in table.columns:
        table[column] = (table[column]/table[column].sum())*100
    return table

# Function to turn on and off Mean abundance checkbox
def toggle_box(): st.session_state.box_value = not st.session_state.box_value

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

    # Define session state variables for each statistical analysis
    if "differential_dataset" not in st.session_state:
        st.session_state.differential_dataset = dataset
    
    if "alpha_dataset" not in st.session_state:
        st.session_state.alpha_dataset = dataset
    
    if "beta_dataset" not in st.session_state:
        st.session_state.beta_dataset = dataset
    
    if "metadata" not in st.session_state:
        st.session_state.metadata = None

    # Print title of the page
    st.title("Statistics")

    # Create tabs for each statistical analysis
    alpha_tab, beta_tab, differential_tab = st.tabs(["Alpha Diversity", "Beta Diversity", "Differential Expression"])

    ################################### Alpha diversity ###################################
    # Tab for alpha diversity analysis
    with alpha_tab:
        if st.session_state.metadata == None:
            metadata_file = st.file_uploader("Upload metadata:")
            if metadata_file:
                bytes_metadata = metadata_file.getvalue()

                metadata_df = pd.read_csv
    
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
                        st.session_state.differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("p__")]
                    case "Taxonomy Level 2":
                        st.session_state.differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("c__")]
                    case "Taxonomy Level 3":
                        st.session_state.differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("o__")]
                    case "Taxonomy Level 4":
                        st.session_state.differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("f__")]
                    case "Taxonomy Level 5":
                        st.session_state.differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("g__")]
                    case "Taxonomy Level 6":
                        st.session_state.differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("s__")]
                    case "Taxonomy Level 7":
                        st.session_state.differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("k__") & ~st.session_state.differential_dataset.index.str.contains("t__")]
                    case "Taxonomy Level 8":
                        st.session_state.differential_dataset = st.session_state.differential_dataset

                selected_dataset = st.session_state.differential_dataset[[str(first_sample), str(second_sample)]]
        
                plotDifferentialHeatmap(selected_dataset)

            elif "pathabundance" in select_file:
                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomy level:", 
                                            options=["Taxonomy Level 1"])
                match taxonomy_level:
                    case "Taxonomy Level 1":
                        st.session_state.differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED") == False]
        
                selected_dataset = st.session_state.differential_dataset[[str(first_sample), str(second_sample)]]
        
                plotDifferentialHeatmap(selected_dataset)

            elif "genefamilies" in select_file:
            
                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                options=["Taxonomy Level 1"])

                match taxonomy_level:
                    case "Taxonomy Level 1":
                        st.session_state.differential_dataset = st.session_state.differential_dataset[st.session_state.differential_dataset.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED") == False]

                selected_dataset = st.session_state.differential_dataset[[str(first_sample), str(second_sample)]]
        
                plotDifferentialHeatmap(selected_dataset)
    
            else:
                st.markdown("## Please select different file.")
            
            
else:
    # If no file is loaded display this title
    st.title("Please upload data in the sidebar")