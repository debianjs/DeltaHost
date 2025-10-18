let currentBotId = null;

document.addEventListener('DOMContentLoaded', function() {
    loadBots();
    lucide.createIcons();
    
    const btnAddBot = document.getElementById('btnAddBot');
    const addBotModal = document.getElementById('addBotModal');
    const closeAddBot = document.getElementById('closeAddBot');
    const addBotForm = document.getElementById('addBotForm');
    
    const commandsModal = document.getElementById('commandsModal');
    const closeCommands = document.getElementById('closeCommands');
    const addCommandForm = document.getElementById('addCommandForm');
    
    const logsModal = document.getElementById('logsModal');
    const closeLogs = document.getElementById('closeLogs');
    const refreshLogs = document.getElementById('refreshLogs');

    btnAddBot.addEventListener('click', function() {
        addBotModal.classList.add('active');
    });

    closeAddBot.addEventListener('click', function() {
        addBotModal.classList.remove('active');
    });

    closeCommands.addEventListener('click', function() {
        commandsModal.classList.remove('active');
    });

    closeLogs.addEventListener('click', function() {
        logsModal.classList.remove('active');
    });

    addBotModal.addEventListener('click', function(e) {
        if (e.target === addBotModal) {
            addBotModal.classList.remove('active');
        }
    });

    commandsModal.addEventListener('click', function(e) {
        if (e.target === commandsModal) {
            commandsModal.classList.remove('active');
        }
    });

    logsModal.addEventListener('click', function(e) {
        if (e.target === logsModal) {
            logsModal.classList.remove('active');
        }
    });

    addBotForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const token = document.getElementById('botToken').value;
        const name = document.getElementById('botName').value || 'Mi Bot';
        
        try {
            const response = await fetch('/add_bot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ token, name })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('Bot añadido correctamente', 'success');
                addBotModal.classList.remove('active');
                addBotForm.reset();
                loadBots();
            } else {
                showToast(data.message || 'Error al añadir bot', 'error');
            }
        } catch (error) {
            showToast('Error de conexión', 'error');
        }
    });

    addCommandForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const command = document.getElementById('commandName').value;
        const code = document.getElementById('commandCode').value;
        
        if (!currentBotId) {
            showToast('Error: No se ha seleccionado un bot', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/add_command/${currentBotId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ command, code })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('Comando añadido correctamente', 'success');
                addCommandForm.reset();
                loadCommands(currentBotId);
            } else {
                showToast(data.message || 'Error al añadir comando', 'error');
            }
        } catch (error) {
            showToast('Error de conexión', 'error');
        }
    });

    refreshLogs.addEventListener('click', function() {
        if (currentBotId) {
            loadLogs(currentBotId);
        }
    });
});

async function loadBots() {
    try {
        const response = await fetch('/get_bots');
        const data = await response.json();
        
        if (data.success) {
            const botsGrid = document.getElementById('botsGrid');
            
            if (data.bots.length === 0) {
                botsGrid.innerHTML = `
                    <div class="empty-state">
                        <i data-lucide="bot" style="width: 80px; height: 80px; margin-bottom: 20px; opacity: 0.5;"></i>
                        <h3>No tienes bots todavía</h3>
                        <p>Añade tu primer bot para empezar</p>
                    </div>
                `;
                lucide.createIcons();
                return;
            }
            
            botsGrid.innerHTML = data.bots.map(bot => `
                <div class="bot-card">
                    <div class="bot-header">
                        <div class="bot-name"><i data-lucide="bot"></i> ${bot.name}</div>
                        <span class="bot-status ${bot.status}">${bot.status === 'running' ? 'Activo' : 'Detenido'}</span>
                    </div>
                    <div class="bot-token"><i data-lucide="key"></i> ${bot.token}</div>
                    <div class="bot-actions">
                        ${bot.status === 'stopped' ? 
                            `<button class="btn-bot start" onclick="startBot(${bot.id})"><i data-lucide="play"></i> Iniciar</button>` :
                            `<button class="btn-bot stop" onclick="stopBot(${bot.id})"><i data-lucide="stop-circle"></i> Detener</button>`
                        }
                        <button class="btn-bot" onclick="openCommands(${bot.id})"><i data-lucide="code-2"></i> Comandos</button>
                        <button class="btn-bot" onclick="openLogs(${bot.id})"><i data-lucide="terminal"></i> Consola</button>
                        <button class="btn-bot delete" onclick="deleteBot(${bot.id})"><i data-lucide="trash-2"></i> Eliminar</button>
                    </div>
                </div>
            `).join('');
            
            lucide.createIcons();
        }
    } catch (error) {
        showToast('Error al cargar bots', 'error');
    }
}

async function startBot(botId) {
    try {
        const response = await fetch(`/start_bot/${botId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Bot iniciado correctamente', 'success');
            loadBots();
        } else {
            showToast(data.message || 'Error al iniciar bot', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
    }
}

async function stopBot(botId) {
    try {
        const response = await fetch(`/stop_bot/${botId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Bot detenido correctamente', 'success');
            loadBots();
        } else {
            showToast(data.message || 'Error al detener bot', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
    }
}

async function deleteBot(botId) {
    if (!confirm('¿Estás seguro de que quieres eliminar este bot?')) {
        return;
    }
    
    try {
        const response = await fetch(`/delete_bot/${botId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Bot eliminado correctamente', 'success');
            loadBots();
        } else {
            showToast(data.message || 'Error al eliminar bot', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
    }
}

async function openCommands(botId) {
    window.location.href = `/editor?bot_id=${botId}`;
}

async function loadCommands(botId) {
    try {
        const response = await fetch(`/get_commands/${botId}`);
        const data = await response.json();
        
        if (data.success) {
            const commandsList = document.getElementById('commandsList');
            
            if (data.commands.length === 0) {
                commandsList.innerHTML = '<p style="color: rgba(255,255,255,0.5);"><i data-lucide="info"></i> No hay comandos todavía. Añade uno abajo.</p>';
                lucide.createIcons();
                return;
            }
            
            commandsList.innerHTML = data.commands.map(cmd => `
                <div class="command-item">
                    <div class="command-name"><i data-lucide="hash"></i> /${cmd.name}</div>
                    <div class="command-code">${escapeHtml(cmd.code)}</div>
                </div>
            `).join('');
            
            lucide.createIcons();
        }
    } catch (error) {
        showToast('Error al cargar comandos', 'error');
    }
}

async function openLogs(botId) {
    currentBotId = botId;
    const logsModal = document.getElementById('logsModal');
    logsModal.classList.add('active');
    loadLogs(botId);
    lucide.createIcons();
}

async function loadLogs(botId) {
    try {
        const response = await fetch(`/get_logs/${botId}`);
        const data = await response.json();
        
        if (data.success) {
            const consoleOutput = document.getElementById('consoleOutput');
            consoleOutput.textContent = data.logs || 'No hay logs disponibles';
            consoleOutput.scrollTop = consoleOutput.scrollHeight;
        }
    } catch (error) {
        showToast('Error al cargar logs', 'error');
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function showToast(message, type) {
    const toast = document.getElementById('messageToast');
    toast.textContent = message;
    toast.className = 'message-toast ' + type;
    
    setTimeout(() => {
        toast.className = 'message-toast';
    }, 3000);
}