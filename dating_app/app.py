"""
Dating App - Main Flask Application

Python concepts demonstrated:
- Flask web framework (similar to Spring Boot in Java)
- SQLAlchemy ORM (like JPA/Hibernate)
- Context managers (with statements)
- Type hints
- List/dict comprehensions
- Decorators (@app.route, @login_required)
"""

from datetime import datetime
from functools import wraps
from math import radians, cos, sin, asin, sqrt
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for, 
    session, jsonify, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from models import db, User, Match, Message, init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
upload_folder = Path(__file__).parent / 'static' / 'uploads'
upload_folder.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = str(upload_folder)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db.init_app(app)

# Helper decorator (like @PreAuthorize in Spring Security)
def login_required(f):
    """Decorator to require login - Pythonic way vs Java annotations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    
    Returns distance in kilometers.
    Python: Type hints in function signature (like Java method signatures)
    """
    # Convert to radians (like Math.toRadians in Java)
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Earth radius in km
    
    return round(c * r, 2)


@app.route('/')
def index():
    """Home page - redirects to login or swipe"""
    if 'user_id' in session:
        return redirect(url_for('swipe'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        # Dictionary unpacking (like Map.getOrDefault in Java)
        data = request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        bio = data.get('bio', '').strip()
        age = int(data.get('age', 0))
        lat = float(data.get('lat', 0))
        lon = float(data.get('lon', 0))
        
        # Check if username exists (list comprehension for filtering)
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
        
        # Create user (like EntityManager.persist in JPA)
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            name=name,
            bio=bio,
            age=age,
            latitude=lat,
            longitude=lon
        )
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        return redirect(url_for('edit_profile'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('swipe'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout - clears session"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit profile and upload images"""
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # Update text fields
        user.name = request.form.get('name', user.name)
        user.bio = request.form.get('bio', user.bio)
        user.age = int(request.form.get('age', user.age))
        user.latitude = float(request.form.get('lat', user.latitude))
        user.longitude = float(request.form.get('lon', user.longitude))
        
        # Handle image uploads (context manager for file handling)
        if 'images' in request.files:
            files = request.files.getlist('images')
            # List comprehension to process files
            new_images = []
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # Generate unique filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    filename = f"{user.id}_{timestamp}_{filename}"
                    filepath = Path(app.config['UPLOAD_FOLDER']) / filename
                    file.save(str(filepath))
                    new_images.append(filename)
            
            # Update images (keep existing, add new, limit to 5)
            existing = user.images.split(',') if user.images else []
            existing = [img for img in existing if img]  # Filter empty strings
            all_images = existing + new_images
            user.images = ','.join(all_images[:5])  # Slice to keep max 5
        
        db.session.commit()
        return redirect(url_for('swipe'))
    
    images = user.images.split(',') if user.images else []
    return render_template('edit_profile.html', user=user, images=images)


@app.route('/swipe')
@login_required
def swipe():
    """Main swiping interface"""
    user = User.query.get(session['user_id'])
    
    # Get users to show (not self, not already swiped)
    swiped_user_ids = {m.user2_id for m in Match.query.filter_by(user1_id=user.id).all()}
    swiped_user_ids.add(user.id)  # Exclude self
    
    # Query with filter (like JPA Criteria API)
    candidates = User.query.filter(
        ~User.id.in_(swiped_user_ids)
    ).limit(10).all()
    
    return render_template('swipe.html', candidates=candidates, current_user=user)


@app.route('/api/swipe', methods=['POST'])
@login_required
def api_swipe():
    """Handle swipe action (like/dislike)"""
    data = request.json
    user_id = session['user_id']
    target_id = data.get('target_id')
    action = data.get('action')  # 'like' or 'pass'
    
    # Create match record
    match = Match(user1_id=user_id, user2_id=target_id, liked=(action == 'like'))
    db.session.add(match)
    
    # Check for mutual like (match!)
    mutual = Match.query.filter_by(
        user1_id=target_id, 
        user2_id=user_id, 
        liked=True
    ).first()
    
    db.session.commit()
    
    return jsonify({
        'matched': mutual is not None,
        'message': 'It\'s a match!' if mutual else 'Swiped!'
    })


@app.route('/matches')
@login_required
def matches():
    """Show all matches"""
    user_id = session['user_id']
    
    # Get mutual matches using join (like SQL JOIN in JPA)
    matches = db.session.query(Match, User).join(
        User, Match.user2_id == User.id
    ).filter(
        Match.user1_id == user_id,
        Match.liked == True
    ).all()
    
    # Filter for mutual likes (list comprehension)
    mutual_matches = []
    for match, matched_user in matches:
        # Check reverse match
        reverse_match = Match.query.filter_by(
            user1_id=matched_user.id,
            user2_id=user_id,
            liked=True
        ).first()
        if reverse_match:
            mutual_matches.append(matched_user)
    
    return render_template('matches.html', matches=mutual_matches)


@app.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    """Chat with a matched user"""
    current_user_id = session['user_id']
    
    # Verify match exists
    match1 = Match.query.filter_by(user1_id=current_user_id, user2_id=user_id, liked=True).first()
    match2 = Match.query.filter_by(user1_id=user_id, user2_id=current_user_id, liked=True).first()
    
    if not (match1 and match2):
        return redirect(url_for('matches'))
    
    other_user = User.query.get(user_id)
    
    # Get messages (ordered by timestamp)
    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
    ).order_by(Message.timestamp.asc()).all()
    
    return render_template('chat.html', other_user=other_user, messages=messages)


@app.route('/api/messages', methods=['POST'])
@login_required
def api_send_message():
    """Send a message"""
    data = request.json
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    message = Message(
        sender_id=session['user_id'],
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'timestamp': message.timestamp.isoformat()
    })


@app.route('/api/messages/<int:user_id>')
@login_required
def api_get_messages(user_id):
    """Get messages with a user"""
    current_user_id = session['user_id']
    
    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
    ).order_by(Message.timestamp.asc()).all()
    
    # List comprehension to convert to dict (like DTO mapping in Java)
    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'content': m.content,
        'timestamp': m.timestamp.isoformat()
    } for m in messages])


@app.route('/api/users/<int:user_id>/distance')
@login_required
def api_get_distance(user_id):
    """Get distance to another user"""
    current_user = User.query.get(session['user_id'])
    other_user = User.query.get(user_id)
    
    if not (current_user and other_user):
        return jsonify({'error': 'User not found'}), 404
    
    distance = haversine_distance(
        current_user.latitude, current_user.longitude,
        other_user.latitude, other_user.longitude
    )
    
    return jsonify({'distance': distance})


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    with app.app_context():
        init_db()
    # For Cloudflare Tunnel: use 127.0.0.1 (localhost only)
    # For local network: use 0.0.0.0
    # debug=True only for development!
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)

