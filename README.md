# Metatranscriptomic visualization dashboard
<div style="text-align:justify">Metatranscriptomic visualization dashboard is a tool for visualizing merged results of HUMAnN workflow. It provides interactive and easy way to view data using various graphs and statistical analysis. </div>

## Requirements ##

### Software ###

1. [Python](https://www.python.org) (version >= 3.11.7)
2. [Streamlit](https://streamlit.io) (version >= 1.33.0)
3. [Plotly](https://plotly.com) (version >= 5.22.0)
4. [Pandas](https://pandas.pydata.org) (version >= 2.2.2)
5. [Scikit-Bio](https://scikit.bio) (version >= 0.6.0)

_Note: Some of these packages may be downloaded together with Streamlit, but you should always check the version._

It is recommended to set up virtual environment in Python for the installation. 

## Initial Setup ##
1. Clone this repository to your machine: `$ git clone git@github.com:HonzaHyl/VisualizationDashboard.git`
2. Switch your working directory to the cloned repository: `$ cd $PATH_TO_REPOSITORY`. 
3. Make sure you meet all requirements.
4. Run command: `$ streamlit run Overview.py`
5. App should open in your browser. 
6. In the app you can upload files from the test dataset in the repository to test the dashboard.

## Input files ##
### Currently supported input files are: ###
- merged_genefamilies_tables.tsv
- merged_metaphlan_bugs_lists.tsv
- merged_pathcoverage_tables.tsv
- merged_pathabundance_tables.tsv


These files should be generate by HUMAnN and MetaPhlAn algorithms. They must be .tsv format and must contain "genefamilies", "metaphlan", "pathcoverage" or "pathabundace" in their file names respectively. Example of each file can be found in the test dataset provided in this repository. 

- metadata.csv/.tsv (Needed for the alfa and beta diversity)

Metadata table can be created separately using this pattern:
| SampleName | SampleSource | SampleMaterial | SequencingKit |
| --- | ----------- |----------- | ----------- |
| Sample1 |  |  |  |
| Sample2 |  |  |  |
| Sample3 |  |  |  |
| ... |  |  |  |
| SampleN |  |  |  |

Dashboard was tested for metadata in this format. It should be possible to add more columns as grouping variables, but do this at your own risk.