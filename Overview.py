import streamlit as st
import pandas as pd
import numpy as np

from io import BytesIO

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
    
    # Copy loaded dataset to variable for dataset to show 
    selected_df = dataset
    
    # Session state variable for disabling Mean column checkbox 
    if "box_value" not in st.session_state:
        st.session_state.box_value = False

    st.title("Overview")

    # Initialize top menu
    top_menu = st.columns(4)

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

    with top_menu[2]:
        # Manage column with mean abundance
        add_mean_abundance = st.checkbox("Mean abundance", disabled=st.session_state.box_value, value=False, help="Adds column with mean abundance per taxon (per row)")
        
        # Normalize dataset
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
    
    with top_menu[3]:
        if "metaphlan" in select_file: 
            taxonomy_sort = st.selectbox("Select taxonomy rank:", options=["Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species"])

            match taxonomy_sort:
                case "Kingdom":
                    selected_df = selected_df[selected_df.index.str.contains("k__")==True]
                case "Phylum":
                    selected_df = selected_df[selected_df.index.str.contains("p__")==True]
                case "Class":
                    selected_df = selected_df[selected_df.index.str.contains("c__")==True]
                case "Order":
                    selected_df = selected_df[selected_df.index.str.contains("o__")==True]
                case "Family":
                    selected_df = selected_df[selected_df.index.str.contains("f__")==True]
                case "Genus":
                    selected_df = selected_df[selected_df.index.str.contains("g__")==True]
                case "Species":
                    selected_df = selected_df[selected_df.index.str.contains("s__")==True]   

        if "genefamilies" in select_file:
            level_sort = st.selectbox("Show row on taxonomy level:", options=["All", "Collapsed", "Genus", "Species"])

            match level_sort:
                case "All":
                    selected_df = selected_df
                case "Collapsed":
                    selected_df = selected_df[selected_df.index.str.contains("g__|unclassified|s__")==False]
                case "Genus":
                    selected_df = selected_df[selected_df.index.str.contains("g__")==True]
                case "Species":
                    selected_df = selected_df[selected_df.index.str.contains("s__")==True]


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

    