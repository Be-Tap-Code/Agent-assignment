// Global variables
let isDarkTheme = false;
let isRecording = false;
let recognition = null;

// DOM elements
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const themeToggle = document.getElementById('themeToggle');
const refreshBtn = document.getElementById('refreshBtn');
const voiceBtn = document.getElementById('voiceBtn');
const attachmentBtn = document.getElementById('attachmentBtn');
const fileInput = document.getElementById('fileInput');
const loadingIndicator = document.getElementById('loadingIndicator');

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    initializeSpeechRecognition();
});

function initializeApp() {
    // Load saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        toggleTheme();
    }
    
    // Focus on input
    messageInput.focus();
}

function setupEventListeners() {
    // Send message events
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Theme toggle
    themeToggle.addEventListener('click', toggleTheme);
    
    // Refresh button
    refreshBtn.addEventListener('click', refreshChat);
    
    // Voice input
    voiceBtn.addEventListener('click', toggleVoiceRecording);
    
    // File attachment
    attachmentBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);
    
    // Input validation
    messageInput.addEventListener('input', function() {
        const text = this.value.trim();
        const hasText = text.length > 0;
        const isValidLength = text.length <= 2000;
        
        sendBtn.disabled = !hasText || !isValidLength;
        
        // Show character count warning
        updateCharacterCount(text.length);
    });
}

function initializeSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            messageInput.value = transcript;
            messageInput.dispatchEvent(new Event('input'));
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            stopVoiceRecording();
        };
        
        recognition.onend = function() {
            stopVoiceRecording();
        };
    } else {
        voiceBtn.style.display = 'none';
    }
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Sanitize input
    const sanitizedMessage = sanitizeInput(message);
    if (!sanitizedMessage) {
        addMessage('Invalid input detected. Please check your message and try again.', 'assistant');
        return;
    }
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    messageInput.value = '';
    sendBtn.disabled = true;
    
    // Show loading
    showLoading();
    
    try {
        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        // Call the API with timeout
        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: sanitizedMessage,
                context: null
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            let errorMessage = `Server error (${response.status})`;
            
            // Handle specific HTTP status codes
            switch (response.status) {
                case 400:
                    errorMessage = 'Invalid request. Please check your input.';
                    break;
                case 422:
                    errorMessage = 'Invalid input format. Please try again.';
                    break;
                case 429:
                    errorMessage = 'Too many requests. Please wait a moment and try again.';
                    break;
                case 500:
                    errorMessage = 'Server error. Please try again later.';
                    break;
                case 503:
                    errorMessage = 'Service temporarily unavailable. Please try again later.';
                    break;
            }
            
            throw new Error(errorMessage);
        }
        
        // Parse JSON response
        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            throw new Error('Invalid response format from server.');
        }
        
        // Validate response structure
        if (!data || typeof data.answer !== 'string') {
            throw new Error('Invalid response structure from server.');
        }
        
        // Add assistant response to chat
        addMessage(data.answer, 'assistant');
        
        // Show citations if available
        if (data.citations && Array.isArray(data.citations) && data.citations.length > 0) {
            addCitations(data.citations);
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        
        let errorMessage = 'Sorry, I encountered an error while processing your question. Please try again.';
        
        // Handle specific error types
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out. The server is taking too long to respond. Please try again.';
        } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
            errorMessage = 'Network error. Please check your internet connection and try again.';
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        addMessage(errorMessage, 'assistant');
    } finally {
        hideLoading();
        messageInput.focus();
    }
}

function addMessage(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    
    // Remove welcome message if it exists
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addCitations(citations) {
    const citationsDiv = document.createElement('div');
    citationsDiv.className = 'citations';
    citationsDiv.style.cssText = `
        max-width: 80%;
        margin: 10px auto 20px auto;
        padding: 12px 16px;
        background-color: #f8fafc;
        border-radius: 8px;
        border-left: 4px solid #8b5cf6;
        font-size: 14px;
        color: #64748b;
    `;
    
    const title = document.createElement('div');
    title.textContent = 'Sources:';
    title.style.cssText = 'font-weight: 600; margin-bottom: 8px; color: #374151;';
    
    citationsDiv.appendChild(title);
    
    citations.forEach((citation, index) => {
        const citationItem = document.createElement('div');
        citationItem.textContent = `${index + 1}. ${citation.source}`;
        citationItem.style.cssText = 'margin-bottom: 4px;';
        citationsDiv.appendChild(citationItem);
    });
    
    chatMessages.appendChild(citationsDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showLoading() {
    loadingIndicator.style.display = 'block';
}

function hideLoading() {
    loadingIndicator.style.display = 'none';
}

function toggleTheme() {
    isDarkTheme = !isDarkTheme;
    document.body.classList.toggle('dark-theme', isDarkTheme);
    
    // Update theme toggle icon
    const icon = themeToggle.querySelector('i');
    icon.className = isDarkTheme ? 'fas fa-sun' : 'fas fa-moon';
    
    // Save preference
    localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
}

function refreshChat() {
    // Clear chat messages
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <h2>What can I help with?</h2>
        </div>
    `;
    
    // Clear input
    messageInput.value = '';
    sendBtn.disabled = true;
    
    // Focus on input
    messageInput.focus();
}

function toggleVoiceRecording() {
    if (!recognition) return;
    
    if (isRecording) {
        stopVoiceRecording();
    } else {
        startVoiceRecording();
    }
}

function startVoiceRecording() {
    if (!recognition) return;
    
    try {
        recognition.start();
        isRecording = true;
        voiceBtn.style.backgroundColor = '#ef4444';
        voiceBtn.style.color = 'white';
        voiceBtn.title = 'Stop recording';
    } catch (error) {
        console.error('Error starting voice recognition:', error);
    }
}

function stopVoiceRecording() {
    if (!recognition) return;
    
    try {
        recognition.stop();
        isRecording = false;
        voiceBtn.style.backgroundColor = '';
        voiceBtn.style.color = '';
        voiceBtn.title = 'Voice input';
    } catch (error) {
        console.error('Error stopping voice recognition:', error);
    }
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type and size
    const allowedTypes = ['text/plain', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    if (!allowedTypes.includes(file.type)) {
        addMessage('Invalid file type. Please upload a text, PDF, or Word document.', 'assistant');
        event.target.value = '';
        return;
    }
    
    if (file.size > maxSize) {
        addMessage('File too large. Please upload a file smaller than 10MB.', 'assistant');
        event.target.value = '';
        return;
    }
    
    // For now, just show a message about file upload
    // In a real implementation, you would process the file
    addMessage(`File "${file.name}" selected. File processing feature coming soon!`, 'assistant');
    
    // Clear the input
    event.target.value = '';
}

function sanitizeInput(input) {
    if (!input || typeof input !== 'string') {
        return null;
    }
    
    // Remove potentially dangerous characters and patterns
    let sanitized = input
        .replace(/[<>]/g, '') // Remove HTML tags
        .replace(/javascript:/gi, '') // Remove javascript: protocol
        .replace(/data:/gi, '') // Remove data: protocol
        .replace(/vbscript:/gi, '') // Remove vbscript: protocol
        .replace(/on\w+\s*=/gi, '') // Remove event handlers
        .trim();
    
    // Check for suspicious patterns
    const suspiciousPatterns = [
        /<script/i,
        /<iframe/i,
        /<object/i,
        /<embed/i,
        /<link/i,
        /<meta/i,
        /eval\s*\(/i,
        /expression\s*\(/i,
        /url\s*\(/i
    ];
    
    for (const pattern of suspiciousPatterns) {
        if (pattern.test(sanitized)) {
            console.warn('Suspicious input detected:', pattern);
            return null;
        }
    }
    
    // Check for excessive special characters (potential injection)
    const specialCharCount = (sanitized.match(/[^\w\s.,!?;:()-]/g) || []).length;
    if (specialCharCount > sanitized.length * 0.3) {
        console.warn('Excessive special characters detected');
        return null;
    }
    
    // Limit length
    if (sanitized.length > 2000) {
        return null;
    }
    
    return sanitized;
}

function updateCharacterCount(length) {
    // Remove existing character count if any
    const existingCount = document.querySelector('.character-count');
    if (existingCount) {
        existingCount.remove();
    }
    
    // Only show count if approaching limit
    if (length > 1500) {
        const countDiv = document.createElement('div');
        countDiv.className = 'character-count';
        countDiv.style.cssText = `
            position: absolute;
            bottom: 60px;
            right: 24px;
            font-size: 12px;
            color: ${length > 2000 ? '#ef4444' : '#f59e0b'};
            background-color: white;
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid #e5e5e5;
            z-index: 1000;
        `;
        countDiv.textContent = `${length}/2000`;
        
        document.body.appendChild(countDiv);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (countDiv.parentNode) {
                countDiv.remove();
            }
        }, 3000);
    }
}

// Handle window resize
window.addEventListener('resize', function() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
});

// Handle page visibility change
document.addEventListener('visibilitychange', function() {
    if (document.hidden && isRecording) {
        stopVoiceRecording();
    }
});
