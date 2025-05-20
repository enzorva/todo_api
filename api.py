import sqlite3
import datetime 
import uuid
import jwt
import os
from dotenv import load_dotenv
from functools import wraps
from flask import Flask, request, jsonify, g

app = Flask(__name__)

load_dotenv()
SECRET_KEY = os.environ.get('SECRET_KEY')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            g.user = data  
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('database.db')
    g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    db.execute('''    
        CREATE TABLE IF NOT EXISTS todo_list (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS todo_items (
            id TEXT PRIMARY KEY,
            list_id TEXT REFERENCES todo_list(id),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            priority INT DEFAULT 0,
            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (list_id) REFERENCES todo_list (id)
        );
    ''')


# ------- User Authentication Routes ---------

@app.route('/auth/register', methods=['POST'])
def register_user():
    data = request.get_json()
    db = get_db()
    user_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    db.execute('''
        INSERT INTO users (id, username, email, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)''', (user_id, data['username'], data['email'], data['password_hash'], now)
    )
    db.commit()
    return jsonify({'id': user_id, 'username': data['username'], 'email': data['email']}), 201

@app.route('/auth/login', methods=['POST'])
def login_user():
    data = request.get_json()
    db = get_db()
    user = db.execute('''
        SELECT * FROM users WHERE username = ? AND password_hash = ?
    ''', (data['username'], data['password_hash'])).fetchone()
    if user:
        payload = {
            "user_id": user['id'],
            "username": user['username'],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'token': token
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401
    
@app.route('/auth/logout', methods=['POST'])
def logout_user():
    
    return jsonify({'message': 'Logged out successfully'}), 200


# --------- Todo Lists Routes ---------

@app.route('/lists', methods=['GET'])
@token_required
def get_lists():
    db = get_db()

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    title = request.args.get('title', None)

    sql = "SELECT * FROM todo_list WHERE user_id = ?"
    params = [g.user['user_id']]

    if title:
        sql += " AND title LIKE ?"
        params.append(f"%{title}%")
    sql += " LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    cursor = db.execute(sql, params)
    lists = cursor.fetchall()
    return jsonify([dict(list) for list in lists]), 200

@app.route('/lists', methods=['POST'])
@token_required
def create_list():
    data = request.get_json()
    db = get_db()
    list_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    db.execute('''
        INSERT INTO todo_list (id, user_id, title, created_at)
        VALUES (?, ?, ?, ?)''', (list_id, data['user_id'], data['title'], now)
    )
    db.commit()
    return jsonify({'id': list_id, 'title': data['title']}), 201

@app.route('/lists/<list_id>', methods=['GET'])
@token_required
def get_list(list_id):
    db = get_db()
    list = db.execute('''
        SELECT * FROM todo_list WHERE id = ?
    ''', (list_id,)).fetchone()
    if list:
        return jsonify(dict(list)), 200
    else:
        return jsonify({'error': 'List not found'}), 404
    
@app.route('/lists/<list_id>', methods=['PUT'])
@token_required
def update_list(list_id):
    data = request.get_json()
    db = get_db()
    now = datetime.datetime.now().isoformat()
    db.execute('''
        UPDATE todo_list SET title = ?, updated_at = ? WHERE id = ?
    ''', (data['title'], now, list_id))
    db.commit()
    return jsonify({'message': 'List updated successfully'}), 200

@app.route('/lists/<list_id>', methods=['DELETE'])
@token_required
def delete_list(list_id):
    db = get_db()
    db.execute('''
        DELETE FROM todo_list WHERE id = ?
    ''', (list_id,))
    db.commit()
    return jsonify({'message': 'List deleted successfully'}), 200

# --------- Todo Items Routes ---------

@app.route('/lists/<list_id>/items', methods=['GET'])
@token_required
def get_items(list_id):
    db = get_db()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    title = request.args.get('title', None)

    count_sql = "SELECT COUNT(*) FROM todo_items WHERE list_id = ?"
    count_params = [list_id]
    if title:
        count_sql += " AND title LIKE ?"
        count_params.append(f"%{title}%")
    total = db.execute(count_sql, count_params).fetchone()[0]

    sql += " LIMIT ? OFFSET ?"
    params = [list_id]

    if title:
        sql += " AND title LIKE ?"
        params.append(f"%{title}%")
    sql += " LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    cursor = db.execute(sql, params)
    items = [dict(item) for item in cursor.fetchall()]

    return jsonify({
        "data": items,
        "page": page,
        "limit": per_page,
        "total": total
    }), 200

@app.route('/lists/<list_id>/items', methods=['POST'])
@token_required 
def create_item(list_id):
    data = request.get_json()
    db = get_db()
    item_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    db.execute('''
        INSERT INTO todo_items (id, list_id, title, description, status, priority, due_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (item_id, list_id, data['title'], data['description'], data['status'], data['priority'], data['due_date'], now)
    )
    db.commit()
    return jsonify({'id': item_id, 'title': data['title']}), 201

@app.route('/lists/<list_id>/items/<item_id>', methods=['GET'])
@token_required
def get_item(list_id, item_id):
    db = get_db()
    item = db.execute('''
        SELECT * FROM todo_items WHERE id = ? AND list_id = ?
    ''', (item_id, list_id)).fetchone()
    if item:
        return jsonify(dict(item)), 200
    else:
        return jsonify({'error': 'Item not found'}), 404
    
@app.route('/lists/<list_id>/items/<item_id>', methods=['PUT'])
@token_required
def update_item(list_id, item_id):
    data = request.get_json()
    db = get_db()
    now = datetime.datetime.now().isoformat()
    db.execute('''
        UPDATE todo_items SET title = ?, description = ?, status = ?, priority = ?, due_date = ?, updated_at = ? WHERE id = ? AND list_id = ?
    ''', (data['title'], data['description'], data['status'], data['priority'], data['due_date'], now, item_id, list_id))
    db.commit()
    return jsonify({'message': 'Item updated successfully'}), 200

@app.route('/lists/<list_id>/items/<item_id>', methods=['DELETE'])
@token_required
def delete_item(list_id, item_id):
    db = get_db()
    db.execute('''
        DELETE FROM todo_items WHERE id = ? AND list_id = ?
    ''', (item_id, list_id))
    db.commit()
    return jsonify({'message': 'Item deleted successfully'}), 200

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)