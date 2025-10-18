import sqlite3
import hashlib
import re
from datetime import datetime, timedelta
import secrets

class AuthManager:
    def __init__(self, db_path='database/users.db'):
        self.db_path = db_path
        self.sessions = {}
        
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        if len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres"
        return True, "OK"
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, email, password):
        if not self.validate_email(email):
            return False, "Email inválido"
        
        is_valid, msg = self.validate_password(password)
        if not is_valid:
            return False, msg
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            hashed = self.hash_password(password)
            c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed))
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            return True, user_id
        except sqlite3.IntegrityError:
            conn.close()
            return False, "El email ya está registrado"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def authenticate_user(self, email, password):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        hashed = self.hash_password(password)
        c.execute('SELECT id, email FROM users WHERE email = ? AND password = ?', (email, hashed))
        user = c.fetchone()
        conn.close()
        
        if user:
            return True, {'id': user[0], 'email': user[1]}
        else:
            return False, "Credenciales incorrectas"
    
    def get_user_by_id(self, user_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT id, email, created_at FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'email': user[1],
                'created_at': user[2]
            }
        return None
    
    def get_user_by_email(self, email):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT id, email, created_at FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'email': user[1],
                'created_at': user[2]
            }
        return None
    
    def change_password(self, user_id, old_password, new_password):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        old_hashed = self.hash_password(old_password)
        c.execute('SELECT id FROM users WHERE id = ? AND password = ?', (user_id, old_hashed))
        user = c.fetchone()
        
        if not user:
            conn.close()
            return False, "Contraseña actual incorrecta"
        
        is_valid, msg = self.validate_password(new_password)
        if not is_valid:
            conn.close()
            return False, msg
        
        new_hashed = self.hash_password(new_password)
        c.execute('UPDATE users SET password = ? WHERE id = ?', (new_hashed, user_id))
        conn.commit()
        conn.close()
        
        return True, "Contraseña actualizada"
    
    def delete_user(self, user_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('DELETE FROM commands WHERE bot_id IN (SELECT id FROM bots WHERE user_id = ?)', (user_id,))
            c.execute('DELETE FROM bots WHERE user_id = ?', (user_id,))
            c.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return True, "Usuario eliminado"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def get_user_stats(self, user_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM bots WHERE user_id = ?', (user_id,))
        total_bots = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM bots WHERE user_id = ? AND status = ?', (user_id, 'running'))
        active_bots = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM commands WHERE bot_id IN (SELECT id FROM bots WHERE user_id = ?)', (user_id,))
        total_commands = c.fetchone()[0]
        
        conn.close()
        
        return {
            'total_bots': total_bots,
            'active_bots': active_bots,
            'total_commands': total_commands
        }
    
    def create_session_token(self, user_id):
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(days=7)
        
        self.sessions[token] = {
            'user_id': user_id,
            'expiry': expiry
        }
        
        return token
    
    def validate_session_token(self, token):
        if token not in self.sessions:
            return False, None
        
        session = self.sessions[token]
        
        if datetime.now() > session['expiry']:
            del self.sessions[token]
            return False, None
        
        return True, session['user_id']
    
    def delete_session_token(self, token):
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False