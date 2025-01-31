# map-forum-discussions

This repository is part of the internship at RNDR Studio, as part of the project **Unfolding the Creative Coding Landscape**. 
This repo focuses specifically on the research question *'What is talked about in the largest creative coding community forums?'*

In general, there are two parts of the repo - organised into data collection and data analysis. 

## Data Collection
This folder includes the scripts used to collect the forum post data from the online forum platforms. Here, the platforms included are Processing, Cinder, and OPENRNDR. Here are the scripts ordered by usage:
1. **extract-topic-id**: used to extract the individual topic id(s) of the posts
2. **extract-post-{platform}**: using the extracted topic id(s), this script collects the forum post data. Specific to OPENRNDR, this used [discourse-archive](https://github.com/jamesob/discourse-archive)
3. **combine-posts-to-csv**: the extracted individual posts (in JSON format) are combined into a csv file

## Data Analysis
This folder includes the notebooks used to analyse the collected data. This is further divided into two folders. The **test-data-analysis** consist of notebooks that used the test data (OPENRNDR) for initial analysis and planning of methods. The **full-analysis** consist of notebooks for the full analysis of the data across the different platforms. This includes different iterations of the methods and the final version, with its ouput used in the visual representation of the analysis.
### test-data-analysis
1. **test_eda**: exploratory data analysis with test data
2. **test_gsdmm_and_sentiment_analysis**: topic modeling with gensim (LDA) and additional sentiment analysis. also includes preprocessing for file used in notebooks: *'test_bertopic'* and *'test_umap_hdbscan'*
3. **test_network_analysis**: creation of network graph based on user replies 
4. **test_bertopic**: use of BerTOPIC for representation (including generating UMAP embeddings and clustering with HDBSCAN)
5. **test_umap_hdsbcan**: sentence transformers for embeddings ('BAAI/bge-base-en'), UMAP and HDBSCAN, fine-tuning
## full-analysis
1. **full_text_analysis_iteration_1**: sentence tranformers (all-MiniLM), UMAP and HDBSCAN, BerTOPIC for representation
2. **full_text_analysis_iteration_2**: minimal text cleaning = removing code content and extra whitespace, stripping HTML tags, sentence transformer (paraphrase-MiniLM-L6-v2), UMAP and HDBSCAN
3. **full_text_analysis_final**: (FINAL VERSION!) more text cleaning: remove HTML tags, code content, remove top and bottom 10% based on word count (too short or too long), parsing (taking only nouns and proper nouns into account), adding custom stop words, TF-IDF vectorizer, UMAP and HDBSCAN, extracting top keywords per cluster, label representation of cluster with LLM, cluster level analysis of users 
4. **llm_representation**: notebook run on GoogleColab (due to personal memory issues), for cluster label representation with Llama2. Output of this notebook was used for the *'full_text_analysis_final'* notebook
