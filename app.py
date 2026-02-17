"""
Flask Web Application for RFID Attendance System
Main server with all routes and WebSocket support
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import models
import config
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database on startup
models.init_db()

# ============================================================================
# Authentication Helpers
# ============================================================================

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# Authentication Routes
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        admin = models.get_admin_by_username(username)
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['full_name']
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    """Initial admin setup - only works if no admins exist"""
    # Check if any admins exist
    with models.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM admins')
        count = cursor.fetchone()['count']
    
    if count > 0:
        return "Admin accounts already exist. Use /login to access the system.", 403
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Create two admin accounts
        admin1_hash = generate_password_hash(data.get('password1'))
        admin2_hash = generate_password_hash(data.get('password2'))
        
        models.create_admin(data.get('username1'), admin1_hash, data.get('fullname1'))
        models.create_admin(data.get('username2'), admin2_hash, data.get('fullname2'))
        
        return jsonify({'success': True})
    
    return render_template('setup_admin.html')

# ============================================================================
# Main Application Routes
# ============================================================================

@app.route('/')
def index():
    """Home page - redirect to check-in display"""
    return redirect(url_for('checkin_display'))

@app.route('/display')
def checkin_display():
    """Live check-in display - no authentication required"""
    return render_template('checkin_display.html')

@app.route('/admin')
@login_required
def admin_panel():
    """Admin dashboard"""
    return render_template('admin.html')

@app.route('/register')
@login_required
def register_card():
    """Card registration page"""
    return render_template('register_card.html')

@app.route('/reports')
@login_required
def reports():
    """Reports and analytics page"""
    return render_template('reports.html')

# ============================================================================
# API Routes - User Management
# ============================================================================

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """Get all users"""
    users = models.get_all_users()
    return jsonify([dict(user) for user in users])

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    """Create new user with RFID card"""
    data = request.get_json()
    
    try:
        user_id = models.create_user(
            rfid_uid=data['rfid_uid'],
            name=data['name'],
            student_id=data['student_id'],
            email=data['email'],
            graduating_year=int(data['graduating_year']),
            assigned_task=data.get('assigned_task', 'No task assigned')
        )
        return jsonify({'success': True, 'user_id': user_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """Update user information"""
    data = request.get_json()
    
    try:
        models.update_user(
            user_id=user_id,
            name=data.get('name'),
            student_id=data.get('student_id'),
            email=data.get('email'),
            graduating_year=int(data['graduating_year']) if data.get('graduating_year') else None,
            assigned_task=data.get('assigned_task')
        )
        
        # Broadcast update to display
        socketio.emit('user_updated', {'user_id': user_id})
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Delete user"""
    try:
        models.delete_user(user_id)
        socketio.emit('user_deleted', {'user_id': user_id})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# ============================================================================
# API Routes - Check-in/Check-out
# ============================================================================

@app.route('/api/checkin/current', methods=['GET'])
def get_current_checkins():
    """Get all currently checked-in users"""
    checkins = models.get_current_checkins()
    
    result = []
    for checkin in checkins:
        check_in_time = datetime.strptime(checkin['check_in_time'], '%Y-%m-%d %H:%M:%S.%f')
        duration = datetime.now() - check_in_time
        
        result.append({
            'id': checkin['id'],
            'name': checkin['name'],
            'student_id': checkin['student_id'],
            'assigned_task': checkin['assigned_task'],
            'check_in_time': checkin['check_in_time'],
            'duration_minutes': int(duration.total_seconds() / 60)
        })
    
    return jsonify(result)

@app.route('/api/checkin/manual', methods=['POST'])
@login_required
def manual_checkin():
    """Manual check-in/check-out by admin"""
    data = request.get_json()
    user_id = data.get('user_id')
    action = data.get('action')  # 'checkin' or 'checkout'
    
    if action == 'checkin':
        success, message = models.check_in(user_id)
    elif action == 'checkout':
        success, message = models.check_out(user_id)
    else:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
    
    if success:
        # Broadcast update
        socketio.emit('checkin_update', {
            'action': action,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
    
    return jsonify({'success': success, 'message': message})

@app.route('/api/checkin/scan-card', methods=['POST'])
@login_required
def scan_card_for_registration():
    """Scan RFID card for registration (admin override)"""
    try:
        # Import here to avoid issues if hardware not available
        from rfid_scanner import manual_scan
        result = manual_scan()
        
        if result:
            return jsonify({'success': True, 'rfid_uid': result.get('rfid_uid')})
        else:
            return jsonify({'success': False, 'message': 'No card detected'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# API Routes - Reports and Analytics
# ============================================================================

@app.route('/api/reports/daily', methods=['GET'])
@login_required
def daily_report():
    """Get daily attendance report"""
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    start_date = f"{date_str} 00:00:00"
    end_date = f"{date_str} 23:59:59"
    
    checkins = models.get_all_checkins(start_date, end_date)
    
    # Calculate statistics
    total_visits = len(checkins)
    unique_visitors = len(set(c['user_id'] for c in checkins))
    
    # Calculate average duration
    total_duration = 0
    completed_visits = 0
    
    for checkin in checkins:
        if checkin['check_out_time']:
            check_in = datetime.strptime(checkin['check_in_time'], '%Y-%m-%d %H:%M:%S.%f')
            check_out = datetime.strptime(checkin['check_out_time'], '%Y-%m-%d %H:%M:%S.%f')
            duration = (check_out - check_in).total_seconds() / 60
            total_duration += duration
            completed_visits += 1
    
    avg_duration = total_duration / completed_visits if completed_visits > 0 else 0
    
    return jsonify({
        'date': date_str,
        'total_visits': total_visits,
        'unique_visitors': unique_visitors,
        'average_duration_minutes': round(avg_duration, 2),
        'checkins': [dict(c) for c in checkins]
    })

@app.route('/api/reports/weekly', methods=['GET'])
@login_required
def weekly_report():
    """Get weekly attendance statistics"""
    # Get last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    checkins = models.get_all_checkins(
        start_date.strftime('%Y-%m-%d 00:00:00'),
        end_date.strftime('%Y-%m-%d 23:59:59')
    )
    
    # Group by day
    daily_stats = {}
    for checkin in checkins:
        date = checkin['check_in_time'][:10]
        if date not in daily_stats:
            daily_stats[date] = {'count': 0, 'unique_users': set()}
        daily_stats[date]['count'] += 1
        daily_stats[date]['unique_users'].add(checkin['user_id'])
    
    # Format for response
    result = []
    for date, stats in sorted(daily_stats.items()):
        result.append({
            'date': date,
            'total_visits': stats['count'],
            'unique_visitors': len(stats['unique_users'])
        })
    
    return jsonify(result)

@app.route('/api/reports/user/<int:user_id>', methods=['GET'])
@login_required
def user_history_report(user_id):
    """Get check-in history for a specific user"""
    history = models.get_user_history(user_id, limit=100)
    
    result = []
    for record in history:
        duration = None
        if record['check_out_time']:
            check_in = datetime.strptime(record['check_in_time'], '%Y-%m-%d %H:%M:%S.%f')
            check_out = datetime.strptime(record['check_out_time'], '%Y-%m-%d %H:%M:%S.%f')
            duration = int((check_out - check_in).total_seconds() / 60)
        
        result.append({
            'check_in_time': record['check_in_time'],
            'check_out_time': record['check_out_time'],
            'duration_minutes': duration,
            'auto_checkout': record['auto_checkout']
        })
    
    return jsonify(result)

# ============================================================================
# API Routes - Settings
# ============================================================================

@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    """Get system settings"""
    return jsonify({
        'max_occupancy': models.get_setting('max_occupancy'),
        'auto_checkout_time': models.get_setting('auto_checkout_time'),
        'auto_checkout_enabled': models.get_setting('auto_checkout_enabled')
    })

@app.route('/api/settings', methods=['POST'])
@login_required
def update_settings():
    """Update system settings"""
    data = request.get_json()
    
    if 'max_occupancy' in data:
        models.update_setting('max_occupancy', str(data['max_occupancy']))
    if 'auto_checkout_time' in data:
        models.update_setting('auto_checkout_time', data['auto_checkout_time'])
    if 'auto_checkout_enabled' in data:
        models.update_setting('auto_checkout_enabled', '1' if data['auto_checkout_enabled'] else '0')
    
    return jsonify({'success': True})

@app.route('/api/auto-checkout', methods=['POST'])
@login_required
def trigger_auto_checkout():
    """Manually trigger auto-checkout for all users"""
    count = models.auto_checkout_all()
    socketio.emit('auto_checkout', {'count': count})
    return jsonify({'success': True, 'count': count})

# ============================================================================
# WebSocket Events
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit('connected', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

# ============================================================================
# Background Tasks
# ============================================================================

def auto_checkout_scheduler():
    """Background task to auto-checkout users at specified time"""
    while True:
        try:
            enabled = models.get_setting('auto_checkout_enabled')
            if enabled == '1':
                checkout_time = models.get_setting('auto_checkout_time')
                now = datetime.now()
                target_time = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {checkout_time}", '%Y-%m-%d %H:%M')
                
                # Check if it's time to auto-checkout (within 1 minute window)
                if abs((now - target_time).total_seconds()) < 60:
                    count = models.auto_checkout_all()
                    if count > 0:
                        print(f"Auto-checkout: {count} users checked out at {checkout_time}")
                        socketio.emit('auto_checkout', {'count': count})
            
            time.sleep(60)  # Check every minute
        except Exception as e:
            print(f"Error in auto-checkout scheduler: {e}")
            time.sleep(60)

# Start background scheduler
scheduler_thread = threading.Thread(target=auto_checkout_scheduler, daemon=True)
scheduler_thread.start()

# ============================================================================
# Run Application
# ============================================================================

if __name__ == '__main__':
    print("="*50)
    print("RFID Attendance System - Web Server")
    print("="*50)
    print(f"Server starting on http://0.0.0.0:5000")
    print("First time setup: http://0.0.0.0:5000/setup-admin")
    print("="*50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=config.DEBUG)
