# server.py
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

active_users = {}

def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(username):
    sid = request.sid  # Get the session ID
    if not username:
        emit('error', {'message': 'Please enter a valid username.'})
        return

    print(f'{username} with SID {sid} has joined the chat.')

    active_users[sid] = {
        'username': username,
        'status': 'Online',
        'last_active': get_current_time()
    }

    emit_user_list()
    emit_activity_log(f'{username} joined the chat.')

@socketio.on('message')
def handle_message(data):
    sid = request.sid  # Get the session ID
    if sid not in active_users:
        emit('error', {'message': 'User not found. Please refresh the page and try again.'})
        return

    sender = active_users[sid]['username']
    message = data.get('message')

    if not message:
        emit('error', {'message': 'Message cannot be empty.'})
        return

    print(f'Message from {sender}: {message}')
    emit('message', {'username': sender, 'message': message, 'status': 'sent'}, broadcast=True)

@socketio.on('message_seen')
def handle_message_seen(data):
    sid = request.sid  # Get the session ID
    if sid not in active_users:
        emit('error', {'message': 'User not found. Please refresh the page and try again.'})
        return

    sender = data.get('sender')
    recipient = active_users[sid]['username']

    if not sender:
        emit('error', {'message': 'Sender information missing. Please try again.'})
        return

    print(f'Message from {sender} seen by {recipient}')
    
    # Only emit to the sender of the original message
    sender_sid = [sid for sid, user in active_users.items() if user['username'] == sender]
    if sender_sid:
        emit('message_seen', {'username': recipient, 'status': 'seen', 'sender': sender}, room=sender_sid[0])
    else:
        print(f'Error: Sender with username {sender} not found.')

@socketio.on('typing')
def handle_typing(typing_message):
    sid = request.sid  # Get the session ID
    if sid not in active_users:
        emit('error', {'message': 'User not found. Please refresh the page and try again.'})
        return

    emit('typing', {'username': active_users[sid]['username'], 'message': typing_message}, broadcast=True)

@socketio.on('leave')
def handle_leave():
    sid = request.sid  # Get the session ID
    if sid not in active_users:
        emit('error', {'message': 'User not found. Please refresh the page and try again.'})
        return

    user = active_users[sid]['username']
    print(f'{user} with SID {sid} has left the chat.')
    del active_users[sid]
    emit_user_list()
    emit_activity_log(f'{user} left the chat.')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid  # Get the session ID
    if sid not in active_users:
        return

    user = active_users[sid]['username']
    print(f'{user} with SID {sid} has left the chat.')
    del active_users[sid]
    emit_user_list()
    emit_activity_log(f'{user} left the chat.')

def emit_user_list():
    users = [{'username': user['username'], 'status': user['status'], 'last_active': user['last_active']}
             for user in active_users.values()]
    emit('update_user_list', users, broadcast=True)

def emit_activity_log(message):
    emit('activity_log', {'message': message}, broadcast=True)

def update_user_status(sid, status):
    if sid in active_users:
        active_users[sid]['status'] = status
        active_users[sid]['last_active'] = get_current_time()
        emit_user_list()

if __name__ == '__main__':
    socketio.run(app, debug=True)
