from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///topics.db'
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
        
@app.route('/classes')
def classes():
    return render_template('classes.html')

# -------------------- Init Route --------------------
@app.route('/init-db')
def init_db():
    db.create_all()
    return "Database initialized!"

# -------------------- Main --------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
