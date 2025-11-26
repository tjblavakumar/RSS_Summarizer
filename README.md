# Daily News AI Assistant

A locally deployable news aggregation system that uses Google Gemini AI to analyze and summarize articles based on user-defined topics.

## Features

- **RSS Feed Management**: Add and manage multiple RSS feeds
- **Topic-Based Filtering**: Define topics with keywords for AI-powered relevance scoring
- **Smart Content Extraction**: Automatically scrapes full articles when RSS descriptions are too short
- **AI Analysis**: Uses Google Gemini 1.5 Flash to analyze relevance and generate summaries
- **Rate Limiting**: Built-in delays to respect Google Gemini Free Tier limits
- **Background Processing**: Non-blocking news updates using threading

## Setup Instructions

### 1. Get Google AI Studio API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### 2. Installation

```bash
# Clone or download the project
cd daily-news-ai

# Install dependencies
pip install -r requirements.txt

# Create environment file
copy .env.example .env

# Edit .env and add your API key
GOOGLE_API_KEY=your_actual_api_key_here
```

### 3. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### 1. Add RSS Feeds
- Go to Admin panel
- Add RSS feed URLs (e.g., `https://feeds.bbci.co.uk/news/rss.xml`)

### 2. Define Topics
- Create topics with relevant keywords
- Example: Topic "Technology" with keywords "AI, machine learning, software, tech"

### 3. Refresh News
- Click "Refresh News" to start background processing
- The system will fetch, analyze, and store relevant articles (score > 75)

## Technical Details

### Rate Limiting
- 2-second delay between AI requests to avoid 429 errors
- Uses `gemini-1.5-flash` model (most efficient for free tier)

### Content Processing
- RSS descriptions < 500 chars trigger full article scraping
- Removes script/style/nav tags to save tokens
- Limits content to 3000 chars for AI analysis

### Database
- SQLite with thread-safe configuration
- Stores feeds, topics, and analyzed articles
- Prevents duplicate article processing

## File Structure

```
daily-news-ai/
├── app.py              # Flask application and routes
├── database.py         # SQLAlchemy models and setup
├── services.py         # RSS fetching and AI analysis
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
├── README.md          # This file
└── templates/
    ├── base.html      # Bootstrap base template
    ├── dashboard.html # Article display
    └── admin.html     # Feed/topic management
```

## Troubleshooting

### API Rate Limits
If you encounter 429 errors, the system will log them and continue processing other articles.

### No Articles Appearing
1. Check that feeds are active and valid
2. Ensure topics have relevant keywords
3. Verify API key is correct
4. Check console logs for errors

### Database Issues
Delete `news.db` file to reset the database if needed.