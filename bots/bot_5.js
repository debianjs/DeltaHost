import TelegramBot from 'node-telegram-bot-api';

const token = '8299609526:AAF9P6nok2SE8ogCW-vTncHQRuJHrO3FNkg';
const bot = new TelegramBot(token, {polling: true});

console.log('Bot iniciado correctamente - ID: 5');

bot.on('message', (msg) => {
    console.log('Mensaje recibido de:', msg.from.username || msg.from.first_name);
});

bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    bot.sendMessage(chatId, '¡Hola! Soy un bot alojado en DeltaHost 🚀');
});

bot.onText(/\/help/, (msg) => {
    const chatId = msg.chat.id;
    try {
        bot.sendMessage(chatId, '¡Hola! Soy un bot alojado en DeltaHost 🚀');
    } catch(error) {
        console.error('Error en comando /help:', error);
        bot.sendMessage(chatId, 'Error al ejecutar el comando');
    }
});

bot.onText(/\/kick/, (msg) => {
    const chatId = msg.chat.id;
    try {
        const chatId = msg.chat.id;
const userId = msg.from.id;

// Verificar si el bot tiene permisos de administrador
bot.getChatMember(chatId, (await bot.getMe()).id).then(async (botMember) => {
    if (!botMember.can_restrict_members) {
        return bot.sendMessage(chatId, '❌ No tengo permisos para expulsar usuarios');
    }
    
    // Verificar si el usuario que ejecuta el comando es admin
    bot.getChatMember(chatId, userId).then(async (userMember) => {
        if (userMember.status !== 'creator' && userMember.status !== 'administrator') {
            return bot.sendMessage(chatId, '❌ Solo los administradores pueden usar este comando');
        }
        
        // Extraer el usuario mencionado
        const text = msg.text;
        const args = text.split(' ');
        
        if (args.length < 2) {
            return bot.sendMessage(chatId, '⚠️ Uso: /kick @usuario o responde a un mensaje');
        }
        
        let targetUserId = null;
        
        // Si es una respuesta a un mensaje
        if (msg.reply_to_message) {
            targetUserId = msg.reply_to_message.from.id;
        } 
        // Si menciona un usuario con @
        else if (args[1].startsWith('@')) {
            const username = args[1].substring(1);
            try {
                const chat = await bot.getChat('@' + username);
                targetUserId = chat.id;
            } catch (error) {
                return bot.sendMessage(chatId, '❌ No se encontró el usuario mencionado');
            }
        }
        // Si proporciona un ID directamente
        else if (!isNaN(args[1])) {
            targetUserId = parseInt(args[1]);
        }
        
        if (!targetUserId) {
            return bot.sendMessage(chatId, '❌ Usuario no válido');
        }
        
        // Verificar que no sea el bot mismo o el creador del grupo
        if (targetUserId === (await bot.getMe()).id) {
            return bot.sendMessage(chatId, '😅 No puedo expulsarme a mí mismo');
        }
        
        bot.getChatMember(chatId, targetUserId).then(async (targetMember) => {
            if (targetMember.status === 'creator') {
                return bot.sendMessage(chatId, '❌ No puedo expulsar al creador del grupo');
            }
            
            if (targetMember.status === 'administrator') {
                return bot.sendMessage(chatId, '❌ No puedo expulsar a otros administradores');
            }
            
            // Expulsar al usuario
            bot.kickChatMember(chatId, targetUserId).then(() => {
                const targetName = msg.reply_to_message ? 
                    (msg.reply_to_message.from.first_name || msg.reply_to_message.from.username) : 
                    args[1];
                
                bot.sendMessage(chatId, `✅ Usuario ${targetName} expulsado del grupo`);
                
                // Desbanear después de 30 segundos para que pueda volver si tiene el link
                setTimeout(() => {
                    bot.unbanChatMember(chatId, targetUserId);
                }, 30000);
            }).catch(error => {
                bot.sendMessage(chatId, '❌ Error al expulsar al usuario: ' + error.message);
            });
        }).catch(error => {
            bot.sendMessage(chatId, '❌ Error al verificar el usuario: ' + error.message);
        });
    }).catch(error => {
        bot.sendMessage(chatId, '❌ Error al verificar permisos: ' + error.message);
    });
}).catch(error => {
    bot.sendMessage(chatId, '❌ Error al verificar permisos del bot: ' + error.message);
});
    } catch(error) {
        console.error('Error en comando /kick:', error);
        bot.sendMessage(chatId, 'Error al ejecutar el comando');
    }
});
