let currentBotId = null;
let currentCommandId = null;
let editor = null;
let commands = [];

const urlParams = new URLSearchParams(window.location.search);
currentBotId = urlParams.get('bot_id');

document.addEventListener('DOMContentLoaded', function() {
    if (!currentBotId) {
        window.location.href = '/dashboard';
        return;
    }
    
    initEditor();
    loadBotInfo();
    loadCommands();
    
    const btnNewCommand = document.getElementById('btnNewCommand');
    const newCommandModal = document.getElementById('newCommandModal');
    const closeNewCommand = document.getElementById('closeNewCommand');
    const newCommandForm = document.getElementById('newCommandForm');
    const btnSave = document.getElementById('btnSave');
    const btnDelete = document.getElementById('btnDelete');
    
    btnNewCommand.addEventListener('click', function() {
        newCommandModal.classList.add('active');
        lucide.createIcons();
    });
    
    closeNewCommand.addEventListener('click', function() {
        newCommandModal.classList.remove('active');
    });
    
    newCommandModal.addEventListener('click', function(e) {
        if (e.target === newCommandModal) {
            newCommandModal.classList.remove('active');
        }
    });
    
    newCommandForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const commandName = document.getElementById('newCommandName').value;
        const defaultCode = `bot.sendMessage(chatId, '¡Hola! Este es el comando /${commandName}');`;
        
        try {
            const response = await fetch(`/add_command/${currentBotId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    command: commandName, 
                    code: defaultCode 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('Comando creado correctamente', 'success');
                newCommandModal.classList.remove('active');
                newCommandForm.reset();
                loadCommands();
            } else {
                showToast(data.message || 'Error al crear comando', 'error');
            }
        } catch (error) {
            showToast('Error de conexión', 'error');
        }
    });
    
    btnSave.addEventListener('click', saveCommand);
    btnDelete.addEventListener('click', deleteCommand);
    
    editor.on('cursorActivity', function() {
        const cursor = editor.getCursor();
        document.getElementById('lineInfo').textContent = `Línea ${cursor.line + 1}, Columna ${cursor.ch + 1}`;
    });
});

function initEditor() {
    const textarea = document.getElementById('codeEditor');
    
    editor = CodeMirror.fromTextArea(textarea, {
        mode: 'javascript',
        theme: 'dracula',
        lineNumbers: true,
        autoCloseBrackets: true,
        matchBrackets: true,
        indentUnit: 4,
        tabSize: 4,
        lineWrapping: true,
        extraKeys: {
            'Ctrl-S': function() {
                saveCommand();
            },
            'Cmd-S': function() {
                saveCommand();
            }
        }
    });
    
    editor.setValue('// Selecciona un comando de la barra lateral para editar\n// o crea uno nuevo con el botón +\n');
    editor.setOption('readOnly', true);
}

async function loadBotInfo() {
    try {
        const response = await fetch('/get_bots');
        const data = await response.json();
        
        if (data.success) {
            const bot = data.bots.find(b => b.id == currentBotId);
            if (bot) {
                document.getElementById('botName').textContent = bot.name;
                document.getElementById('botStatus').textContent = bot.status === 'running' ? '🟢 Activo' : '🔴 Detenido';
            }
        }
    } catch (error) {
        console.error('Error al cargar info del bot:', error);
    }
}

async function loadCommands() {
    try {
        const response = await fetch(`/get_commands/${currentBotId}`);
        const data = await response.json();
        
        if (data.success) {
            commands = data.commands;
            const commandsList = document.getElementById('commandsList');
            
            if (commands.length === 0) {
                commandsList.innerHTML = '<p style="color: rgba(255,255,255,0.5); text-align: center; padding: 20px;">No hay comandos todavía</p>';
                return;
            }
            
            commandsList.innerHTML = commands.map(cmd => `
                <div class="command-item" onclick="selectCommand(${cmd.id})">
                    <i data-lucide="hash"></i>
                    /${cmd.name}
                </div>
            `).join('');
            
            lucide.createIcons();
        }
    } catch (error) {
        showToast('Error al cargar comandos', 'error');
    }
}

function selectCommand(commandId) {
    currentCommandId = commandId;
    const command = commands.find(cmd => cmd.id === commandId);
    
    if (!command) return;
    
    document.querySelectorAll('.command-item').forEach(item => {
        item.classList.remove('active');
    });
    
    event.target.closest('.command-item').classList.add('active');
    
    document.getElementById('currentCommand').textContent = `/${command.name}`;
    editor.setValue(command.code);
    editor.setOption('readOnly', false);
    
    document.getElementById('statusIndicator').textContent = 'Listo';
    document.getElementById('statusIndicator').style.color = '#27c93f';
}

async function saveCommand() {
    if (!currentCommandId) {
        showToast('Selecciona un comando primero', 'error');
        return;
    }
    
    const command = commands.find(cmd => cmd.id === currentCommandId);
    if (!command) return;
    
    const code = editor.getValue();
    
    document.getElementById('statusIndicator').textContent = 'Guardando...';
    document.getElementById('statusIndicator').style.color = '#ffbd2e';
    
    try {
        const response = await fetch(`/delete_command/${currentCommandId}`, {
            method: 'DELETE'
        });
        
        const deleteData = await response.json();
        
        if (deleteData.success) {
            const addResponse = await fetch(`/add_command/${currentBotId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    command: command.name, 
                    code: code 
                })
            });
            
            const addData = await addResponse.json();
            
            if (addData.success) {
                showToast('Comando guardado correctamente', 'success');
                document.getElementById('statusIndicator').textContent = 'Guardado';
                document.getElementById('statusIndicator').style.color = '#27c93f';
                
                setTimeout(() => {
                    document.getElementById('statusIndicator').textContent = 'Listo';
                }, 2000);
                
                await loadCommands();
                
                const updatedCommand = commands.find(cmd => cmd.name === command.name);
                if (updatedCommand) {
                    currentCommandId = updatedCommand.id;
                }
            } else {
                showToast(addData.message || 'Error al guardar', 'error');
                document.getElementById('statusIndicator').textContent = 'Error';
                document.getElementById('statusIndicator').style.color = '#ff5f56';
            }
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
        document.getElementById('statusIndicator').textContent = 'Error';
        document.getElementById('statusIndicator').style.color = '#ff5f56';
    }
}

async function deleteCommand() {
    if (!currentCommandId) {
        showToast('Selecciona un comando primero', 'error');
        return;
    }
    
    const command = commands.find(cmd => cmd.id === currentCommandId);
    if (!command) return;
    
    if (!confirm(`¿Estás seguro de que quieres eliminar el comando /${command.name}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/delete_command/${currentCommandId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Comando eliminado correctamente', 'success');
            currentCommandId = null;
            editor.setValue('// Selecciona un comando de la barra lateral para editar\n// o crea uno nuevo con el botón +\n');
            editor.setOption('readOnly', true);
            document.getElementById('currentCommand').textContent = 'Selecciona un comando';
            loadCommands();
        } else {
            showToast(data.message || 'Error al eliminar comando', 'error');
        }
    } catch (error) {
        showToast('Error de conexión', 'error');
    }
}

function showToast(message, type) {
    const toast = document.getElementById('messageToast');
    toast.textContent = message;
    toast.className = 'message-toast ' + type;
    
    setTimeout(() => {
        toast.className = 'message-toast';
    }, 3000);
}