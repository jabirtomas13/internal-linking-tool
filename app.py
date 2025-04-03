import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
import time
import matplotlib.pyplot as plt

# Function to scrape sitemap URLs
def sitemap_scrapping(sitemap_url):
    url_list = []
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    try:
        headers = {'User-Agent': random.choice(user_agents)}
        response = requests.get(sitemap_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        urls = soup.find_all('loc')
        url_list = [url.text for url in urls]
    except Exception as e:
        st.error(f"Error retrieving sitemap: {e}")
    return url_list

# Function to extract keyword context
def extract_keyword_context(text, keyword):
    occurrences = []
    words = text.lower().split()
    for i, word in enumerate(words):
        if word == keyword.lower():
            before = words[i-1] if i > 0 else ""
            after = words[i+1] if i < len(words)-1 else ""
            context = f"{before} {keyword} {after}".strip()
            occurrences.append({
                'keyword': keyword,
                'context': context,
                'paragraph': text
            })
    return occurrences

# Function to extract content from URLs and find keywords
def content_extraction(urls_list, keywords):
    occurrences = []
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) rv:89.0 Gecko/20100101 Firefox/89.0'
    ]
    for url in urls_list:
        try:
            headers = {'User-Agent': random.choice(user_agents)}
            time.sleep(random.uniform(1, 3))
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            h1 = soup.find("h1").get_text().lower() if soup.find("h1") else ""
            paragraphs = [p.get_text() for p in soup.find_all('p')]

            for keyword in keywords:
                h1_occurrence = keyword.lower() in h1
                p_occurrence = any(keyword.lower() in p.lower() for p in paragraphs)

                if h1_occurrence:
                    h1_occurrences = extract_keyword_context(h1, keyword)
                    for occurrence in h1_occurrences:
                        occurrence['occurrence_type'] = 'H1'
                        occurrence['url'] = url
                    occurrences.extend(h1_occurrences)

                if p_occurrence:
                    for p in paragraphs:
                        if keyword.lower() in p.lower():
                            p_occurrences = extract_keyword_context(p, keyword)
                            for occurrence in p_occurrences:
                                occurrence['occurrence_type'] = 'Paragraph'
                                occurrence['url'] = url
                            occurrences.extend(p_occurrences)
        except Exception as e:
            st.warning(f"Failed to retrieve URL {url}: {e}")
    return occurrences

# Streamlit app starts here
st.title("Internal Linking Analysis Tool")

# Upload CSV file with keywords
uploaded_file = st.file_uploader("Upload a CSV file with keywords", type="csv")
if uploaded_file is not None:
    keywords_df = pd.read_csv(uploaded_file)
    if "keyword" not in keywords_df.columns:
        st.error("The uploaded CSV must have a column named 'keyword'.")
        st.stop()
    keywords_list = keywords_df["keyword"].tolist()
else:
    st.info("Please upload a CSV file with a column named 'keyword'.")
    st.stop()

# Input sitemap URL
sitemap_url = st.text_input("Enter the Sitemap URL:")
if not sitemap_url:
    st.info("Please enter the Sitemap URL.")
    st.stop()

# Run analysis when the user clicks the button
if st.button("Run Analysis"):
    with st.spinner("Analyzing..."):
        sitemap_urls = sitemap_scrapping(sitemap_url)
        if not sitemap_urls:
            st.error("No URLs found in the sitemap.")
            st.stop()

        # Perform content extraction and analysis
        occurrences_data = content_extraction(sitemap_urls, keywords_list)

        # Create DataFrame from occurrences data
        if occurrences_data:
            occurrences_df = pd.DataFrame(occurrences_data)
            occurrences_df = occurrences_df[['url', 'occurrence_type', 'context', 'keyword', 'paragraph']]

            # Display DataFrame in Streamlit app
            st.subheader("Analysis Results")
            st.dataframe(occurrences_df)

            # Download link for DataFrame as CSV
            csv_data = occurrences_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Results as CSV",
                data=csv_data,
                file_name="internal_linking_results.csv",
                mime="text/csv"
            )

            # Bar chart visualization of keyword occurrences
            st.subheader("Keyword Occurrences Bar Chart")
            keyword_counts = occurrences_df['keyword'].value_counts()

            fig, ax = plt.subplots(figsize=(10, 6))
            keyword_counts.plot(kind='bar', color='skyblue', edgecolor='black', ax=ax)

            ax.set_title('Keyword Occurrences', fontsize=16)
            ax.set_xlabel('Keywords', fontsize=12)
            ax.set_ylabel('Number of Occurrences', fontsize=12)

            plt.xticks(rotation=45, ha='right')

            # Add value labels above each bar
            for index, value in enumerate(keyword_counts):
                ax.text(index, value + 0.5, str(value), ha='center', fontsize=10)

            st.pyplot(fig)
        else:
            st.warning("No keyword occurrences found.")
