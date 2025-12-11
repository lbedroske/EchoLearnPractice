from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Use PostgreSQL on Render, SQLite locally
database_url = os.environ.get('DATABASE_URL', 'sqlite:///topics.db')

# Fix for Render's postgres:// vs postgresql:// issue
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------- Models --------------------
class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.Date, nullable=False)
    next_review_date = db.Column(db.Date, nullable=True)

# -------------------- Routes --------------------
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/enter-topic', methods=['GET', 'POST'])
def enter_topic():
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form.get('description', '').strip()
        
        if title:
            new_topic = Topic(
                title=title,
                description=description,
                date_added=datetime.today().date(),
                next_review_date=datetime.today().date() + timedelta(days=1)
            )
            db.session.add(new_topic)
            db.session.commit()
            return redirect(url_for('dashboard'))
    
    return render_template('enter_topic.html')

@app.route('/enter-missing-topic', methods=['GET', 'POST'])
def enter_missing_topic():
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form.get('description', '').strip()
        date_added_str = request.form.get('date_added')
        
        if title and date_added_str:
            # Parse the date from the form
            date_added = datetime.strptime(date_added_str, '%Y-%m-%d').date()
            
            # Calculate next review date based on when it was "added"
            days_since = (datetime.today().date() - date_added).days
            
            # Simple logic: if it was added recently, schedule soon; if long ago, schedule sooner
            if days_since == 0:
                next_review = datetime.today().date() + timedelta(days=1)
            elif days_since <= 3:
                next_review = datetime.today().date() + timedelta(days=1)
            elif days_since <= 7:
                next_review = datetime.today().date() + timedelta(days=2)
            else:
                next_review = datetime.today().date()  # Review today if it's old
            
            new_topic = Topic(
                title=title,
                description=description,
                date_added=date_added,
                next_review_date=next_review
            )
            db.session.add(new_topic)
            db.session.commit()
            return redirect(url_for('dashboard'))
    
    return render_template('enter_missing_topic.html')

@app.route('/review_topics')
def review_topics():
    try:
        today = datetime.today().date()
        topics_to_review = Topic.query.filter(
            Topic.next_review_date <= today
        ).all()
        
        return render_template('review_topics.html', topics=topics_to_review)
        
    except Exception as e:
        return render_template('review_topics.html', topics=[], error_message="Nothing to review today — come back tomorrow or add some topics!")

@app.route('/review/<int:topic_id>/good', methods=['POST'])
def review_good(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    
    # Calculate days since last review
    days_since_added = (datetime.today().date() - topic.date_added).days
    
    # Simple spaced repetition: 1, 3, 7, 14, 30, 60 days
    if topic.next_review_date:
        days_since_last_review = (datetime.today().date() - topic.next_review_date).days + 1
    else:
        days_since_last_review = 1
    
    # Determine next interval (roughly double each time)
    if days_since_last_review <= 1:
        next_interval = 3
    elif days_since_last_review <= 3:
        next_interval = 7
    elif days_since_last_review <= 7:
        next_interval = 14
    elif days_since_last_review <= 14:
        next_interval = 30
    elif days_since_last_review <= 30:
        next_interval = 60
    else:
        next_interval = 90
    
    topic.next_review_date = datetime.today().date() + timedelta(days=next_interval)
    db.session.commit()
    
    return redirect(url_for('review_topics'))

@app.route('/review/<int:topic_id>/again', methods=['POST'])
def review_again(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    
    # If marked "again", review sooner (1 day)
    topic.next_review_date = datetime.today().date() + timedelta(days=1)
    db.session.commit()
    
    return redirect(url_for('review_topics'))

@app.route('/classes')
def classes():
    return render_template('classes.html')

# -------------------- Init Route --------------------
@app.route('/init-db')
def init_db():
    with app.app_context():
        db.create_all()
    return "Database initialized!"

@app.route('/migrate-db')
def migrate_db():
    """Add next_review_date column to existing topics if it doesn't exist"""
    try:
        from sqlalchemy import inspect, text
        
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('topic')]
        
        if 'next_review_date' not in columns:
            # Add the column
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE topic ADD COLUMN next_review_date DATE'))
                conn.commit()
            
            # Set initial review dates for existing topics
            topics = Topic.query.all()
            for topic in topics:
                if not topic.next_review_date:
                    topic.next_review_date = datetime.today().date() + timedelta(days=1)
            db.session.commit()
            
            return "Database migrated successfully! next_review_date column added."
        else:
            return "Database already has next_review_date column. No migration needed."
    except Exception as e:
        return f"Migration error: {str(e)}"

# -------------------- Main --------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
