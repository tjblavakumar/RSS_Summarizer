import sqlite3

# Add system_config table
conn = sqlite3.connect('news.db')
cursor = conn.cursor()

try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_config (
        key VARCHAR(100) PRIMARY KEY,
        value TEXT,
        description TEXT
    )
    """)
    print("Created system_config table")
    
    # Insert default values if not exist
    default_configs = [
        ('llm_provider', 'bedrock', 'LLM Provider (bedrock, openai, anthropic)'),
        ('llm_api_key', '', 'API Key for the LLM provider'),
        ('llm_model', 'anthropic.claude-3-haiku-20240307-v1:0', 'Model ID to use'),
        ('llm_api_base', '', 'Optional API Base URL (for OpenAI compatible)')
    ]
    
    for key, value, desc in default_configs:
        try:
            cursor.execute("INSERT INTO system_config (key, value, description) VALUES (?, ?, ?)", (key, value, desc))
            print(f"Inserted default config: {key}")
        except sqlite3.IntegrityError:
            print(f"Config {key} already exists")
            
except Exception as e:
    print(f"Error creating table: {e}")

conn.commit()
conn.close()
print("Database migration complete")
