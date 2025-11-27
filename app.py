from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import os
import threading
from sqlalchemy.orm import joinedload
from database import SessionLocal, Feed, Topic, Article
from services import NewsProcessor

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Initialize news processor (no API key needed for AWS Bedrock)
news_processor = NewsProcessor()

@app.route('/')
def dashboard():
    db = SessionLocal()
    try:
        articles = db.query(Article).options(joinedload(Article.topic), joinedload(Article.feed)).order_by(Article.published_date.desc()).limit(20).all()
        latest_article = db.query(Article).order_by(Article.created_at.desc()).first()
        last_refresh = latest_article.created_at if latest_article else None
        return render_template('dashboard.html', articles=articles, last_refresh=last_refresh)
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
        topics = db.query(Topic).all()
        return render_template('admin_topics.html', topics=topics, active_tab='topics')
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
    
    db = SessionLocal()
    try:
        topic = Topic(name=name, keywords=keywords)
        db.add(topic)
        db.commit()
        flash('Topic added successfully')
    finally:
        db.close()
    return redirect(url_for('admin_topics'))

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

if __name__ == '__main__':
    app.run(debug=True, threaded=True)