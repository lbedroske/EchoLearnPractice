from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta
from sqlalchemy import and_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///topics.db'
db = SQLAlchemy(app)

# -------------------- Models --------------------

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.Date, nullable=False)

# -------------------- Routes --------------------
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/enter-topic', methods=['GET', 'POST'])
def enter_topic():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description')
        today = date.today()
        new_topic = Topic(title=title, description=description, date_added=today)
        db.session.add(new_topic)
        db.session.commit()
        return redirect('/')
    return render_template('enter_topic.html')

@app.route('/enter-missing-topic', methods=['GET', 'POST'])
def enter_missing_topic():
    if request.method == 'POST':
        try:
            title = request.form['title']
            description = request.form.get('description')
            date_added_str = request.form['date_added']
            from datetime import datetime
            date_added = datetime.strptime(date_added_str, '%Y-%m-%d').date()
            new_topic = Topic(title=title, description=description, date_added=date_added)
            db.session.add(new_topic)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            print(f"Error adding missing topic: {e}")
            return f"Error: {e}", 500
    return render_template('enter_missing_topic.html')

@app.route('/review_topics')
def review_topics():
    try:
        # Try to get today's scheduled topics (your existing logic)
        today = datetime.today().date()
        topics_to_review = Topic.query.filter(
            Topic.next_review_date <= today
        ).all()
        
        return render_template('review_topics.html', topics=topics_to_review)
        
    except Exception as e:
        # This catches: no table yet, no topics, or any other error
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


