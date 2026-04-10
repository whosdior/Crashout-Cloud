from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import uuid
import os
from bson.objectid import ObjectId

app = Flask(__name__)
CORS(app)

# MongoDB connection
MONGO_URI = ""
try:
    client = MongoClient(MONGO_URI)
    db = client["crashout_db"]
    print("✅ Connected to MongoDB Atlas successfully!")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB Atlas: {e}")
    # Fallback to local MongoDB for testing
    MONGO_URI = ""
    client = MongoClient(MONGO_URI)
    db = client["crashout_db"]
    print("⚠️ Fallback to local MongoDB")

# Collections
journals_collection = db["journals"]
users_collection = db["users"]
servers_collection = db["servers"]
settings_collection = db["settings"]

# Initialize MongoDB collections and default settings
def init_mongodb():
    # Create default settings if they don't exist
    if settings_collection.count_documents({}) == 0:
        default_settings = {
            'username': 'Trader',
            'serverName': 'Crashout',
            'serverIcon': 'CR',
            'theme': 'dark'
        }
        settings_collection.insert_one(default_settings)

# Initialize MongoDB on startup
init_mongodb()


@app.route("/")
def landing():
    return render_template("crashout_v2.html")



# User registration and authentication
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    # Check if user already exists
    if users_collection.find_one({'username': username}):
        return jsonify({'error': 'Username already taken'}), 400
    
    user_data = {
        'username': username,
        'registeredAt': datetime.now().isoformat(),
        'ownedJournals': [],
        'servers': []
    }
    
    users_collection.insert_one(user_data)
    return jsonify(user_data)


@app.route('/manifest.json')
def manifest():
    return send_file('manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js')
def service_worker():
    return send_file('sw.js', mimetype='application/javascript')


@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json
    
    username = data.get('username', '').strip()
    
    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({'error': 'Username not found'}), 404
    
    # Convert ObjectId to string for JSON serialization
    user['_id'] = str(user['_id'])
    return jsonify(user)

@app.route('/api/check-username/<username>', methods=['GET'])
def check_username(username):
    user = users_collection.find_one({'username': username})
    return jsonify({'available': user is None})

# Server management
@app.route('/api/servers', methods=['GET'])
def get_servers():
    servers = list(servers_collection.find({}))
    # Convert ObjectId to string for JSON serialization
    for server in servers:
        server['_id'] = str(server['_id'])
    return jsonify({server['name']: server for server in servers})

@app.route('/api/servers', methods=['POST'])
def create_server():
    data = request.json
    
    server_name = data.get('name', '').strip()
    username = data.get('username', '').strip()
    
    if not server_name:
        return jsonify({'error': 'Server name is required'}), 400
    
    # Check if server already exists
    if servers_collection.find_one({'name': server_name}):
        return jsonify({'error': 'Server already exists'}), 400
    
    # Check if user already has a server (one server per user limit)
    user = users_collection.find_one({'username': username})
    if user and user.get('servers') and len(user['servers']) > 0:
        return jsonify({'error': 'You can only create one server per user'}), 400
    
    server_data = {
        'name': server_name,
        'owner': username,
        'channels': {
            'general': {
                'id': str(uuid.uuid4()),
                'name': 'general',
                'messages': []
            }
        },
        'members': [username],
        'createdAt': datetime.now().isoformat()
    }
    
    result = servers_collection.insert_one(server_data)
    server_data['_id'] = str(result.inserted_id)
    
    # Add server to user's servers
    users_collection.update_one(
        {'username': username},
        {'$push': {'servers': server_name}}
    )
    
    return jsonify(server_data)

@app.route('/api/servers/<server_name>/channels/<channel_name>/messages', methods=['GET'])
def get_channel_messages(server_name, channel_name):
    server = servers_collection.find_one({'name': server_name})
    
    if not server:
        return jsonify({'error': 'Server not found'}), 404
    
    if channel_name not in server['channels']:
        return jsonify({'error': 'Channel not found'}), 404
    
    return jsonify(server['channels'][channel_name]['messages'])

@app.route('/api/servers/<server_name>/channels/<channel_name>/messages', methods=['POST'])
def add_channel_message(server_name, channel_name):
    server = servers_collection.find_one({'name': server_name})
    
    if not server:
        return jsonify({'error': 'Server not found'}), 404
    
    if channel_name not in server['channels']:
        return jsonify({'error': 'Channel not found'}), 404
    
    data = request.json
    content = data.get('content', '').strip()
    username = data.get('username', '').strip()
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    message = {
        'id': str(uuid.uuid4()),
        'author': username,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }
    
    # Add message to server
    servers_collection.update_one(
        {'name': server_name},
        {'$push': {f'channels.{channel_name}.messages': message}}
    )
    
    return jsonify(message)

@app.route('/api/journals/<journal_name>', methods=['DELETE'])
def delete_journal(journal_name):
    data = request.json or {}
    username = data.get('username', '').strip()
    
    journal = journals_collection.find_one({'name': journal_name})
    if not journal:
        return jsonify({'error': 'Journal not found'}), 404
    
    # Check if user owns this journal
    if journal['createdBy'] != username:
        return jsonify({'error': 'Only the journal owner can delete it'}), 403
    
    # Delete journal
    result = journals_collection.delete_one({'name': journal_name})
    
    # Remove from user's owned journals
    users_collection.update_one(
        {'username': username},
        {'$pull': {'ownedJournals': journal_name}}
    )
    
    return jsonify({'success': True})

@app.route('/api/servers/<server_name>', methods=['DELETE'])
def delete_server(server_name):
    data = request.json or {}
    username = data.get('username', '').strip()
    
    server = servers_collection.find_one({'name': server_name})
    if not server:
        return jsonify({'error': 'Server not found'}), 404
    
    # Check if user owns this server
    if server['owner'] != username:
        return jsonify({'error': 'Only the server owner can delete it'}), 403
    
    # Delete server
    servers_collection.delete_one({'name': server_name})
    
    # Remove from all users' server lists
    users_collection.update_many(
        {},
        {'$pull': {'servers': server_name}}
    )
    
    return jsonify({'success': True})

@app.route('/api/journals/<journal_name>/entries/<entry_id>', methods=['DELETE'])
def delete_entry(journal_name, entry_id):
    data = request.json or {}
    username = data.get('username', '').strip()
    
    journal = journals_collection.find_one({'name': journal_name})
    if not journal:
        return jsonify({'error': 'Journal not found'}), 404
    
    # Find the entry first
    entry = None
    for entry_data in journal.get('entries', []):
        if entry_data['id'] == entry_id:
            entry = entry_data
            break
    
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404
    
    # Check if user owns this entry (not just the journal)
    if entry['author'] != username:
        return jsonify({'error': 'You can only delete your own entries'}), 403
    
    # Remove the entry
    result = journals_collection.update_one(
        {'name': journal_name},
        {'$pull': {'entries': {'id': entry_id}}}
    )
    
    if result.modified_count == 0:
        return jsonify({'error': 'Entry not found'}), 404
    
    return jsonify({'success': True})

@app.route('/api/journals', methods=['GET'])
def get_journals():
    journals = list(journals_collection.find({}))
    # Convert ObjectId to string for JSON serialization
    for journal in journals:
        journal['_id'] = str(journal['_id'])
    return jsonify({journal['name']: journal for journal in journals})

@app.route('/api/journals', methods=['POST'])
def create_journal():
    data = request.json
    
    journal_name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    username = data.get('username', 'Anonymous')
    
    if not journal_name:
        return jsonify({'error': 'Journal name is required'}), 400
    
    # Check if journal already exists
    if journals_collection.find_one({'name': journal_name}):
        return jsonify({'error': 'Journal already exists'}), 400
    
    # Check if user already has 3 journals (limit per user)
    user = users_collection.find_one({'username': username})
    if user and user.get('ownedJournals') and len(user['ownedJournals']) >= 3:
        return jsonify({'error': 'You can only create up to 3 journals per user'}), 400
    
    journal_data = {
        'name': journal_name,
        'description': description,
        'entries': [],
        'createdBy': username,
        'createdAt': datetime.now().isoformat()
    }
    
    result = journals_collection.insert_one(journal_data)
    journal_data['_id'] = str(result.inserted_id)
    
    # Add journal to user's owned journals
    users_collection.update_one(
        {'username': username},
        {'$push': {'ownedJournals': journal_name}}
    )
    
    return jsonify(journal_data)

@app.route('/api/journals/<journal_name>/entries', methods=['GET'])
def get_entries(journal_name):
    journal = journals_collection.find_one({'name': journal_name})
    
    if not journal:
        return jsonify({'error': 'Journal not found'}), 404
    
    return jsonify(journal['entries'])

@app.route('/api/journals/<journal_name>/entries', methods=['POST'])
def add_entry(journal_name):
    journal = journals_collection.find_one({'name': journal_name})
    
    if not journal:
        return jsonify({'error': 'Journal not found'}), 404
    
    data = request.json
    content = data.get('content', '').strip()
    username = data.get('username', 'Anonymous')
    image_url = data.get('imageUrl', '')
    
    # Allow either content or image_url (or both)
    if not content and not image_url:
        return jsonify({'error': 'Content or image is required'}), 400
    
    # Debug logging
    print(f"Ownership check: journalOwner='{journal['createdBy']}', currentUser='{username}', isOwner={journal['createdBy'] == username}")
    
    # Check if user owns this journal
    if journal['createdBy'] != username:
        return jsonify({'error': 'Only the journal owner can add entries'}), 403
    
    entry = {
        'id': str(uuid.uuid4()),
        'author': username,
        'content': content,
        'imageUrl': image_url,
        'timestamp': datetime.now().isoformat()
    }
    
    # Add entry to journal
    journals_collection.update_one(
        {'name': journal_name},
        {'$push': {'entries': entry}}
    )
    
    return jsonify(entry)

@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = settings_collection.find_one()
    if settings:
        settings['_id'] = str(settings['_id'])
        return jsonify(settings)
    else:
        return jsonify({})

@app.route('/api/settings', methods=['POST'])
def save_settings():
    try:
        settings = request.json
        
        # Get existing settings to preserve _id
        existing_settings = settings_collection.find_one()
        
        if existing_settings:
            # Update existing settings without changing _id
            settings_collection.update_one(
                {'_id': existing_settings['_id']},
                {'$set': {
                    'username': settings.get('username', existing_settings.get('username', 'Trader')),
                    'serverName': settings.get('serverName', existing_settings.get('serverName', 'Crashout')),
                    'serverIcon': settings.get('serverIcon', existing_settings.get('serverIcon', 'CR')),
                    'theme': settings.get('theme', existing_settings.get('theme', 'dark'))
                }}
            )
        else:
            # Create new settings if none exist
            default_settings = {
                'username': settings.get('username', 'Trader'),
                'serverName': settings.get('serverName', 'Crashout'),
                'serverIcon': settings.get('serverIcon', 'CR'),
                'theme': settings.get('theme', 'dark')
            }
            settings_collection.insert_one(default_settings)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error saving settings: {e}")
        return jsonify({'error': 'Failed to save settings'}), 500

@app.route('/api/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Create uploads directory if it doesn't exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    # Save file with unique name
    filename = str(uuid.uuid4()) + '_' + file.filename
    file_path = os.path.join('uploads', filename)
    file.save(file_path)
    
    return jsonify({'imageUrl': f'/uploads/{filename}'})

@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
