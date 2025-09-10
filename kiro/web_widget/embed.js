/**
 * Health Chatbot Widget Embed Script
 * 
 * Usage:
 * <script src="https://your-domain.com/widget/embed.js"></script>
 * <script>
 *   HealthChatbotWidget.init({
 *     apiEndpoint: 'https://your-api-domain.com',
 *     theme: 'blue', // 'blue', 'green', 'purple'
 *     position: 'bottom-right', // 'bottom-right', 'bottom-left'
 *     language: 'en' // default language
 *   });
 * </script>
 */

(function() {
    'use strict';
    
    const HealthChatbotWidget = {
        config: {
            apiEndpoint: 'http://localhost:8000',
            theme: 'blue',
            position: 'bottom-right',
            language: 'en'
        },
        
        init: function(options = {}) {
            // Merge options with default config
            this.config = { ...this.config, ...options };
            
            // Check if widget already exists
            if (document.getElementById('health-chatbot-widget-container')) {
                console.warn('Health Chatbot Widget already initialized');
                return;
            }
            
            // Create and inject widget
            this.createWidget();
            this.injectStyles();
            this.initializeWidget();
        },
        
        createWidget: function() {
            const widgetHTML = `
                <div id="health-chatbot-widget-container">
                    <!-- Widget Toggle Button -->
                    <button class="hcw-toggle" id="hcwToggle">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
                        </svg>
                    </button>

                    <!-- Widget Container -->
                    <div class="hcw-widget" id="hcwWidget">
                        <!-- Widget Header -->
                        <div class="hcw-header">
                            <div class="hcw-title">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M19 8l-4 4h3c0 3.31-2.69 6-6 6-1.01 0-1.97-.25-2.8-.7l-1.46 1.46C8.97 19.54 10.43 20 12 20c4.42 0 8-3.58 8-8h3l-4-4zM6 12c0-3.31 2.69-6 6-6 1.01 0 1.97.25 2.8.7l1.46-1.46C15.03 4.46 13.57 4 12 4c-4.42 0-8 3.58-8 8H1l4 4 4-4H6z"/>
                                </svg>
                                Health Assistant
                            </div>
                            <button class="hcw-close" id="hcwClose">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                                </svg>
                            </button>
                        </div>

                        <!-- Widget Messages -->
                        <div class="hcw-messages" id="hcwMessages">
                            <div class="hcw-message hcw-bot">
                                <div class="hcw-message-content">
                                    Hi! I'm your AI Health Assistant. I can help with health questions and provide medical information.
                                    <br><br><strong>Disclaimer:</strong> This is for educational purposes only. Always consult healthcare professionals for medical advice.
                                </div>
                            </div>
                            
                            <!-- Typing Indicator -->
                            <div class="hcw-typing" id="hcwTyping">
                                <div class="hcw-typing-content">
                                    <span>AI is typing</span>
                                    <div class="hcw-typing-dots">
                                        <div class="hcw-dot"></div>
                                        <div class="hcw-dot"></div>
                                        <div class="hcw-dot"></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Widget Input -->
                        <div class="hcw-input-container">
                            <div class="hcw-language-selector">
                                <select id="hcwLanguage" class="hcw-language">
                                    <option value="en">🇺🇸 English</option>
                                    <option value="hi">🇮🇳 हिंदी</option>
                                    <option value="es">🇪🇸 Español</option>
                                    <option value="fr">🇫🇷 Français</option>
                                </select>
                            </div>
                            <div class="hcw-input-wrapper">
                                <input type="text" class="hcw-input" id="hcwInput" placeholder="Ask about your health..." maxlength="300">
                                <button class="hcw-send" id="hcwSend">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Create container and add to body
            const container = document.createElement('div');
            container.innerHTML = widgetHTML;
            document.body.appendChild(container.firstElementChild);
        },
        
        injectStyles: function() {
            const styles = `
                #health-chatbot-widget-container {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    z-index: 999999;
                }
                
                .hcw-toggle {
                    position: fixed;
                    ${this.config.position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
                    ${this.config.position.includes('bottom') ? 'bottom: 20px;' : 'top: 20px;'}
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    border: none;
                    background: ${this.getThemeColor()};
                    color: white;
                    cursor: pointer;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                    transition: all 0.3s ease;
                    z-index: 1000000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .hcw-toggle:hover {
                    transform: scale(1.1);
                    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
                }
                
                .hcw-toggle.hidden {
                    display: none;
                }
                
                .hcw-widget {
                    position: fixed;
                    ${this.config.position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
                    ${this.config.position.includes('bottom') ? 'bottom: 20px;' : 'top: 20px;'}
                    width: 350px;
                    height: 500px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
                    display: none;
                    flex-direction: column;
                    overflow: hidden;
                    z-index: 1000000;
                }
                
                .hcw-widget.open {
                    display: flex;
                }
                
                .hcw-header {
                    background: ${this.getThemeColor()};
                    color: white;
                    padding: 16px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .hcw-title {
                    font-weight: 600;
                    font-size: 16px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .hcw-close {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 4px;
                    transition: background 0.2s ease;
                }
                
                .hcw-close:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
                
                .hcw-messages {
                    flex: 1;
                    padding: 16px;
                    overflow-y: auto;
                    background: #f8fafc;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
                
                .hcw-message {
                    max-width: 85%;
                    animation: slideIn 0.3s ease;
                }
                
                .hcw-message.hcw-user {
                    align-self: flex-end;
                }
                
                .hcw-message.hcw-bot {
                    align-self: flex-start;
                }
                
                .hcw-message-content {
                    padding: 12px 16px;
                    border-radius: 12px;
                    font-size: 14px;
                    line-height: 1.4;
                }
                
                .hcw-bot .hcw-message-content {
                    background: white;
                    border: 1px solid #e2e8f0;
                    color: #334155;
                }
                
                .hcw-user .hcw-message-content {
                    background: ${this.getThemeColor()};
                    color: white;
                }
                
                .hcw-typing {
                    display: none;
                    align-self: flex-start;
                    max-width: 85%;
                }
                
                .hcw-typing.show {
                    display: block;
                }
                
                .hcw-typing-content {
                    background: white;
                    border: 1px solid #e2e8f0;
                    padding: 12px 16px;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 14px;
                    color: #64748b;
                }
                
                .hcw-typing-dots {
                    display: flex;
                    gap: 2px;
                }
                
                .hcw-dot {
                    width: 4px;
                    height: 4px;
                    background: #64748b;
                    border-radius: 50%;
                    animation: typing 1.4s infinite;
                }
                
                .hcw-dot:nth-child(2) { animation-delay: 0.2s; }
                .hcw-dot:nth-child(3) { animation-delay: 0.4s; }
                
                .hcw-input-container {
                    padding: 16px;
                    background: white;
                    border-top: 1px solid #e2e8f0;
                }
                
                .hcw-language-selector {
                    margin-bottom: 12px;
                }
                
                .hcw-language {
                    width: 100%;
                    padding: 8px 12px;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    font-size: 12px;
                    background: white;
                    color: #334155;
                }
                
                .hcw-input-wrapper {
                    display: flex;
                    gap: 8px;
                    align-items: center;
                }
                
                .hcw-input {
                    flex: 1;
                    padding: 12px 16px;
                    border: 1px solid #e2e8f0;
                    border-radius: 24px;
                    font-size: 14px;
                    outline: none;
                    transition: border-color 0.2s ease;
                }
                
                .hcw-input:focus {
                    border-color: ${this.getThemeColor()};
                }
                
                .hcw-send {
                    width: 40px;
                    height: 40px;
                    background: ${this.getThemeColor()};
                    border: none;
                    border-radius: 50%;
                    color: white;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                }
                
                .hcw-send:hover {
                    transform: scale(1.05);
                }
                
                .hcw-send:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                    transform: none;
                }
                
                @keyframes slideIn {
                    from {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                @keyframes typing {
                    0%, 60%, 100% { transform: translateY(0); }
                    30% { transform: translateY(-6px); }
                }
                
                @media (max-width: 480px) {
                    .hcw-widget {
                        width: calc(100vw - 20px);
                        height: calc(100vh - 40px);
                        ${this.config.position.includes('right') ? 'right: 10px;' : 'left: 10px;'}
                        ${this.config.position.includes('bottom') ? 'bottom: 10px;' : 'top: 10px;'}
                    }
                    
                    .hcw-toggle {
                        ${this.config.position.includes('right') ? 'right: 10px;' : 'left: 10px;'}
                        ${this.config.position.includes('bottom') ? 'bottom: 10px;' : 'top: 10px;'}
                    }
                }
            `;
            
            const styleSheet = document.createElement('style');
            styleSheet.textContent = styles;
            document.head.appendChild(styleSheet);
        },
        
        getThemeColor: function() {
            const themes = {
                blue: 'linear-gradient(135deg, #667eea, #764ba2)',
                green: 'linear-gradient(135deg, #4ade80, #22c55e)',
                purple: 'linear-gradient(135deg, #a855f7, #7c3aed)',
                red: 'linear-gradient(135deg, #ef4444, #dc2626)'
            };
            return themes[this.config.theme] || themes.blue;
        },
        
        initializeWidget: function() {
            const toggle = document.getElementById('hcwToggle');
            const widget = document.getElementById('hcwWidget');
            const close = document.getElementById('hcwClose');
            const messages = document.getElementById('hcwMessages');
            const input = document.getElementById('hcwInput');
            const send = document.getElementById('hcwSend');
            const language = document.getElementById('hcwLanguage');
            const typing = document.getElementById('hcwTyping');
            
            let isOpen = false;
            let isProcessing = false;
            let currentLanguage = this.config.language;
            
            // Set initial language
            language.value = currentLanguage;
            
            // Event listeners
            toggle.addEventListener('click', () => {
                if (isOpen) {
                    closeWidget();
                } else {
                    openWidget();
                }
            });
            
            close.addEventListener('click', closeWidget);
            
            send.addEventListener('click', sendMessage);
            
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            language.addEventListener('change', (e) => {
                currentLanguage = e.target.value;
            });
            
            function openWidget() {
                widget.classList.add('open');
                toggle.classList.add('hidden');
                isOpen = true;
                input.focus();
            }
            
            function closeWidget() {
                widget.classList.remove('open');
                toggle.classList.remove('hidden');
                isOpen = false;
            }
            
            async function sendMessage() {
                const message = input.value.trim();
                if (!message || isProcessing) return;
                
                // Add user message
                addMessage(message, 'user');
                input.value = '';
                
                // Show typing
                showTyping();
                setProcessing(true);
                
                try {
                    const response = await fetch(`${HealthChatbotWidget.config.apiEndpoint}/chat`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: message,
                            language: currentLanguage
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    
                    const data = await response.json();
                    addMessage(data.response, 'bot');
                    
                } catch (error) {
                    console.error('Health Chatbot Widget Error:', error);
                    addMessage('Sorry, I\'m having trouble connecting. Please try again later.', 'bot');
                } finally {
                    hideTyping();
                    setProcessing(false);
                }
            }
            
            function addMessage(content, sender) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `hcw-message hcw-${sender}`;
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'hcw-message-content';
                contentDiv.textContent = content;
                
                messageDiv.appendChild(contentDiv);
                messages.insertBefore(messageDiv, typing);
                
                scrollToBottom();
            }
            
            function showTyping() {
                typing.classList.add('show');
                scrollToBottom();
            }
            
            function hideTyping() {
                typing.classList.remove('show');
            }
            
            function setProcessing(processing) {
                isProcessing = processing;
                send.disabled = processing;
                input.disabled = processing;
            }
            
            function scrollToBottom() {
                setTimeout(() => {
                    messages.scrollTop = messages.scrollHeight;
                }, 100);
            }
        }
    };
    
    // Make widget available globally
    window.HealthChatbotWidget = HealthChatbotWidget;
    
})();