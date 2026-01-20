-- Clear existing data
DELETE FROM topics;
DELETE FROM feeds;
DELETE FROM categories;
DELETE FROM system_config;
DELETE FROM articles;

-- Insert Categories
INSERT INTO categories (id, name, description, color, active) VALUES
(1, 'Financial System', 'Banking, Federal Reserve, monetary policy', '#1e3a8a', 1),
(2, 'Economic Indicators', 'GDP, employment, inflation, economic data', '#059669', 1),
(3, 'Markets', 'Stock markets, bonds, commodities', '#dc2626', 1),
(4, 'Technology', 'Tech companies, innovation, digital transformation', '#7c3aed', 1),
(5, 'Global Economy', 'International trade, global markets', '#ea580c', 1);

-- Insert RSS Feeds
INSERT INTO feeds (id, name, url, active, access_key) VALUES
(1, 'Federal Reserve News', 'https://www.federalreserve.gov/feeds/press_all.xml', 1, NULL),
(2, 'Reuters Business', 'https://feeds.reuters.com/reuters/businessNews', 1, NULL),
(3, 'Reuters Economy', 'https://feeds.reuters.com/reuters/economyNews', 1, NULL),
(4, 'Bloomberg Markets', 'https://feeds.bloomberg.com/markets/news.rss', 1, NULL),
(5, 'CNBC Top News', 'https://www.cnbc.com/id/100003114/device/rss/rss.html', 1, NULL),
(6, 'Financial Times', 'https://www.ft.com/?format=rss', 1, NULL),
(7, 'Wall Street Journal', 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml', 1, NULL);

-- Insert Topics
INSERT INTO topics (id, name, keywords, category_id, active) VALUES
(1, 'Federal Reserve Policy', 'federal reserve, fed, monetary policy, interest rates, FOMC, Jerome Powell, central bank', 1, 1),
(2, 'Banking Sector', 'banks, banking, financial institutions, JPMorgan, Bank of America, Wells Fargo, credit', 1, 1),
(3, 'Inflation', 'inflation, CPI, consumer prices, price increases, deflation, PCE', 2, 1),
(4, 'Employment', 'jobs, employment, unemployment, labor market, payrolls, wages, hiring', 2, 1),
(5, 'GDP & Growth', 'GDP, economic growth, recession, expansion, productivity', 2, 1),
(6, 'Stock Markets', 'stocks, S&P 500, Dow Jones, Nasdaq, equity, shares, market rally, market decline', 3, 1),
(7, 'Bond Markets', 'bonds, treasury, yields, fixed income, debt securities', 3, 1),
(8, 'Fintech', 'fintech, digital banking, cryptocurrency, blockchain, payment technology', 4, 1),
(9, 'Global Trade', 'trade, tariffs, exports, imports, trade war, international commerce', 5, 1);

-- Insert System Configuration
INSERT INTO system_config (key, value, description) VALUES
('llm_provider', 'bedrock', 'LLM provider (bedrock/openai)'),
('llm_model', 'anthropic.claude-3-haiku-20240307-v1:0', 'Model ID'),
('llm_api_key', '', 'API key if needed'),
('llm_api_base', '', 'API base URL if needed');
