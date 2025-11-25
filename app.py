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

@app.route('/review-topics')
def review_topics():
    today = date.today()
    recent_date = today - timedelta(days=3)
    medium_date = today - timedelta(days=14)
    long_date = today - timedelta(days=35)

    recent = Topic.query.filter(
        and_(
            Topic.date_added >= recent_date,
            Topic.date_added < recent_date + timedelta(days=1)
        )
    ).all()

    medium = Topic.query.filter(
        and_(
            Topic.date_added >= medium_date,
            Topic.date_added < medium_date + timedelta(days=1)
        )
    ).all()

    long = Topic.query.filter(
        and_(
            Topic.date_added >= long_date,
            Topic.date_added < long_date + timedelta(days=1)
        )
    ).all()

    return render_template('review_topics.html', recent=recent, medium=medium, long=long)

# -------------------- Init Route --------------------

@app.route('/init-db')
def init_db():
    db.create_all()
    return "Database initialized!"

# -------------------- Main --------------------

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000, debug=True)
