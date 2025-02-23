document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const newChatBtn = document.getElementById('new-chat-btn');
    const chatMode = document.body.dataset.chatMode; // Definido no HTML

    // Envio de mensagem
    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = userInput.value.trim();
            
            if (!message) return;

            try {
                const response = await fetch('/send_message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, mode: chatMode })
                });

                if (!response.ok) throw new Error('Erro na resposta do servidor');
                
                const data = await response.json();
                appendMessage(message, 'user');
                appendMessage(data.response, 'bot');
                userInput.value = '';
                chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll
            } catch (error) {
                console.error('Erro:', error);
                appendMessage('Erro ao processar sua mensagem.', 'error');
            }
        });
    }

    // Nova conversa
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            chatMessages.innerHTML = '';
        });
    }

    // Helper para adicionar mensagens
    function appendMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
    }
});