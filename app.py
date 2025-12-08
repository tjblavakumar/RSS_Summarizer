from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from dotenv import load_dotenv
import os
import threading
from sqlalchemy.orm import joinedload
from database import SessionLocal, Feed, Topic, Article, Category, SystemConfig
from sqlalchemy import func
from collections import Counter
from services import NewsProcessor
from scheduler import init_scheduler, rss_scheduler
from output_generators import OutputGenerator
import pytz
from datetime import datetime

load_dotenv()

import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

def slugify(s):
    s = str(s).lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s

app.jinja_env.filters['slugify'] = slugify

# Initialize news processor (no API key needed for AWS Bedrock)
news_processor = NewsProcessor()
output_generator = OutputGenerator()

# Initialize scheduler
init_scheduler()

@app.route('/')
def dashboard():
    db = SessionLocal()
    try:
        articles = db.query(Article).options(
            joinedload(Article.topic).joinedload(Topic.category),
            joinedload(Article.feed)
        ).order_by(Article.relevancy_score.desc(), Article.published_date.desc()).limit(200).all()
        
        categories = db.query(Category).filter(Category.active == True).all()
        
        total_articles = db.query(Article).count()
        
        latest_article = db.query(Article).order_by(Article.created_at.desc()).first()
        last_refresh = None
        if latest_article and latest_article.created_at:
            pst = pytz.timezone('US/Pacific')
            last_refresh = latest_article.created_at.replace(tzinfo=pytz.UTC).astimezone(pst)
        
        # Calculate stats from the actually fetched articles to ensure links match content
        category_names = [a.category_name for a in articles if a.category_name]
        category_stats = dict(Counter(category_names))
        
        return render_template('dashboard.html', 
                             articles=articles, 
                             categories=categories,
                             last_refresh=last_refresh,
                             category_stats=category_stats,
                             total_articles=total_articles)
    finally:
        db.close()

@app.route('/admin')
def admin():
    return redirect(url_for('admin_feeds'))

@app.route('/admin/feeds')
def admin_feeds():
    db = SessionLocal()
    try:
        feeds = db.query(Feed).all()
        return render_template('admin_feeds.html', feeds=feeds, active_tab='feeds')
    finally:
        db.close()

@app.route('/admin/topics')
def admin_topics():
    db = SessionLocal()
    try:
        topics = db.query(Topic).options(joinedload(Topic.category)).all()
        categories = db.query(Category).filter(Category.active == True).all()
        return render_template('admin_topics.html', topics=topics, categories=categories, active_tab='topics')
    finally:
        db.close()

@app.route('/admin/categories')
def admin_categories():
    db = SessionLocal()
    try:
        categories = db.query(Category).all()
        return render_template('admin_categories.html', categories=categories, active_tab='categories')
    finally:
        db.close()

@app.route('/admin/llm')
def admin_llm():
    db = SessionLocal()
    try:
        config_items = db.query(SystemConfig).all()
        config = {item.key: item.value for item in config_items}
        return render_template('admin_llm.html', config=config, active_tab='llm')
    finally:
        db.close()

@app.route('/update_llm_config', methods=['POST'])
def update_llm_config():
    db = SessionLocal()
    try:
        config_keys = ['llm_provider', 'llm_api_key', 'llm_model', 'llm_api_base']
        for key in config_keys:
            value = request.form.get(key, '')
            config_item = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if config_item:
                config_item.value = value
            else:
                config_item = SystemConfig(key=key, value=value)
                db.add(config_item)
        db.commit()
        flash('LLM configuration updated successfully')
    finally:
        db.close()
    return redirect(url_for('admin_llm'))

@app.route('/add_feed', methods=['POST'])
def add_feed():
    name = request.form['name']
    url = request.form['url']
    access_key = request.form.get('access_key')
    
    db = SessionLocal()
    try:
        feed = Feed(name=name, url=url, access_key=access_key)
        db.add(feed)
        db.commit()
        flash('Feed added successfully')
    finally:
        db.close()
    return redirect(url_for('admin_feeds'))

@app.route('/add_topic', methods=['POST'])
def add_topic():
    name = request.form['name']
    keywords = request.form['keywords']
    category_id = request.form.get('category_id')
    
    db = SessionLocal()
    try:
        topic = Topic(name=name, keywords=keywords, category_id=category_id if category_id else None)
        db.add(topic)
        db.commit()
        flash('Topic added successfully')
    finally:
        db.close()
    return redirect(url_for('admin_topics'))

@app.route('/add_category', methods=['POST'])
def add_category():
    name = request.form['name']
    description = request.form.get('description', '')
    color = request.form.get('color', '#007bff')
    
    db = SessionLocal()
    try:
        category = Category(name=name, description=description, color=color)
        db.add(category)
        db.commit()
        flash('Category added successfully')
    finally:
        db.close()
    return redirect(url_for('admin_categories'))

@app.route('/edit_topic/<int:topic_id>', methods=['POST'])
def edit_topic(topic_id):
    name = request.form['name']
    keywords = request.form['keywords']
    category_id = request.form.get('category_id')
    
    db = SessionLocal()
    try:
        topic = db.get(Topic, topic_id)
        if topic:
            topic.name = name
            topic.keywords = keywords
            topic.category_id = category_id if category_id else None
            db.commit()
            flash('Topic updated successfully')
    finally:
        db.close()
    return redirect(url_for('admin_topics'))

@app.route('/edit_category/<int:category_id>', methods=['POST'])
def edit_category(category_id):
    name = request.form['name']
    description = request.form.get('description', '')
    color = request.form.get('color', '#007bff')
    
    db = SessionLocal()
    try:
        category = db.get(Category, category_id)
        if category:
            category.name = name
            category.description = description
            category.color = color
            db.commit()
            flash('Category updated successfully')
    finally:
        db.close()
    return redirect(url_for('admin_categories'))

@app.route('/refresh_news')
def refresh_news():
    def background_refresh():
        result = news_processor.process_feeds()
        print(f"Background refresh result: {result}")
    
    if not news_processor.processing:
        thread = threading.Thread(target=background_refresh)
        thread.daemon = True
        thread.start()
        return jsonify({"status": "started", "message": "News refresh started in background"})
    else:
        return jsonify({"status": "busy", "message": "Already processing"})

@app.route('/clear_all_news')
def clear_all_news():
    count = news_processor.clear_all_articles()
    return jsonify({"status": "success", "message": f"Cleared {count} articles", "count": count})

@app.route('/toggle_feed/<int:feed_id>')
def toggle_feed(feed_id):
    db = SessionLocal()
    try:
        feed = db.get(Feed, feed_id)
        if feed:
            feed.active = not feed.active
            db.commit()
    finally:
        db.close()
    return redirect(url_for('admin_feeds'))

@app.route('/toggle_topic/<int:topic_id>')
def toggle_topic(topic_id):
    db = SessionLocal()
    try:
        topic = db.get(Topic, topic_id)
        if topic:
            topic.active = not topic.active
            db.commit()
    finally:
        db.close()
    return redirect(url_for('admin_topics'))

@app.route('/toggle_category/<int:category_id>')
def toggle_category(category_id):
    db = SessionLocal()
    try:
        category = db.get(Category, category_id)
        if category:
            category.active = not category.active
            db.commit()
    finally:
        db.close()
    return redirect(url_for('admin_categories'))

@app.route('/delete_feed/<int:feed_id>')
def delete_feed(feed_id):
    db = SessionLocal()
    try:
        feed = db.get(Feed, feed_id)
        if feed:
            db.delete(feed)
            db.commit()
            flash('Feed deleted successfully')
    finally:
        db.close()
    return redirect(url_for('admin_feeds'))

@app.route('/delete_topic/<int:topic_id>')
def delete_topic(topic_id):
    db = SessionLocal()
    try:
        topic = db.get(Topic, topic_id)
        if topic:
            db.delete(topic)
            db.commit()
            flash('Topic deleted successfully')
    finally:
        db.close()
    return redirect(url_for('admin_topics'))

@app.route('/delete_category/<int:category_id>')
def delete_category(category_id):
    db = SessionLocal()
    try:
        category = db.get(Category, category_id)
        if category:
            db.delete(category)
            db.commit()
            flash('Category deleted successfully')
    finally:
        db.close()
    return redirect(url_for('admin_categories'))

@app.route('/admin/scheduler')
def admin_scheduler():
    next_run = rss_scheduler.get_next_run_time()
    return render_template('admin_scheduler.html', 
                         next_run=next_run, 
                         is_running=rss_scheduler.is_running,
                         active_tab='scheduler')

@app.route('/update_schedule', methods=['POST'])
def update_schedule():
    hour = int(request.form['hour'])
    minute = int(request.form['minute'])
    
    rss_scheduler.schedule_daily(hour=hour, minute=minute)
    flash(f'Schedule updated to {hour:02d}:{minute:02d} daily')
    return redirect(url_for('admin_scheduler'))

@app.route('/run_scheduler_now')
def run_scheduler_now():
    print("=== Run Now button clicked ===")
    app.logger.info("Run Now button clicked")
    
    if not news_processor.processing:
        print("=== Starting RSS processing ===")
        result = news_processor.process_feeds()
        print(f"=== RSS processing result: {result} ===")
        flash(f'RSS summary completed: {result}')
    else:
        print("=== RSS processing already in progress ===")
        flash('RSS summary already in progress')
    return redirect(url_for('admin_scheduler'))

@app.route('/generate_markdown')
def generate_markdown():
    try:
        filename = output_generator.generate_markdown()
        return send_file(filename, as_attachment=True, download_name=f"rss_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    except Exception as e:
        flash(f'Error generating markdown: {e}')
        return redirect(url_for('dashboard'))

@app.route('/generate_html')
def generate_html():
    try:
        filename = output_generator.generate_html()
        return send_file(filename, as_attachment=True, download_name=f"rss_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    except Exception as e:
        flash(f'Error generating HTML: {e}')
        return redirect(url_for('dashboard'))

@app.route('/update_summary/<int:article_id>', methods=['POST'])
def update_summary(article_id):
    data = request.json
    new_summary = data.get('summary')
    
    if not new_summary:
        return jsonify({"success": False, "message": "No summary provided"}), 400
        
    db = SessionLocal()
    try:
        article = db.get(Article, article_id)
        if article:
            article.summary = new_summary
            db.commit()
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Article not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()

@app.route('/rate_article/<int:article_id>', methods=['POST'])
def rate_article(article_id):
    data = request.json
    feedback = data.get('feedback')  # 1 for like, -1 for dislike, 0 for neutral
    
    if feedback not in [1, -1, 0]:
        return jsonify({"success": False, "message": "Invalid feedback value"}), 400
        
    db = SessionLocal()
    try:
        article = db.get(Article, article_id)
        if article:
            article.user_feedback = feedback
            db.commit()
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Article not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)