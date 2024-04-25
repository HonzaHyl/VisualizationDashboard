import streamlit as st
import pandas as pd
import numpy as np


# Allow the content to be spread across the whole page
st.set_page_config(layout="wide")

# Function for loading data from .tsv file
@st.cache_data(show_spinner=False)
def load_data(file_path):
    dataset = pd.read_csv(file_path, sep="\t", index_col=0)
    return dataset

# Function to split dataset for pagination
@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df = [input_df.iloc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df

# Function to create normalized dataset
@st.cache_data(show_spinner=False)
def normalize_dataset(table):
    for column in table.columns:
        table[column] = (table[column]/table[column].sum())*100
    
    return table

# Function to turn on and off Mean abundance checkbox
def toggle_box(): st.session_state.box_value = not st.session_state.box_value

# Widget to upload single file
file_path = st.sidebar.file_uploader("Select TSV file to upload")

# If file is uploaded, load it to session state dataset
if file_path:
    if "dataset" not in st.session_state:
        st.session_state.dataset = load_data(file_path)

# Initialize values in session state
if "dataset" in st.session_state:

    if "normalized_dataset" not in st.session_state:
        st.session_state.normalized_dataset = normalize_dataset(st.session_state.dataset)
    
    if "selected_dataset" not in st.session_state:
        st.session_state.selected_dataset = st.session_state.dataset
    
    if "box_value" not in st.session_state:
        st.session_state.box_value = False
    
    # Initialize top menu
    top_menu = st.columns(3)
    
    with top_menu[2]:
        # Manage column with mean abundance
        add_mean_abundance = st.checkbox("Mean abundance", disabled=st.session_state.box_value, value=False, help="Adds column with mean abundance per taxon (per row)")
        
        # Normalize dataset
        normalize = st.checkbox("Normalize", value=False, on_change=toggle_box, help="Normalize columns to relative abundance of taxons per sample (percentage)")

        # Conditions to toggle normalization
        if normalize == True:
            st.session_state.selected_dataset = st.session_state.normalized_dataset
        if normalize == False:
            st.session_state.selected_dataset = st.session_state.dataset

        # Condition to toggle mean abundance
        if add_mean_abundance == True:
            st.session_state.selected_dataset["Mean abundance"] = st.session_state.selected_dataset.mean(axis=1)

        if add_mean_abundance == False and "Mean abundance" in st.session_state.selected_dataset.columns:
            st.session_state.selected_dataset = st.session_state.selected_dataset.drop("Mean abundance", axis=1)
        
        

        if normalize == True:
            st.session_state.selected_dataset = st.session_state.normalized_dataset
        if normalize == False:
            st.session_state.selected_dataset = st.session_state.dataset

    with top_menu[0]:
        columnsNames = st.session_state.selected_dataset.columns.to_list()
        columnsNames.append(st.session_state.selected_dataset.index.name)

        sort_field = st.selectbox("Sort By", options=columnsNames, index=len(columnsNames)-1)

    with top_menu[1]:
        sort_direction = st.radio(
            "Direction", options=["⬆️", "⬇️"], horizontal=True
        )
       
        st.session_state.selected_dataset = st.session_state.selected_dataset.sort_values(
        by=sort_field, ascending=sort_direction == "⬆️"
        )
                 

    pagination = st.container()

    bottom_menu = st.columns((4, 1, 1))

    with bottom_menu[2]:
        batch_size = st.selectbox("Page Size", options=[25, 50, 100])

    with bottom_menu[1]:
        total_pages = (
            int(len(st.session_state.selected_dataset) / batch_size) if int(len(st.session_state.selected_dataset) / batch_size) > 0 else 1
        )
        current_page = st.number_input(
            "Page", min_value=1, max_value=total_pages, step=1
        )

    with bottom_menu[0]:
        st.markdown(f"Page **{current_page}** of **{total_pages}** ")
    

    pages = split_frame(st.session_state.selected_dataset, batch_size)
    pagination.dataframe(data=pages[current_page - 1], use_container_width=True)


   

else:
    st.title("Please upload data in the sidebar")

    