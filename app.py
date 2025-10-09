import time
import os
import feedparser
from flask import Flask, render_template, request
from newspaper import Article, ArticleException
import boto3
import json

# --- CONFIGURATION ---

# AWS Bedrock configuration
BEDROCK_REGION = os.environ.get("AWS_REGION", "us-east-1")
# Claude 3.5 model ID (update if you have a newer Claude 3.5 Bedrock model)
BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
# --- END CONFIGURATION ---

app = Flask(__name__)

def fetch_and_summarize(article_url):
    """
    Fetches the full text of an article and calls AWS Bedrock Claude 3.5 for summarization.
    """
    article_content = ""
    summary_text = "Failed to generate summary."

    # 1. Fetch full article content using newspaper3k
    try:
        article = Article(article_url)
        article.download()
        article.parse()
        article_content = article.text
    except ArticleException as e:
        print(f"Error fetching content for {article_url}: {e}")
        return summary_text

    # If content is too short or failed extraction
    if not article_content or len(article_content.split()) < 50:
        return "Article content was too short or unavailable for summarization."

    # 2. Prepare prompt for Claude 3.5
    prompt = f"\n\nHuman: Summarize the following article in two concise paragraphs, highlighting key arguments and main topic. Article content: {article_content}\n\nAssistant:"

    # 3. Call AWS Bedrock Claude 3.5
    try:
        bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=BEDROCK_REGION,
        )
        body = json.dumps({
            "messages": [
                {"role": "user", "content": f"Summarize the following article in two concise paragraphs, highlighting key arguments and main topic. Article content: {article_content}"},
            ],
            "max_tokens": 500,
            "temperature": 0.5,
            "anthropic_version": "bedrock-2023-05-31"
        })
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=body
        )
        result_stream = response.get("body")
        if hasattr(result_stream, "read"):
            result = result_stream.read()
        else:
            result = result_stream
        if isinstance(result, (bytes, bytearray)):
            result = result.decode()
        result_json = json.loads(result)
        summary_text = result_json.get("content", summary_text)
        return summary_text
    except Exception as e:
        print(f"Error calling Bedrock Model: {e}")
        return summary_text

def process_feeds(rss_urls_str, topics_str):
    """
    Parses RSS feeds, generates summaries, and filters results by topic.
    """
    all_results = []
    
    # Clean and normalize inputs
    rss_urls = [url.strip() for url in rss_urls_str.split('\n') if url.strip()]
    raw_topics = [t.strip() for t in topics_str.replace(',', '\n').split('\n') if t.strip()]
    search_topics = [t.lower() for t in raw_topics]

    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            print(f"Processing feed: {feed.feed.get('title', url)}")

            for entry in feed.entries:
                article_url = entry.link

                # Check if the article has already been processed (e.g., in a different feed)
                if any(res['url'] == article_url for res in all_results):
                    continue

                # Generate summary
                generated_summary = fetch_and_summarize(article_url)

                # Topic Matching (currently always True)
                is_match = True
                # If you want to filter by topic, uncomment and use the following:
                # summary_lower = generated_summary.lower()
                # for topic in search_topics:
                #     if topic in summary_lower:
                #         is_match = True
                #         break

                # Store result if match is found
                if is_match:
                    all_results.append({
                        'url': article_url,
                        'summary': generated_summary
                    })

        except Exception as e:
            print(f"An error occurred while processing feed {url}: {e}")
    return all_results

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles the main application route for displaying the form and results.
    """
    results = []
    
    # Example RSS Feeds for initial load
    default_rss_urls = (
        "https://feeds.npr.org/1001/rss.xml"
    )

    if request.method == 'POST':
        # Get data from the submitted form
        rss_urls_input = request.form.get('url_textarea', default_rss_urls)
        topics_input = request.form.get('topics_input', 'everything')
        
        # Process the data
        results = process_feeds(rss_urls_input, topics_input)
        
        # Pass inputs back to the template to persist user data
        return render_template(
            'index.html', 
            results=results, 
            rss_urls=rss_urls_input, 
            topics=topics_input
        )
    
    # Initial GET request
    return render_template(
        'index.html', 
        results=[], 
        rss_urls=default_rss_urls, 
        topics='everything'
    )

if __name__ == '__main__':
    # Add a logger for firestore/auth if this were a production app
    # setLogLevel('Debug') 
    app.run(debug=True)
