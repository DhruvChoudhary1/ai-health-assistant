class HealthChatbot {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.languageSelect = document.getElementById('languageSelect');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.loadingModal = document.getElementById('loadingModal');
        
        this.currentLanguage = 'en';
        this.isProcessing = false;
        
        this.initializeEventListeners();
        this.updateCharCount();
    }
    
    initializeEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Character count update
        this.messageInput.addEventListener('input', () => this.updateCharCount());
        
        // Language change
        this.languageSelect.addEventListener('change', (e) => {
            this.currentLanguage = e.target.value;
            this.showLanguageChangeMessage();
        });
        
        // Auto-resize input
        this.messageInput.addEventListener('input', () => this.autoResizeInput());
    }
    
    updateCharCount() {
        const charCount = this.messageInput.value.length;
        const charCountElement = document.querySelector('.char-count');
        charCountElement.textContent = `${charCount}/500`;
        
        if (charCount > 450) {
            charCountElement.style.color = '#ef4444';
        } else if (charCount > 400) {
            charCountElement.style.color = '#f59e0b';
        } else {
            charCountElement.style.color = '#64748b';
        }
    }
    
    autoResizeInput() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isProcessing) {
            return;
        }
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.updateCharCount();
        this.autoResizeInput();
        
        // Show processing state
        this.setProcessingState(true);
        
        try {
            // Send message to backend
            const response = await this.sendToBackend(message);
            
            // Add bot response to chat
            this.addMessage(response.response, 'bot', response.citations);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage(
                'I apologize, but I\'m experiencing technical difficulties. Please try again later.',
                'bot'
            );
        } finally {
            this.setProcessingState(false);
        }
    }
    
    async sendToBackend(message) {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                language: this.currentLanguage
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    addMessage(content, sender, citations = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Add main content
        const contentP = document.createElement('p');
        contentP.textContent = content;
        contentDiv.appendChild(contentP);
        
        // Add citations if available
        if (citations && citations.length > 0) {
            const citationsDiv = this.createCitationsElement(citations);
            contentDiv.appendChild(citationsDiv);
        }
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    createCitationsElement(citations) {
        const citationsDiv = document.createElement('div');
        citationsDiv.className = 'citations';
        
        const citationsTitle = document.createElement('h4');
        citationsTitle.innerHTML = '<i class="fas fa-book"></i> Sources:';
        citationsDiv.appendChild(citationsTitle);
        
        const citationsList = document.createElement('ul');
        citationsList.className = 'citation-list';
        
        citations.forEach(citation => {
            const listItem = document.createElement('li');
            listItem.className = 'citation-item';
            
            const badge = document.createElement('span');
            badge.className = 'citation-badge';
            badge.textContent = citation.id;
            
            const source = document.createElement('span');
            source.textContent = citation.source;
            
            listItem.appendChild(badge);
            listItem.appendChild(source);
            
            if (citation.url) {
                const link = document.createElement('a');
                link.href = citation.url;
                link.target = '_blank';
                link.className = 'citation-link';
                link.innerHTML = '<i class="fas fa-external-link-alt"></i>';
                listItem.appendChild(link);
            }
            
            citationsList.appendChild(listItem);
        });
        
        citationsDiv.appendChild(citationsList);
        return citationsDiv;
    }
    
    setProcessingState(isProcessing) {
        this.isProcessing = isProcessing;
        this.sendButton.disabled = isProcessing;
        this.messageInput.disabled = isProcessing;
        
        if (isProcessing) {
            this.showTypingIndicator();
            this.loadingModal.style.display = 'flex';
        } else {
            this.hideTypingIndicator();
            this.loadingModal.style.display = 'none';
        }
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    showLanguageChangeMessage() {
        const languageNames = {
            'en': 'English',
            'hi': 'हिंदी (Hindi)',
            'es': 'Español (Spanish)',
            'fr': 'Français (French)'
        };
        
        const message = `Language changed to ${languageNames[this.currentLanguage]}. You can now ask questions in this language.`;
        this.addMessage(message, 'bot');
    }
    
    // Utility method to format time
    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    // Method to handle voice input (future enhancement)
    startVoiceInput() {
        if ('webkitSpeechRecognition' in window) {
            const recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = this.getVoiceLanguageCode();
            
            recognition.onstart = () => {
                console.log('Voice recognition started');
            };
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.messageInput.value = transcript;
                this.updateCharCount();
            };
            
            recognition.onerror = (event) => {
                console.error('Voice recognition error:', event.error);
            };
            
            recognition.start();
        } else {
            alert('Voice recognition not supported in this browser');
        }
    }
    
    getVoiceLanguageCode() {
        const voiceCodes = {
            'en': 'en-US',
            'hi': 'hi-IN',
            'es': 'es-ES',
            'fr': 'fr-FR'
        };
        return voiceCodes[this.currentLanguage] || 'en-US';
    }
}

// Initialize the chatbot when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new HealthChatbot();
});

// Add some helpful utility functions
window.healthChatUtils = {
    // Copy message to clipboard
    copyToClipboard: (text) => {
        navigator.clipboard.writeText(text).then(() => {
            console.log('Text copied to clipboard');
        });
    },
    
    // Share message via Web Share API
    shareMessage: (text) => {
        if (navigator.share) {
            navigator.share({
                title: 'Health Information',
                text: text
            });
        }
    },
    
    // Download chat history
    downloadChatHistory: () => {
        const messages = document.querySelectorAll('.message');
        let chatHistory = 'AI Health Chatbot - Chat History\n\n';
        
        messages.forEach((message, index) => {
            const isUser = message.classList.contains('user-message');
            const content = message.querySelector('.message-content p').textContent;
            const sender = isUser ? 'You' : 'AI Assistant';
            
            chatHistory += `${sender}: ${content}\n\n`;
        });
        
        const blob = new Blob([chatHistory], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `health-chat-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }
};