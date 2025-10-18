import subprocess
import os
import signal
import sqlite3
from datetime import datetime

class BotManager:
    def __init__(self):
        self.running_bots = {}
        
    def create_bot_file(self, bot_id, token):
        bot_code = f"""const TelegramBot = require('node-telegram-bot-api');

const token = '{token}';
const bot = new TelegramBot(token, {{polling: true}});

console.log('Bot iniciado correctamente - ID: {bot_id}');

bot.on('message', (msg) => {{
    console.log('Mensaje recibido de:', msg.from.username || msg.from.first_name);
}});

bot.onText(/\/start/, (msg) => {{
    const chatId = msg.chat.id;
    bot.sendMessage(chatId, '¡Hola! Soy un bot alojado en DeltaHost 🚀');
}});
"""
        
        bot_file_path = f'bots/bot_{bot_id}.js'
        with open(bot_file_path, 'w', encoding='utf-8') as f:
            f.write(bot_code)
        
        return bot_file_path
    
    def update_bot_commands(self, bot_id):
        conn = sqlite3.connect('database/users.db')
        c = conn.cursor()
        
        c.execute('SELECT bot_token FROM bots WHERE id = ?', (bot_id,))
        token_row = c.fetchone()
        if not token_row:
            conn.close()
            return False
        
        token = token_row[0]
        
        c.execute('SELECT command_name, command_code FROM commands WHERE bot_id = ?', (bot_id,))
        commands = c.fetchall()
        conn.close()
        
        bot_code = f"""const TelegramBot = require('node-telegram-bot-api');

const token = '{token}';
const bot = new TelegramBot(token, {{polling: true}});

console.log('Bot iniciado correctamente - ID: {bot_id}');

bot.on('message', (msg) => {{
    console.log('Mensaje recibido de:', msg.from.username || msg.from.first_name);
}});

bot.onText(/\/start/, (msg) => {{
    const chatId = msg.chat.id;
    bot.sendMessage(chatId, '¡Hola! Soy un bot alojado en DeltaHost 🚀');
}});
"""
        
        for cmd in commands:
            command_name = cmd[0]
            command_code = cmd[1]
            
            bot_code += f"""
bot.onText(/\/{command_name}/, (msg) => {{
    const chatId = msg.chat.id;
    try {{
        {command_code}
    }} catch(error) {{
        console.error('Error en comando /{command_name}:', error);
        bot.sendMessage(chatId, 'Error al ejecutar el comando');
    }}
}});
"""
        
        bot_file_path = f'bots/bot_{bot_id}.js'
        with open(bot_file_path, 'w', encoding='utf-8') as f:
            f.write(bot_code)
        
        if bot_id in self.running_bots:
            self.stop_bot(bot_id)
            conn = sqlite3.connect('database/users.db')
            c = conn.cursor()
            c.execute('SELECT bot_token FROM bots WHERE id = ?', (bot_id,))
            token_result = c.fetchone()
            conn.close()
            if token_result:
                self.start_bot(bot_id, token_result[0])
        
        return True
    
    def start_bot(self, bot_id, token):
        if bot_id in self.running_bots:
            return False
        
        bot_file = f'bots/bot_{bot_id}.js'
        if not os.path.exists(bot_file):
            self.create_bot_file(bot_id, token)
        
        log_file_path = f'logs/bot_{bot_id}.log'
        log_file = open(log_file_path, 'a', encoding='utf-8')
        
        try:
            process = subprocess.Popen(
                ['node', bot_file],
                stdout=log_file,
                stderr=log_file,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self.running_bots[bot_id] = {
                'process': process,
                'log_file': log_file,
                'started_at': datetime.now()
            }
            
            log_file.write(f"\n{'='*50}\n")
            log_file.write(f"Bot {bot_id} iniciado - {datetime.now()}\n")
            log_file.write(f"{'='*50}\n\n")
            log_file.flush()
            
            return True
        except Exception as e:
            log_file.write(f"Error al iniciar bot: {str(e)}\n")
            log_file.close()
            return False
    
    def stop_bot(self, bot_id):
        if bot_id not in self.running_bots:
            return False
        
        bot_info = self.running_bots[bot_id]
        process = bot_info['process']
        log_file = bot_info['log_file']
        
        try:
            if os.name != 'nt':
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()
            
            process.wait(timeout=5)
        except Exception as e:
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
            except:
                pass
        
        log_file.write(f"\n{'='*50}\n")
        log_file.write(f"Bot {bot_id} detenido - {datetime.now()}\n")
        log_file.write(f"{'='*50}\n\n")
        log_file.close()
        
        del self.running_bots[bot_id]
        return True
    
    def delete_bot_file(self, bot_id):
        bot_file = f'bots/bot_{bot_id}.js'
        log_file = f'logs/bot_{bot_id}.log'
        
        try:
            if os.path.exists(bot_file):
                os.remove(bot_file)
            if os.path.exists(log_file):
                os.remove(log_file)
            return True
        except:
            return False
    
    def get_bot_logs(self, bot_id):
        log_file = f'logs/bot_{bot_id}.log'
        
        if not os.path.exists(log_file):
            return "No hay logs disponibles"
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return ''.join(lines[-100:])
        except:
            return "Error al leer logs"
    
    def get_running_bots(self):
        return list(self.running_bots.keys())
