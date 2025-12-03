import os
from datetime import datetime, date
from database import get_db, Article, Category
from sqlalchemy import and_

class OutputGenerator:
    def __init__(self):
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_markdown(self, start_date=None, end_date=None):
        db = get_db()
        try:
            query = db.query(Article)
            
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                query = query.filter(and_(
                    Article.published_date >= start_dt,
                    Article.published_date <= end_dt
                ))
            
            articles = query.order_by(Article.published_date.desc()).all()
            
            content = f"# RSS News Summary\n\n"
            content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            if start_date and end_date:
                content += f"Date Range: {start_date} to {end_date}\n\n"
            content += f"Total Articles: {len(articles)}\n\n"
            
            for article in articles:
                content += f"### [{article.title}]({article.url})\n\n"
                content += f"**Author:** {article.author or 'Unknown'} | **Published:** {article.published_date.strftime('%Y-%m-%d %H:%M')}\n\n"
                
                if article.summary:
                    content += f"{article.summary}\n\n"
                
                if hasattr(article, 'category_name') and article.category_name:
                    content += f"**Category:** {article.category_name} | [Read More]({article.url})\n\n"
                
                content += "---\n\n"
            
            filename = f"{self.output_dir}/rss_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return filename
        finally:
            db.close()
    
    def generate_html(self, start_date=None, end_date=None):
        db = get_db()
        try:
            query = db.query(Article)
            
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                query = query.filter(and_(
                    Article.published_date >= start_dt,
                    Article.published_date <= end_dt
                ))
            
            articles = query.order_by(Article.published_date.desc()).all()
            
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSS News Summary</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; line-height: 1.6; color: #333; }}
        .header {{ border-bottom: 2px solid #2c3e50; padding-bottom: 20px; margin-bottom: 30px; }}
        .article {{ background: #ffffff; padding: 25px; margin-bottom: 25px; border-bottom: 1px solid #dee2e6; }}
        .article-title {{ font-size: 1.2em; font-weight: 600; margin: 0 0 10px 0; }}
        .article-title a {{ color: #0d6efd; text-decoration: none; }}
        .article-title a:hover {{ text-decoration: underline; }}
        .meta {{ color: #666; font-size: 0.9em; margin-bottom: 15px; font-style: italic; }}
        .summary {{ margin-top: 15px; }}
        .summary ul {{ margin: 0; padding-left: 20px; }}
        .summary li {{ margin-bottom: 8px; color: #444; }}
        .category-row {{ display: flex; justify-content: space-between; align-items: center; margin-top: 10px; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.8em; color: white; }}
        .read-more-btn {{ padding: 4px 12px; border-radius: 4px; font-size: 0.8em; color: white; text-decoration: none; border: none; }}
        .read-more-btn:hover {{ opacity: 0.8; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>RSS News Summary</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        {f'<p>Date Range: {start_date} to {end_date}</p>' if start_date and end_date else ''}
        <p>Total Articles: {len(articles)}</p>
    </div>
"""
            
            for article in articles:
                html += f'    <div class="article">\n'
                html += f'        <h3 class="article-title"><a href="{article.url}" target="_blank">{article.title}</a></h3>\n'
                html += f'        <div class="meta">\n'
                html += f'            Author: {article.author or "Unknown"} | Published: {article.published_date.strftime("%Y-%m-%d %H:%M")}\n'
                html += f'        </div>\n'
                
                if article.summary:
                    summary_lines = article.summary.split('\n')
                    html += f'        <div class="summary">\n'
                    html += f'            <ul>\n'
                    for line in summary_lines:
                        if line.strip().startswith('•'):
                            html += f'                <li>{line.strip()[1:].strip()}</li>\n'
                    html += f'            </ul>\n'
                    html += f'        </div>\n'
                
                if hasattr(article, 'category_name') and article.category_name:
                    color = getattr(article, 'category_color', '#3498db')
                    html += f'        <div class="category-row">\n'
                    html += f'            <span class="badge" style="background-color: {color};">{article.category_name}</span>\n'
                    html += f'            <a href="{article.url}" target="_blank" class="read-more-btn" style="background-color: {color};">Read More</a>\n'
                    html += f'        </div>\n'
                
                html += f'    </div>\n'
            
            html += """</body>
</html>"""
            
            filename = f"{self.output_dir}/rss_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            
            return filename
        finally:
            db.close()