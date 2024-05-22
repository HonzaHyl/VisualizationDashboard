import streamlit as st
import pandas as pd

from io import BytesIO
import plotly.graph_objects as go
from skbio.diversity.alpha import shannon, simpson
from skbio.diversity import beta_diversity
from skbio.stats.ordination import pcoa
import plotly.express as px


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
        
    selected_dataset["Difference"] = abs(selected_dataset[str(first_sample)] - selected_dataset[str(second_sample)])
    
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
                    alpha_taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                options=["Taxonomy Level 1", "Taxonomy Level 2", "Taxonomy Level 3", "Taxonomy Level 4", "Taxonomy Level 5", "Taxonomy Level 6", "Taxonomy Level 7", "Taxonomy Level 8"])
                    
                    alpha_dataset = metaphlanTaxonomy(dataset, alpha_taxonomy_level)

                elif "pathabundance" in select_file:
                    # Select box for selecting taxonomy level
                    alpha_taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                options=["Taxonomy Level 1"])
                    alpha_dataset = pathabundaceTaxonomy(dataset, alpha_taxonomy_level)

                elif "genefamilies" in select_file:
                
                    # Select box for selecting taxonomy level
                    alpha_taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                    options=["Taxonomy Level 1", "Taxonomy Level 2"])

                    alpha_dataset = genefamiliesTaxonomy(dataset, alpha_taxonomy_level)
                
                elif "pathcoverage" in select_file:

                    alpha_dataset = dataset[dataset.index.str.contains("g__") == False]
                    
            with alpha_menu[1]:
                metric_selection = st.selectbox("Select metric to group by:", options=st.session_state.metadata.columns)
                
            with alpha_menu[2]:
                measure = st.selectbox("Select measure to calculate alpha diversity:", options=["Shannon", "Simpson"])


            diversity_indexes = {}
            if measure == "Shannon":
                # Calculate shannon index for all samples
                for column in alpha_dataset:
                    diversity_indexes[column.split("_")[0]] = shannon(alpha_dataset[column])
            
            elif measure == "Simpson":
                # Calculate simpson index for all samples
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
        if st.session_state.metadata_uploaded == False:
            st.markdown("### Alpha and beta analysis requires metadata file. Please upload it below:")
            metadata_file = st.file_uploader("Upload metadata:", key="Beta")
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

            beta_menu = st.columns(3)

            with beta_menu[0]:
                if "metaphlan" in select_file:

                    # Select box for selecting taxonomy level
                    beta_taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                options=["Taxonomy Level 1", "Taxonomy Level 2", "Taxonomy Level 3", "Taxonomy Level 4", "Taxonomy Level 5", "Taxonomy Level 6", "Taxonomy Level 7", "Taxonomy Level 8"],
                                                key="Beta")
                    
                    beta_dataset = metaphlanTaxonomy(dataset, beta_taxonomy_level)

                elif "pathabundance" in select_file:
                    # Select box for selecting taxonomy level
                    beta_taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                options=["Taxonomy Level 1"],
                                                key="Beta")
                    beta_dataset = pathabundaceTaxonomy(dataset, beta_taxonomy_level)

                elif "genefamilies" in select_file:
                
                    # Select box for selecting taxonomy level
                    beta_taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                    options=["Taxonomy Level 1", "Taxonomy Level 2"],
                                                    key="Beta")

                    beta_dataset = genefamiliesTaxonomy(dataset, beta_taxonomy_level)
                
                elif "pathcoverage" in select_file:

                    beta_dataset = dataset[dataset.index.str.contains("g__") == False]
                    
            #with beta_menu[1]:
                #metric_selection = st.selectbox("Select metric to group by:", options=st.session_state.metadata.columns, key="MetricBeta")
                
            with beta_menu[2]:
                measure = st.selectbox("Select measure to calculate alpha diversity:", options=["Braycurtis", "Jaccard"])

            if any(beta_dataset[col].eq(0).all() for col in beta_dataset.columns):
                all_zero_columns = beta_dataset.columns[(beta_dataset==0).all()]
                beta_dataset = beta_dataset.drop(columns=all_zero_columns)

                all_zero_list = ", ".join(list(all_zero_columns))
                print(all_zero_list)
                st.markdown(f"<span style='color:red'>Column dropped due zero abundance values: {all_zero_list}.</span>", unsafe_allow_html=True)


            beta_dataset = beta_dataset.T
            
            if measure == "Braycurtis":
                distance_matrix = beta_diversity(metric="braycurtis", counts=beta_dataset)
                title_heatmap = 'Heatmap of Bray-Curtis Distance Matrix (0 - max. similarity, 1 - max. dissimilarity)'
                title_3D = '3D PCoA of Bray-Curtis Distance Matrix'

            elif measure == "Jaccard":
                distance_matrix = beta_diversity(metric="jaccard", counts=beta_dataset)
                title_heatmap = 'Heatmap of Jaccard Distance Matrix (0 - max. dissimilarity, 1 - max. similarity)'
                title_3D = '3D PCoA of Jaccard Distance Matrix'

            distance_df = pd.DataFrame(distance_matrix.data, index=distance_matrix.ids, columns=distance_matrix.ids)
            pcoa_results = pcoa(distance_matrix)

            pcoa_df = pcoa_results.samples
            pcoa_df.reset_index(inplace=True)
            pcoa_df.rename(columns={'index': 'Sample'}, inplace=True)

            # Plot the heatmap using Plotly
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

            # Show the plot
            st.plotly_chart(beta_heatmap, use_container_width=True)  

    
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
            
            st.plotly_chart(fig, use_container_width=True)


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
                                            options=["Taxonomy Level 1", "Taxonomy Level 2", "Taxonomy Level 3", "Taxonomy Level 4", "Taxonomy Level 5", "Taxonomy Level 6", "Taxonomy Level 7", "Taxonomy Level 8"],
                                            key="diff")
                
                differential_dataset = metaphlanTaxonomy(dataset,taxonomy_level)

                selected_dataset = differential_dataset[[str(first_sample), str(second_sample)]]
        
                plotDifferentialHeatmap(selected_dataset)

            elif "pathabundance" in select_file:
                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomy level:", 
                                            options=["Taxonomy Level 1"],
                                            key="diff")
                differential_dataset = pathabundaceTaxonomy(dataset, taxonomy_level)

                selected_dataset = differential_dataset[[str(first_sample), str(second_sample)]]
        
                plotDifferentialHeatmap(selected_dataset)

            elif "genefamilies" in select_file:
            
                # Select box for selecting taxonomy level
                taxonomy_level = st.selectbox("Select taxonomy level:", 
                                                options=["Taxonomy Level 1", "Taxonomy Level 2"],
                                                key="diff")

                differential_dataset = genefamiliesTaxonomy(dataset, taxonomy_level)

                selected_dataset = differential_dataset[[str(first_sample), str(second_sample)]]
        
                plotDifferentialHeatmap(selected_dataset)
    
            else:
                st.markdown("## Please select different file.")
            
            
else:
    # If no file is loaded display this title
    st.title("Please upload data in the sidebar")