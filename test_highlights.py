# -*- coding: utf-8 -*-
from services import NewsProcessor

# Test the updated highlights extraction
processor = NewsProcessor()

# Clear existing articles and process fresh ones
print("Clearing existing articles...")
processor.clear_all_articles()

print("Processing feeds with updated highlights extraction...")
result = processor.process_feeds()
print(f"Result: {result}")