from flask import Flask, render_template, request, redirect, url_for, flash, abort
import sqlite3
import secrets
import validators
from datetime import datetime, timedelta
from config import get_config

app = Flask(__name__)
app.config.from_object(get_config())

# Database initialization with improved datetime handling
def get_db_connection():
    conn = sqlite3.connect('url_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            expiration_date TEXT,
            clicks INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def generate_short_code():
    return secrets.token_urlsafe(4)[:6]

def parse_db_datetime(dt_str):
    """Safely parse datetime strings from database"""
    if not dt_str:
        return None
    try:
        # Handle both with and without fractional seconds
        if '.' in dt_str:
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return dt_str  # Return as string if parsing fails

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form['url']
        custom_code = request.form.get('custom_code', '').strip()
        expiration_days = int(request.form.get('expiration', 30))
        
        if not validators.url(original_url):
            flash('Please enter a valid URL', 'danger')
            return redirect(url_for('index'))
        
        conn = get_db_connection()
        
        # Validate custom code
        if custom_code:
            if not custom_code.isalnum() or len(custom_code) < 3:
                flash('Custom code must be alphanumeric and at least 3 characters', 'danger')
                return redirect(url_for('index'))
            
            existing = conn.execute('SELECT * FROM urls WHERE short_code = ?', (custom_code,)).fetchone()
            if existing:
                flash('Custom code already in use', 'danger')
                return redirect(url_for('index'))
            short_code = custom_code
        else:
            short_code = generate_short_code()
            while conn.execute('SELECT * FROM urls WHERE short_code = ?', (short_code,)).fetchone():
                short_code = generate_short_code()
        
        # Calculate and format expiration date
        expiration_date = (datetime.now() + timedelta(days=expiration_days)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert into database
        conn.execute(
            'INSERT INTO urls (original_url, short_code, expiration_date) VALUES (?, ?, ?)',
            (original_url, short_code, expiration_date)
        )
        conn.commit()
        conn.close()
        
        short_url = request.host_url + short_code
        flash(f'Your shortened URL is ready!', 'success')
        return render_template('index.html', short_url=short_url, original_url=original_url)
    
    return render_template('index.html')

@app.route('/<short_code>')
def redirect_to_url(short_code):
    conn = get_db_connection()
    url_data = conn.execute(
        'SELECT original_url, expiration_date FROM urls WHERE short_code = ?',
        (short_code,)
    ).fetchone()
    conn.close()
    
    if url_data is None:
        abort(404)
    
    original_url = url_data['original_url']
    expiration_date = parse_db_datetime(url_data['expiration_date'])
    
    if expiration_date and datetime.now() > expiration_date:
        abort(410)  # Gone (expired)
    
    # Update click count
    conn = get_db_connection()
    conn.execute(
        'UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?',
        (short_code,)
    )
    conn.commit()
    conn.close()
    
    return redirect(original_url)

@app.route('/stats/<short_code>')
def url_stats(short_code):
    conn = get_db_connection()
    url_data = conn.execute(
        '''SELECT original_url, short_code, created_at, 
           expiration_date, clicks FROM urls WHERE short_code = ?''',
        (short_code,)
    ).fetchone()
    conn.close()
    
    if url_data is None:
        abort(404)
    
    # Convert to dict and parse datetimes
    url_dict = dict(url_data)
    url_dict['created_at'] = parse_db_datetime(url_data['created_at'])
    url_dict['expiration_date'] = parse_db_datetime(url_data['expiration_date'])
    
    return render_template('stats.html', url=url_dict)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(410)
def url_expired(e):
    return render_template('410.html'), 410

if __name__ == '__main__':
    init_db()
    app.run(debug=True)