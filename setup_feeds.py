from database import get_db, Feed, Category, Topic

def setup_common_feeds():
    db = get_db()
    try:
        # Common news feeds
        feeds = [
            ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml"),
            ("Reuters Top News", "https://feeds.reuters.com/reuters/topNews"),
            ("CNN Top Stories", "http://rss.cnn.com/rss/edition.rss"),
            ("AP News", "https://feeds.apnews.com/rss/apf-topnews"),
            ("NPR News", "https://feeds.npr.org/1001/rss.xml")
        ]
        
        for name, url in feeds:
            existing = db.query(Feed).filter(Feed.url == url).first()
            if not existing:
                feed = Feed(name=name, url=url, active=True)
                db.add(feed)
                print(f"Added feed: {name}")
        
        db.commit()
        print("Feed setup complete!")
        
    finally:
        db.close()

if __name__ == "__main__":
    setup_common_feeds()