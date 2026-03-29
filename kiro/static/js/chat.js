// Disease prediction logic
document.addEventListener('DOMContentLoaded', function() {
    const predictBtn = document.getElementById('predictDiseaseBtn');
    if (predictBtn) {
        predictBtn.addEventListener('click', async function() {
            const symptomsText = document.getElementById('symptomsInput').value;
            const symptoms = symptomsText.split(',').map(s => s.trim()).filter(s => s);
            const resultDiv = document.getElementById('predictionResult');
            resultDiv.textContent = 'Predicting...';
            try {
                const response = await fetch('/predict-disease', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symptoms: symptoms })
                });
                if (!response.ok) {
                    throw new Error('Prediction failed');
                }
                const data = await response.json();
                resultDiv.textContent = 'Predicted Disease: ' + data.predicted_disease;
            } catch (err) {
                resultDiv.textContent = 'Error: ' + err.message;
            }
        });
    }
});
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
            'fr': 'Français (French)',
            'ar': 'العربية (Arabic)'
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

// Nearby hospitals (uses browser GPS)
// ...existing code...

// Nearby hospitals (uses browser GPS)
document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('nearbyHospitalsBtn');
    const resultsEl = document.getElementById('hospitalResults');

    if (!btn || !resultsEl) return;

    const renderMessage = (text, isError = false) => {
        resultsEl.innerHTML = '';
        const div = document.createElement('div');
        div.textContent = text;
        div.className = isError ? 'hospital-item hospital-disclaimer' : 'hospital-item';
        resultsEl.appendChild(div);
    };

    const setLoading = (isLoading) => {
        btn.disabled = isLoading;
        btn.textContent = isLoading ? 'Finding...' : 'Find Nearby Hospitals';
    };

    // NEW: tries multiple backend routes so frontend works even if route name differs
    const fetchHospitals = async (lat, lon) => {
        const endpoints = [
            '/hospitals',
            '/nearby-hospitals',
            '/nearby_hospitals',
            '/api/hospitals'
        ];

        let lastError = null;

        for (const base of endpoints) {
            const url = `${base}?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`;
            try {
                const resp = await fetch(url);
                if (resp.status === 404) continue; // try next endpoint
                if (!resp.ok) throw new Error(`HTTP ${resp.status} on ${base}`);
                return await resp.json();
            } catch (err) {
                lastError = err;
            }
        }

        throw lastError || new Error('No hospital endpoint found');
    };

    btn.addEventListener('click', async () => {
        if (!navigator.geolocation) {
            renderMessage('Geolocation is not supported in this browser.', true);
            return;
        }

        setLoading(true);
        renderMessage('Requesting location permission...');

        navigator.geolocation.getCurrentPosition(
            async (pos) => {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;

                try {
                    setLoading(true);
                    renderMessage('Searching hospitals near you...');

                    const data = await fetchHospitals(lat, lon);
                    const hospitals = data.hospitals || [];

                    resultsEl.innerHTML = '';
                    if (hospitals.length === 0) {
                        renderMessage('No hospitals found near your location right now. Please try again later.', true);
                        return;
                    }

                    hospitals.forEach((h) => {
                        const item = document.createElement('div');
                        item.className = 'hospital-item';

                        const title = document.createElement('div');
                        title.className = 'hospital-item-title';
                        title.textContent = h.name || 'Hospital';

                        const meta = document.createElement('div');
                        meta.className = 'hospital-item-meta';
                        meta.textContent = h.distance_km != null ? `~${h.distance_km} km away` : '';

                        item.appendChild(title);
                        item.appendChild(meta);
                        resultsEl.appendChild(item);
                    });
                } catch (err) {
                    console.error('Hospital lookup failed:', err);
                    renderMessage('Unable to look up hospitals right now. Please try again later.', true);
                } finally {
                    setLoading(false);
                }
            },
            (err) => {
                console.error('Geolocation error:', err);
                renderMessage('Location permission denied or unavailable. You can still use the chat for health advice.', true);
                setLoading(false);
            },
            { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
        );
    });
});

// ...existing code...

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