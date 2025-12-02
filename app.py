from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from dotenv import load_dotenv
import os
import threading
from sqlalchemy.orm import joinedload
from database import SessionLocal, Feed, Topic, Article, Category
from services import NewsProcessor
from scheduler import init_scheduler, rss_scheduler
from output_generators import OutputGenerator
import pytz
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

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
        ).order_by(Article.published_date.desc()).limit(20).all()
        
        categories = db.query(Category).filter(Category.active == True).all()
        latest_article = db.query(Article).order_by(Article.created_at.desc()).first()
        last_refresh = None
        if latest_article and latest_article.created_at:
            pst = pytz.timezone('US/Pacific')
            last_refresh = latest_article.created_at.replace(tzinfo=pytz.UTC).astimezone(pst)
        
        return render_template('dashboard.html', 
                             articles=articles, 
                             categories=categories,
                             last_refresh=last_refresh)
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

@app.route('/add_feed', methods=['POST'])
def add_feed():
    name = request.form['name']
    url = request.form['url']
    
    db = SessionLocal()
    try:
        feed = Feed(name=name, url=url)
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

if __name__ == '__main__':
    app.run(debug=True, threaded=True)