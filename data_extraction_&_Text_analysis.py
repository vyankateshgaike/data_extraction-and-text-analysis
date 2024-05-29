# Import necessary libraries
import requests
import pandas as pd 
import os
import re
from bs4 import BeautifulSoup
import nltk
from nltk import word_tokenize, sent_tokenize
#********************************************************************************************************#

# Read the input data from an Excel file
data_frame = pd.read_excel("input.xlsx")

for index, row in data_frame.iterrows():
    url_id = row['URL_ID']
    url = row['URL']
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        html_content = response.content
        corpus=[]
        soup = BeautifulSoup(html_content, 'html.parser')
        
        title = soup.find('h1').text.strip()
        
        article_content_div = soup.find('div', class_='td-post-content')

        article_content = ""

        if article_content_div:
            paragraphs = article_content_div.find_all(['p', 'li', 'ul', 'ol'])
            
            article_content = '\n'.join([paragraph.get_text(strip=True) for paragraph in paragraphs if paragraph.get_text(strip=True)])
        
        os.makedirs('extracted1',exist_ok=True)
        with open(f"extracted1\{url_id}.txt", "w", encoding="utf-8") as file:
            file.write(title + "\n\n")
            file.write(article_content)
            
            
            
    except requests.exceptions.HTTPError as error:
        print(f"Error for URL_ID {url_id}: {error}")
        continue
#********************************************************************************************************#
#function to load stopwords from text files
def load_stopwords(stopword_dict):
    stopwords = set()
    for file in os.listdir(stopword_dict):
        if file.endswith('.txt'):
            with open(os.path.join(stopword_dict, file), 'r', encoding='latin1') as f:
                stopwords.update(f.read().splitlines())
    return stopwords

# Load stopwords, positive words, and negative words
stopword_dir = "StopWords"
stop_words = load_stopwords(stopword_dir)

with open('MasterDictionary/positive-words.txt', 'r') as file:
    positive_list = [line.strip() for line in file.readlines()]

with open('MasterDictionary/negative-words.txt', 'r') as file:
    
    negative_list = [line.strip() for line in file.readlines()]
#********************************************************************************************************#   
    
    
#function to count syllables in a word(easy way)
# from textstat.textstat import textstatistics, legacy_round
# def syllable_count(word):
    # return textstatistics().syllable_count(word)
    
    

def count_syllables(word):
    vowels = "aeiouy"
    count = 0
    word = word.lower()
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith('e'):
        count -= 1
    if count == 0:
        count += 1 
    return count

#function to analyze text content
def analyze_text(text, stop_words, positive_list, negative_list):
    sentences = sent_tokenize(text)
    words = nltk.word_tokenize(text)
    
    # filtering the input text
    word_clean = [word for word in words if word.isalpha() and word.lower() not in stop_words]
    
    #Calculating various metrics
    word_count = len(word_clean)
    sentences_count = len(sentences)
    complex_wordcount = sum(1 for word in word_clean if count_syllables(word) >= 3)
    syllables = sum(count_syllables(word) for word in word_clean)
    personal_pronouns = len(re.findall(r'\b(?:I|we|my|ours|us)(?!US\b)\b', text, flags=re.IGNORECASE))
    positive_words = len([word for word in word_clean if word.lower() in positive_list])
    negative_words = len([word for word in word_clean if word.lower() in negative_list])
    avg_sent_length = word_count / sentences_count if sentences_count else 0
    per_complex_word = (complex_wordcount / word_count * 100) if word_count else 0
    fog_index = 0.4 * (avg_sent_length + per_complex_word)
    avg_word_length = sum(len(word) for word in word_clean) / word_count if word_count else 0
    avg_words_per_sentence = word_count / sentences_count if sentences_count else 0
    polarity_score = (positive_words - negative_words) / ((positive_words + negative_words) + 0.000001)
    sub_score = (positive_words + negative_words) / ((word_count) + 0.000001)

    return {
        'POSITIVE SCORE': positive_words,
        'NEGATIVE SCORE': negative_words,
        'POLARITY SCORE': polarity_score,
        'SUBJECTIVITY SCORE': sub_score,
        'AVG SENTENCE LENGTH': avg_sent_length,
        'PERCENTAGE OF COMPLEX WORDS': per_complex_word,
        'FOG INDEX': fog_index,
        'AVG NUMBER OF WORDS PER SENTENCE': avg_words_per_sentence,
        'COMPLEX WORD COUNT': complex_wordcount,
        'WORD COUNT': word_count,
        'SYLLABLE PER WORD': syllables / word_count if word_count else 0,
        'PERSONAL PRONOUNS': personal_pronouns,
        'AVG WORD LENGTH': avg_word_length
    }
    
    
#********************************************************************************************************#

# Analyze text content for each URL_ID
results = []

for index, row in data_frame.iterrows():
    url_id = row['URL_ID']
    try:
        # Read text content from the extracted file
        with open(f"extracted1/{url_id}.txt", "r", encoding="utf-8") as file:
            
            text = file.read()
            
            analysis_results = analyze_text(text, stop_words, positive_list, negative_list)
    except FileNotFoundError:
        
        print(f"Text file for URL_ID {url_id} not found")
        #setting placeholder values.
        analysis_results = {
            'POSITIVE SCORE': 0,
            'NEGATIVE SCORE': 0,
            'POLARITY SCORE': 0,
            'SUBJECTIVITY SCORE': 0,
            'AVG SENTENCE LENGTH': 0,
            'PERCENTAGE OF COMPLEX WORDS': 0,
            'FOG INDEX': 0,
            'AVG NUMBER OF WORDS PER SENTENCE': 0,
            'COMPLEX WORD COUNT': 0,
            'WORD COUNT': 0,
            'SYLLABLE PER WORD': 0,
            'PERSONAL PRONOUNS': 0,
            'AVG WORD LENGTH': 0
        }
    except Exception as e:
        print(f"Error processing URL_ID {url_id}: {e}")
        # Set placeholder values for analysis results if error occurs
        analysis_results = {
            'POSITIVE SCORE': None,
            'NEGATIVE SCORE': None,
            'POLARITY SCORE': None,
            'SUBJECTIVITY SCORE': None,
            'AVG SENTENCE LENGTH': None,
            'PERCENTAGE OF COMPLEX WORDS': None,
            'FOG INDEX': None,
            'AVG NUMBER OF WORDS PER SENTENCE': None,
            'COMPLEX WORD COUNT': None,
            'WORD COUNT': None,
            'SYLLABLE PER WORD': None,
            'PERSONAL PRONOUNS': None,
            'AVG WORD LENGTH': None
        }
    
    #append the Results
    results.append({**row.to_dict(), **analysis_results})

# Create a DataFrame 
results_df = pd.DataFrame(results)
results_df.to_excel("Output Data Structure.xlsx", index=False)
