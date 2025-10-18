from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import os
from datetime import datetime
import json
from bot_manager import BotManager
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
bot_manager = BotManager()

def init_db():
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bots
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  bot_name TEXT,
                  bot_token TEXT NOT NULL,
                  status TEXT DEFAULT 'stopped',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS commands
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  bot_id INTEGER,
                  command_name TEXT NOT NULL,
                  command_code TEXT NOT NULL,
                  FOREIGN KEY(bot_id) REFERENCES bots(id))''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    return render_template('dashboard.html')

@app.route('/editor')
def editor():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    return render_template('editor.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email y contraseña requeridos'})
    
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    
    try:
        hashed = hash_password(password)
        c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed))
        conn.commit()
        user_id = c.lastrowid
        session['user_id'] = user_id
        session['email'] = email
        conn.close()
        return jsonify({'success': True, 'message': 'Registro exitoso'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'El email ya existe'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    
    hashed = hash_password(password)
    c.execute('SELECT id, email FROM users WHERE email = ? AND password = ?', (email, hashed))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user[0]
        session['email'] = user[1]
        return jsonify({'success': True, 'message': 'Login exitoso'})
    else:
        return jsonify({'success': False, 'message': 'Credenciales incorrectas'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/get_bots', methods=['GET'])
def get_bots():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'})
    
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute('SELECT id, bot_name, bot_token, status FROM bots WHERE user_id = ?', (session['user_id'],))
    bots = c.fetchall()
    conn.close()
    
    bots_list = []
    for bot in bots:
        bots_list.append({
            'id': bot[0],
            'name': bot[1] if bot[1] else 'Bot sin nombre',
            'token': bot[2][:10] + '...' + bot[2][-5:],
            'status': bot[3]
        })
    
    return jsonify({'success': True, 'bots': bots_list})

@app.route('/add_bot', methods=['POST'])
def add_bot():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'})
    
    data = request.json
    token = data.get('token')
    name = data.get('name', 'Mi Bot')
    
    if not token:
        return jsonify({'success': False, 'message': 'Token requerido'})
    
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute('INSERT INTO bots (user_id, bot_name, bot_token) VALUES (?, ?, ?)',
              (session['user_id'], name, token))
    conn.commit()
    bot_id = c.lastrowid
    conn.close()
    
    bot_manager.create_bot_file(bot_id, token)
    
    return jsonify({'success': True, 'message': 'Bot añadido correctamente', 'bot_id': bot_id})

@app.route('/start_bot/<int:bot_id>', methods=['POST'])
def start_bot(bot_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'})
    
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute('SELECT user_id, bot_token FROM bots WHERE id = ?', (bot_id,))
    bot = c.fetchone()
    
    if not bot or bot[0] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Bot no encontrado'})
    
    result = bot_manager.start_bot(bot_id, bot[1])
    
    if result:
        c.execute('UPDATE bots SET status = ? WHERE id = ?', ('running', bot_id))
        conn.commit()
    
    conn.close()
    return jsonify({'success': result, 'message': 'Bot iniciado' if result else 'Error al iniciar'})

@app.route('/stop_bot/<int:bot_id>', methods=['POST'])
def stop_bot(bot_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'})
    
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM bots WHERE id = ?', (bot_id,))
    bot = c.fetchone()
    
    if not bot or bot[0] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Bot no encontrado'})
    
    result = bot_manager.stop_bot(bot_id)
    
    if result:
        c.execute('UPDATE bots SET status = ? WHERE id = ?', ('stopped', bot_id))
        conn.commit()
    
    conn.close()
    return jsonify({'success': result, 'message': 'Bot detenido' if result else 'Error al detener'})

@app.route('/delete_bot/<int:bot_id>', methods=['DELETE'])
def delete_bot(bot_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'})
    
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM bots WHERE id = ?', (bot_id,))
    bot = c.fetchone()
    
    if not bot or bot[0] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Bot no encontrado'})
    
    bot_manager.stop_bot(bot_id)
    bot_manager.delete_bot_file(bot_id)
    
    c.execute('DELETE FROM commands WHERE bot_id = ?', (bot_id,))
    c.execute('DELETE FROM bots WHERE id = ?', (bot_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Bot eliminado'})

@app.route('/add_command/<int:bot_id>', methods=['POST'])
def add_command(bot_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'})
    
    data = request.json
    command_name = data.get('command')
    command_code = data.get('code')
    
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM bots WHERE id = ?', (bot_id,))
    bot = c.fetchone()
    
    if not bot or bot[0] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Bot no encontrado'})
    
    c.execute('INSERT INTO commands (bot_id, command_name, command_code) VALUES (?, ?, ?)',
              (bot_id, command_name, command_code))
    conn.commit()
    conn.close()
    
    bot_manager.update_bot_commands(bot_id)
    
    return jsonify({'success': True, 'message': 'Comando añadido'})

@app.route('/get_commands/<int:bot_id>', methods=['GET'])
def get_commands(bot_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'})
    
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM bots WHERE id = ?', (bot_id,))
    bot = c.fetchone()
    
    if not bot or bot[0] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Bot no encontrado'})
    
    c.execute('SELECT id, command_name, command_code FROM commands WHERE bot_id = ?', (bot_id,))
    commands = c.fetchall()
    conn.close()
    
    commands_list = [{'id': cmd[0], 'name': cmd[1], 'code': cmd[2]} for cmd in commands]
    
    return jsonify({'success': True, 'commands': commands_list})

@app.route('/delete_command/<int:command_id>', methods=['DELETE'])
def delete_command(command_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'})
    
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    
    c.execute('''SELECT bot_id FROM commands 
                 WHERE id = ? AND bot_id IN 
                 (SELECT id FROM bots WHERE user_id = ?)''', 
              (command_id, session['user_id']))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return jsonify({'success': False, 'message': 'Comando no encontrado'})
    
    bot_id = result[0]
    
    c.execute('DELETE FROM commands WHERE id = ?', (command_id,))
    conn.commit()
    conn.close()
    
    bot_manager.update_bot_commands(bot_id)
    
    return jsonify({'success': True, 'message': 'Comando eliminado'})

@app.route('/get_logs/<int:bot_id>', methods=['GET'])
def get_logs(bot_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'})
    
    logs = bot_manager.get_bot_logs(bot_id)
    return jsonify({'success': True, 'logs': logs})

if __name__ == '__main__':
    os.makedirs('bots', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
app.run(debug=False, host='0.0.0.0', port=port)