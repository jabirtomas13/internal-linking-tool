import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
import time
import matplotlib.pyplot as plt

def internal_linking(keywords_input, sitemap):
    keywords = [keyword.strip() for keyword in keywords_input.split(",")]

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.41',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36',
    ]

    def sitemap_scrapping(sitemap):
        url_list = []
        try:
            headers = {'User-Agent': random.choice(user_agents)}
            response = requests.get(sitemap, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'xml')
            urls = soup.find_all('loc')
            url_list = [url.text for url in urls]
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to retrieve the sitemap: {e}")
            return []
        except Exception as e:
            st.error(f"Error parsing sitemap: {e}")
            return []
        return url_list

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

    def content_extraction(urls_list, keywords):
        occurrences = []
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
            except requests.exceptions.RequestException as e:
                st.warning(f"Failed to retrieve URL {url}: {e}")
                continue
            except Exception as e:
                st.warning(f"Error parsing content from {url}: {e}")
                continue

        return occurrences

    sitemap_urls = sitemap_scrapping(sitemap)
    if not sitemap_urls:
        st.error("No URLs found in the sitemap.")
        return pd.DataFrame()

    occurrences = content_extraction(sitemap_urls, keywords)

    if occurrences:
        occurrences_df = pd.DataFrame(occurrences)
        occurrences_df = occurrences_df[['url', 'occurrence_type', 'context', 'keyword', 'paragraph']]
    else:
        st.warning("No keyword occurrences found.")
        occurrences_df = pd.DataFrame(columns=['url', 'occurrence_type', 'context', 'keyword', 'paragraph'])

    return occurrences_df

def main():
    st.title("Internal Linking Analysis Tool (Text Input)")

    keywords_input = st.text_input(
        "Introduce las palabras clave que quieres buscar (separadas por comas):"
    )
    sitemap = st.text_input(
        "Introduce la URL del sitemap del sitio que quieres analizar:"
    )

    if st.button("Run Analysis"):
        if not keywords_input.strip() or not sitemap.strip():
            st.warning("Please provide both keywords and sitemap URL.")
            st.stop()

        with st.spinner("Analyzing..."):
            try:
                result_df = internal_linking(keywords_input, sitemap)

                if not result_df.empty:
                    st.subheader("Resultados de la Análisis")
                    st.dataframe(result_df)

                    csv_data = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Descargar resultados como CSV",
                        data=csv_data,
                        file_name="internal_linking_results.csv",
                        mime="text/csv"
                    )

                    st.subheader("Gráfico de ocurrencias de palabras clave")
                    keyword_counts = result_df['keyword'].value_counts()

                    fig, ax = plt.subplots(figsize=(10, 6))
                    keyword_counts.plot(kind='bar', color='skyblue', edgecolor='black', ax=ax)

                    ax.set_title('Ocurrencias de Palabras Clave', fontsize=16)
                    ax.set_xlabel('Palabras Clave', fontsize=12)
                    ax.set_ylabel('Cantidad de Ocurrencias', fontsize=12)

                    plt.xticks(rotation=45, ha='right')

                    for index, value in enumerate(keyword_counts):
                        ax.text(index, value + 0.5, str(value), ha='center', fontsize=10)

                    st.pyplot(fig)

            except Exception as e:
                st.error(f"Ha ocurrido un error inesperado: {e}")

if __name__ == "__main__":
    main()
