from database import SessionLocal, Feed, Topic, Category, SystemConfig
from datetime import datetime

def populate_database(force=False):
    db = SessionLocal()
    try:
        # Check if database already has data
        if not force:
            existing_categories = db.query(Category).count()
            if existing_categories > 0:
                print("Database already populated. Skipping initialization.")
                return
        
        # Clear existing data if force=True
        if force:
            print("Clearing existing data...")
            db.query(Topic).delete()
            db.query(Feed).delete()
            db.query(Category).delete()
            db.query(SystemConfig).delete()
            db.commit()
        
        # Add Categories
        print("Adding categories...")
        categories = [
            Category(name="Financial System", description="Banking, Federal Reserve, monetary policy", color="#1e3a8a"),
            Category(name="Economic Indicators", description="GDP, employment, inflation, economic data", color="#059669"),
            Category(name="Markets", description="Stock markets, bonds, commodities", color="#dc2626"),
            Category(name="Technology", description="Tech companies, innovation, digital transformation", color="#7c3aed"),
            Category(name="Global Economy", description="International trade, global markets", color="#ea580c"),
        ]
        for cat in categories:
            db.add(cat)
        db.commit()
        
        # Get category IDs
        financial_cat = db.query(Category).filter(Category.name == "Financial System").first()
        economic_cat = db.query(Category).filter(Category.name == "Economic Indicators").first()
        markets_cat = db.query(Category).filter(Category.name == "Markets").first()
        tech_cat = db.query(Category).filter(Category.name == "Technology").first()
        global_cat = db.query(Category).filter(Category.name == "Global Economy").first()
        
        # Add RSS Feeds
        print("Adding RSS feeds...")
        feeds = [
            Feed(name="Federal Reserve News", url="https://www.federalreserve.gov/feeds/press_all.xml", active=True),
            Feed(name="Reuters Business", url="https://feeds.reuters.com/reuters/businessNews", active=True),
            Feed(name="Reuters Economy", url="https://feeds.reuters.com/reuters/economyNews", active=True),
            Feed(name="Bloomberg Markets", url="https://feeds.bloomberg.com/markets/news.rss", active=True),
            Feed(name="CNBC Top News", url="https://www.cnbc.com/id/100003114/device/rss/rss.html", active=True),
            Feed(name="Financial Times", url="https://www.ft.com/?format=rss", active=True),
            Feed(name="Wall Street Journal", url="https://feeds.a.dj.com/rss/RSSMarketsMain.xml", active=True),
        ]
        for feed in feeds:
            db.add(feed)
        db.commit()
        
        # Add Topics
        print("Adding topics...")
        topics = [
            Topic(name="Federal Reserve Policy", 
                  keywords="federal reserve, fed, monetary policy, interest rates, FOMC, Jerome Powell, central bank",
                  category_id=financial_cat.id, active=True),
            Topic(name="Banking Sector", 
                  keywords="banks, banking, financial institutions, JPMorgan, Bank of America, Wells Fargo, credit",
                  category_id=financial_cat.id, active=True),
            Topic(name="Inflation", 
                  keywords="inflation, CPI, consumer prices, price increases, deflation, PCE",
                  category_id=economic_cat.id, active=True),
            Topic(name="Employment", 
                  keywords="jobs, employment, unemployment, labor market, payrolls, wages, hiring",
                  category_id=economic_cat.id, active=True),
            Topic(name="GDP & Growth", 
                  keywords="GDP, economic growth, recession, expansion, productivity",
                  category_id=economic_cat.id, active=True),
            Topic(name="Stock Markets", 
                  keywords="stocks, S&P 500, Dow Jones, Nasdaq, equity, shares, market rally, market decline",
                  category_id=markets_cat.id, active=True),
            Topic(name="Bond Markets", 
                  keywords="bonds, treasury, yields, fixed income, debt securities",
                  category_id=markets_cat.id, active=True),
            Topic(name="Fintech", 
                  keywords="fintech, digital banking, cryptocurrency, blockchain, payment technology",
                  category_id=tech_cat.id, active=True),
            Topic(name="Global Trade", 
                  keywords="trade, tariffs, exports, imports, trade war, international commerce",
                  category_id=global_cat.id, active=True),
        ]
        for topic in topics:
            db.add(topic)
        db.commit()
        
        # Add System Config (LLM settings)
        print("Adding system configuration...")
        configs = [
            SystemConfig(key="llm_provider", value="bedrock", description="LLM provider (bedrock/openai)"),
            SystemConfig(key="llm_model", value="anthropic.claude-3-haiku-20240307-v1:0", description="Model ID"),
            SystemConfig(key="llm_api_key", value="", description="API key if needed"),
            SystemConfig(key="llm_api_base", value="", description="API base URL if needed"),
        ]
        for config in configs:
            db.add(config)
        db.commit()
        
        print("\nDatabase populated successfully!")
        print(f"  - {len(categories)} categories")
        print(f"  - {len(feeds)} RSS feeds")
        print(f"  - {len(topics)} topics")
        print(f"  - {len(configs)} system configs")
        
    except Exception as e:
        print(f"Error populating database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    force = '--force' in sys.argv or '-f' in sys.argv
    populate_database(force=force)
