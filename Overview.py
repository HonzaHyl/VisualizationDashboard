# Import libraries 
import streamlit as st
import pandas as pd
from io import BytesIO

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

# Function to split dataset for pagination
def split_frame(input_df, rows):
    """Takes whole DataFrame and returns list of DataFrames. These DataFrames
    represent individual pages with selected number of rows.

    Args:
        input_df (DataFrame): Table to split
        rows (int): Number of rows to display in a page

    Returns:
        List: List of DataFrames
    """
    split_df = [input_df.iloc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return split_df

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

# Function to turn on and off Mean abundance checkbox
def toggle_box(): st.session_state.box_value = not st.session_state.box_value

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

def pathabundaceTaxonomy(dataframe, taxonomy_level):
    """Function selects rows based on taxonomic level.

    Args:
        dataframe (DataFrame): Whole table (file)
        taxonomy_level (str): Selected taxonomic level

    Returns:
        DataFrame: DataFrame with only rows on selected taxonomic level.
    """
    match taxonomy_level:
        case "Taxonomy Level 1":
            selection = dataframe[dataframe.index.str.contains("g__|unclassified|UNINTEGRATED|UNMAPPED") == False]
    return selection


# Initialize the session state dictionary if not already present
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

# Widget to upload multiple files
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
    
    # Copy loaded dataset to variable for dataset to show 
    selected_df = dataset
    
    # Session state variable for disabling Mean column checkbox 
    if "box_value" not in st.session_state:
        st.session_state.box_value = False

    st.title("Overview")

    # Initialize top menu
    top_menu = st.columns(4)

    with top_menu[2]:
        # Manage column with mean abundance
        add_mean_abundance = st.checkbox("Mean abundance", disabled=st.session_state.box_value, value=False, help="Adds column with mean abundance per taxon (per row)")
        
        # Normalize dataset
        if "metaphlan" in select_file:
            normalize = st.checkbox("Normalize", value=False, disabled=True, on_change=toggle_box, help="Normalize columns to relative abundance of taxons per sample (percentage)")
        else:    
            normalize = st.checkbox("Normalize", value=False, on_change=toggle_box, help="Normalize columns to relative abundance of taxons per sample (percentage)")

        # Conditions to toggle normalization
        if normalize == True:
            selected_df = normalize_dataset(selected_df)
        if normalize == False:
            selected_df = selected_df

        # Condition to toggle mean abundance
        if add_mean_abundance == True:
            selected_df["Mean abundance"] = selected_df.mean(axis=1)

        if add_mean_abundance == False and "Mean abundance" in selected_df.columns:
            selected_df = selected_df.drop("Mean abundance", axis=1)
        
        if st.session_state.box_value == True and "Mean abundance" in selected_df.columns:
            selected_df = selected_df.drop("Mean abundance", axis=1)

    # Select box to choose by which column to sort
    with top_menu[0]:
        columnsNames = selected_df.columns.to_list()
        columnsNames.append(selected_df.index.name)

        sort_field = st.selectbox("Sort By", options=columnsNames, index=len(columnsNames)-1)

    # Radio buttons for sorting direction
    with top_menu[1]:
        sort_direction = st.radio("Direction", options=["⬆️", "⬇️"], horizontal=True)

        # Sort selected dataset
        selected_df = selected_df.sort_values(by=sort_field, ascending=sort_direction == "⬆️")
    
    # Select taxonomic level
    with top_menu[3]:
        # Button for taxonomic level selection for MetaPhlAn results
        if "metaphlan" in select_file: 
            taxonomy_sort = st.selectbox("Select taxonomic level:", 
                                         options=["Taxonomic Level 1 (Kingdom)", "Taxonomic Level 2 (Phylum)", "Taxonomic Level 3 (Class)", "Taxonomic Level 4 (Order)", "Taxonomic Level 5 (Family)", "Taxonomic Level 6 (Genus)", "Taxonomic Level 7 (Species)", "Taxonomic Level 8 (All)"], 
                                         help="Shows all rows assigned to specific taxonomic level.")

            selected_df = metaphlanTaxonomy(selected_df, taxonomy_sort)

        # Button for taxonomic level selection for gene families
        if "genefamilies" in select_file:
            level_sort = st.selectbox("Show row on taxonomic level:", options=["All", "Collapsed", "Genus & Species"], 
                                      help="Select taxonomic level (All - whole table, Collapsed - without g__ & s__, Genus & Species - only g__ & s__)")

            match level_sort:
                case "All":
                    selected_df = selected_df
                case "Collapsed":
                    selected_df = selected_df[selected_df.index.str.contains("g__|unclassified|s__")==False]
                case "Genus & Species":
                    selected_df = selected_df[selected_df.index.str.contains("g__")==True]


    # Set up container for dataset
    pagination = st.container()

    # Initialize bottom menu
    bottom_menu = st.columns((4, 1, 1))

    # Select box for page size
    with bottom_menu[2]:
        batch_size = st.selectbox("Page Size", options=[25, 50, 100])

    # Counter for pagination
    with bottom_menu[1]:
        total_pages = (
            int(len(selected_df) / batch_size) if int(len(selected_df) / batch_size) > 0 else 1
        )
        current_page = st.number_input(
            "Page", min_value=1, max_value=total_pages, step=1
        )

    # Display number of current page out of all pages
    with bottom_menu[0]:
        st.markdown(f"Page **{current_page}** of **{total_pages}** ")
    
    # Split dataset to pages
    pages = split_frame(selected_df, batch_size)

    # Print dataset on the page
    pagination.dataframe(data=pages[current_page - 1], use_container_width=True)

    


   

else:
    # If no file is loaded display this title
    st.title("Please upload data in the sidebar")

    