from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from dotenv import load_dotenv
import os
import threading
import json
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from bs4 import BeautifulSoup
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

@app.route('/delete_article/<int:article_id>', methods=['POST'])
def delete_article(article_id):
    db = SessionLocal()
    try:
        article = db.get(Article, article_id)
        if article:
            db.delete(article)
            db.commit()
            return jsonify({"status": "success", "message": "Article deleted successfully"})
        else:
            return jsonify({"status": "error", "message": "Article not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

@app.route('/refresh_status')
def refresh_status():
    return jsonify({"processing": news_processor.processing})

@app.route('/download_pdf/<int:article_id>')
def download_pdf(article_id):
    db = SessionLocal()
    try:
        article = db.query(Article).options(joinedload(Article.topic), joinedload(Article.feed)).filter(Article.id == article_id).first()
        if not article:
            return jsonify({"error": "Article not found"}), 404
        
        # Scrape full content from URL
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(article.url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            full_content = soup.get_text(separator='\n', strip=True)
        except Exception as e:
            return jsonify({"error": f"Failed to scrape article: {str(e)}"}), 500
        
        # Parse topic scores
        topic_scores = {}
        if article.topic_scores:
            try:
                topic_scores = json.loads(article.topic_scores)
            except:
                pass
        
        # Generate PDF using ReportLab
        pdf_file = BytesIO()
        doc = SimpleDocTemplate(pdf_file, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#333333'), spaceAfter=12)
        story.append(Paragraph(article.title, title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Metadata
        metadata_data = [
            ['Source:', article.feed.name],
            ['Published:', article.published_date.strftime('%Y-%m-%d %H:%M')],
        ]
        if article.author:
            metadata_data.append(['Author:', article.author])
        metadata_data.append(['URL:', article.url])
        
        metadata_table = Table(metadata_data, colWidths=[1*inch, 5.5*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#007bff')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 0.2*inch))
        
        # AI Summary
        summary_style = ParagraphStyle('Summary', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#155724'), spaceAfter=8)
        story.append(Paragraph('AI-Generated Summary', summary_style))
        summary_text = article.summary.replace('•', '\u2022')
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Topic Scores
        story.append(Paragraph('Topic Relevancy Scores', summary_style))
        scores_text = f"<b>Best Match:</b> {article.topic.name} ({article.relevancy_score}%)"
        for name, score in topic_scores.items():
            if score >= 75:
                scores_text += f" | <b>{name}:</b> {score}%"
        story.append(Paragraph(scores_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Full Content
        content_style = ParagraphStyle('Content', parent=styles['Heading2'], fontSize=12, spaceAfter=8)
        story.append(Paragraph('Full Article Content', content_style))
        
        # Split content into paragraphs
        paragraphs = full_content.split('\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        pdf_file.seek(0)
        
        # Create safe filename
        safe_title = "".join(c for c in article.title if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        filename = f"{safe_title}.pdf"
        
        return send_file(pdf_file, mimetype='application/pdf', as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, threaded=True)