document.addEventListener('DOMContentLoaded', function() {
    const chatbotIcon = document.getElementById('chatbot-icon');
    const chatbotWindow = document.getElementById('chatbot-window');
    const closeChat = document.getElementById('close-chat');
    const sendMessage = document.getElementById('send-message');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');

    chatbotIcon.addEventListener('click', function() {
        chatbotWindow.classList.remove('hidden');
        chatbotIcon.style.display = 'none';
    });

    closeChat.addEventListener('click', function() {
        chatbotWindow.classList.add('hidden');
        chatbotIcon.style.display = 'flex';
    });

    sendMessage.addEventListener('click', sendUserMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendUserMessage();
        }
    });

    function sendUserMessage() {
        const message = userInput.value.trim();
        if (message) {
            addMessage('user', message);
            userInput.value = '';
            // Simulate bot response (replace with actual API call later)
            setTimeout(() => {
                const botReply = "Thank you for your message. This is a placeholder response from the SRM TRP Assistant.";
                addMessage('bot', botReply);
            }, 1000);
        }
    }

    function addMessage(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        messageElement.textContent = message;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});