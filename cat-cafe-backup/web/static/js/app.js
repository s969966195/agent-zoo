/**
 * Cat Café - Main Application
 * Coordinates WebSocket connection, UI interactions, and message handling
 */

class CatCafeApp {
    constructor() {
        this.ws = new CatCafeWebSocket();
        this.currentThread = null;
        this.threads = [];
        this.isProcessing = false;
        this.activeAgents = new Set();
        
        // DOM elements
        this.elements = {
            messages: null,
            input: null,
            sendBtn: null,
            stopBtn: null,
            newThreadBtn: null,
            threads: null,
            themeToggle: null,
            currentThreadTitle: null
        };
    }
    
    /**
     * Initialize the application
     */
    async init() {
        console.log('🐱 Cat Café initializing...');
        
        // Initialize DOM references
        this.initializeElements();
        
        // Initialize Toast
        if (typeof Toast !== 'undefined') {
            Toast.init();
        }
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initialize WebSocket
        this.initializeWebSocket();
        
        // Load initial data
        await this.loadThreads();
        
        // Load saved theme
        this.loadTheme();
        
        // Focus input
        if (this.elements.input) {
            this.elements.input.focus();
        }
        
        console.log('✨ Cat Café ready!');
    }
    
    /**
     * Initialize DOM element references
     */
    initializeElements() {
        this.elements.messages = document.getElementById('messages');
        this.elements.input = document.getElementById('message-input');
        this.elements.sendBtn = document.getElementById('send-btn');
        this.elements.stopBtn = document.getElementById('stop-btn');
        this.elements.newThreadBtn = document.getElementById('new-thread');
        this.elements.threads = document.getElementById('threads');
        this.elements.themeToggle = document.getElementById('theme-toggle');
        this.elements.currentThreadTitle = document.getElementById('current-thread-title');
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Send button
        if (this.elements.sendBtn) {
            this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        // Stop button
        if (this.elements.stopBtn) {
            this.elements.stopBtn.addEventListener('click', () => this.stopExecution());
        }
        
        // Input enter key
        if (this.elements.input) {
            this.elements.input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            // Auto-resize textarea
            this.elements.input.addEventListener('input', () => {
                if (typeof autoResizeTextarea === 'function') {
                    autoResizeTextarea(this.elements.input);
                }
            });
            
            // Setup mention autocomplete
            if (typeof setupMentionAutocomplete === 'function') {
                setupMentionAutocomplete(this.elements.input, (agentId) => {
                    console.log('Selected agent:', agentId);
                });
            }
        }
        
        // New thread button
        if (this.elements.newThreadBtn) {
            this.elements.newThreadBtn.addEventListener('click', () => this.createNewThread());
        }
        
        // Thread list click delegation
        if (this.elements.threads) {
            this.elements.threads.addEventListener('click', (e) => {
                const threadItem = e.target.closest('.thread-item');
                if (threadItem) {
                    const threadId = threadItem.getAttribute('data-thread-id');
                    if (threadId) {
                        this.switchThread(threadId);
                    }
                }
            });
        }
        
        // Theme toggle
        if (this.elements.themeToggle) {
            this.elements.themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        // Window beforeunload - cleanup
        window.addEventListener('beforeunload', () => {
            this.ws.disconnect();
        });
        
        // Handle visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                // Reconnect if needed
                if (!this.ws.isConnected()) {
                    this.ws.connect();
                }
            }
        });
    }
    
    /**
     * Initialize WebSocket connection
     */
    initializeWebSocket() {
        // Set up WebSocket event handlers
        this.ws.onConnect = () => {
            console.log('WebSocket connected');
            if (this.currentThread) {
                this.ws.subscribeThread(this.currentThread.id);
            }
        };
        
        this.ws.onDisconnect = () => {
            console.log('WebSocket disconnected');
            this.hideStopButton();
        };
        
        this.ws.onError = (error) => {
            console.error('WebSocket error:', error);
            if (typeof Toast !== 'undefined') {
                Toast.error('连接出错，正在尝试重新连接...');
            }
        };
        
        // Connect
        this.ws.connect();
    }
    
    /**
     * Load threads from server
     */
    async loadThreads() {
        try {
            this.threads = await this.ws.fetchThreads();
            
            // Update UI
            if (typeof updateThreadList === 'function') {
                updateThreadList(this.threads, this.currentThread?.id);
            }
            
            // If no threads, create one
            if (this.threads.length === 0) {
                await this.createNewThread('新对话');
            } else if (!this.currentThread) {
                // Load the most recent thread
                await this.switchThread(this.threads[0].id);
            }
            
        } catch (error) {
            console.error('Error loading threads:', error);
            if (typeof Toast !== 'undefined') {
                Toast.error('加载对话列表失败');
            }
        }
    }
    
    /**
     * Create a new thread
     * @param {string} title - Thread title
     */
    async createNewThread(title = '新对话') {
        try {
            const thread = await this.ws.createThread(title);
            this.threads.unshift(thread);
            await this.switchThread(thread.id);
            
            if (typeof Toast !== 'undefined') {
                Toast.success('新对话已创建');
            }
            
        } catch (error) {
            console.error('Error creating thread:', error);
            if (typeof Toast !== 'undefined') {
                Toast.error('创建对话失败');
            }
        }
    }
    
    /**
     * Switch to a different thread
     * @param {string} threadId - Thread ID to switch to
     */
    async switchThread(threadId) {
        // Unsubscribe from current thread
        if (this.currentThread) {
            this.ws.unsubscribeThread(this.currentThread.id);
        }
        
        // Find thread
        const thread = this.threads.find(t => t.id === threadId);
        if (!thread) return;
        
        this.currentThread = thread;
        
        // Update UI
        if (this.elements.currentThreadTitle) {
            this.elements.currentThreadTitle.textContent = thread.title || '新对话';
        }
        
        if (typeof updateThreadList === 'function') {
            updateThreadList(this.threads, threadId);
        }
        
        // Clear messages
        if (this.elements.messages) {
            // Keep welcome message if no thread loaded
            const welcomeMessage = this.elements.messages.querySelector('.welcome-message');
            this.elements.messages.innerHTML = '';
            if (!threadId) {
                this.elements.messages.appendChild(welcomeMessage);
            }
        }
        
        // Load messages
        if (threadId) {
            try {
                const messages = await this.ws.fetchMessages(threadId);
                this.renderMessages(messages);
                
                // Subscribe to thread
                this.ws.subscribeThread(threadId);
                
            } catch (error) {
                console.error('Error loading messages:', error);
                if (typeof Toast !== 'undefined') {
                    Toast.error('加载消息失败');
                }
            }
        }
    }
    
    /**
     * Render messages to the UI
     * @param {Array} messages - Array of message objects
     */
    renderMessages(messages) {
        if (!this.elements.messages || !messages) return;
        
        this.elements.messages.innerHTML = '';
        
        messages.forEach(msg => {
            if (typeof createMessageBubble === 'function') {
                const messageEl = createMessageBubble(msg);
                this.elements.messages.appendChild(messageEl);
            }
        });
        
        if (typeof scrollToBottom === 'function') {
            scrollToBottom();
        }
    }
    
    /**
     * Send a message
     */
    async sendMessage() {
        if (!this.elements.input || this.isProcessing) return;
        
        const content = this.elements.input.value.trim();
        if (!content) return;
        
        // Extract mentions
        let agentIds = [];
        if (typeof extractMentions === 'function') {
            agentIds = extractMentions(content);
        }
        
        // Add user message to UI immediately
        if (typeof createMessageBubble === 'function') {
            const userMessage = {
                content,
                sender: 'user',
                timestamp: new Date().toISOString()
            };
            const messageEl = createMessageBubble(userMessage);
            this.elements.messages.appendChild(messageEl);
            
            // Remove welcome message if present
            const welcomeMessage = this.elements.messages.querySelector('.welcome-message');
            if (welcomeMessage) {
                welcomeMessage.remove();
            }
            
            if (typeof scrollToBottom === 'function') {
                scrollToBottom();
            }
        }
        
        // Clear input
        this.elements.input.value = '';
        this.elements.input.style.height = 'auto';
        
        // Show stop button
        this.showStopButton();
        this.isProcessing = true;
        
        try {
            // Send to server
            const response = await this.ws.sendMessage(
                content,
                agentIds,
                this.currentThread?.id
            );
            
            // If new thread was created
            if (response.thread_id && response.thread_id !== this.currentThread?.id) {
                await this.switchThread(response.thread_id);
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            if (typeof Toast !== 'undefined') {
                Toast.error('发送消息失败');
            }
            this.hideStopButton();
        }
    }
    
    /**
     * Stop current execution
     */
    async stopExecution() {
        if (!this.currentThread || !this.isProcessing) return;
        
        try {
            const success = await this.ws.stopThread(this.currentThread.id);
            
            if (success) {
                if (typeof Toast !== 'undefined') {
                    Toast.info('已停止');
                }
                this.hideStopButton();
                this.isProcessing = false;
            } else {
                if (typeof Toast !== 'undefined') {
                    Toast.error('停止失败');
                }
            }
            
        } catch (error) {
            console.error('Error stopping execution:', error);
            if (typeof Toast !== 'undefined') {
                Toast.error('停止失败');
            }
        }
    }
    
    /**
     * Show stop button
     */
    showStopButton() {
        if (this.elements.sendBtn) {
            this.elements.sendBtn.classList.add('hidden');
        }
        if (this.elements.stopBtn) {
            this.elements.stopBtn.classList.remove('hidden');
        }
    }
    
    /**
     * Hide stop button
     */
    hideStopButton() {
        if (this.elements.sendBtn) {
            this.elements.sendBtn.classList.remove('hidden');
        }
        if (this.elements.stopBtn) {
            this.elements.stopBtn.classList.add('hidden');
        }
        this.isProcessing = false;
        
        // Reset all agent statuses to idle
        Object.keys(AGENTS || {}).forEach(agentId => {
            if (typeof updateAgentStatus === 'function') {
                updateAgentStatus(agentId, 'idle');
            }
        });
    }
    
    /**
     * Toggle dark/light theme
     */
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('cat-cafe-theme', newTheme);
        
        // Update toggle button icon
        if (this.elements.themeToggle) {
            const icon = this.elements.themeToggle.querySelector('.theme-icon');
            if (icon) {
                icon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
            }
        }
    }
    
    /**
     * Load saved theme preference
     */
    loadTheme() {
        const savedTheme = localStorage.getItem('cat-cafe-theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = savedTheme || (prefersDark ? 'dark' : 'light');
        
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update toggle button icon
        if (this.elements.themeToggle) {
            const icon = this.elements.themeToggle.querySelector('.theme-icon');
            if (icon) {
                icon.textContent = theme === 'dark' ? '☀️' : '🌙';
            }
        }
    }
    
    /**
     * Handle agent activity
     * @param {string} agentId - Agent ID
     * @param {string} activity - Activity type
     */
    handleAgentActivity(agentId, activity) {
        if (activity === 'start') {
            this.activeAgents.add(agentId);
            this.showStopButton();
        } else if (activity === 'end') {
            this.activeAgents.delete(agentId);
            if (this.activeAgents.size === 0) {
                this.hideStopButton();
            }
        }
    }
    
    /**
     * Update thread title
     * @param {string} title - New title
     */
    async updateThreadTitle(title) {
        if (!this.currentThread) return;
        
        try {
            await this.ws.updateThreadTitle(this.currentThread.id, title);
            this.currentThread.title = title;
            
            if (this.elements.currentThreadTitle) {
                this.elements.currentThreadTitle.textContent = title;
            }
            
            await this.loadThreads();
            
        } catch (error) {
            console.error('Error updating thread title:', error);
            if (typeof Toast !== 'undefined') {
                Toast.error('更新标题失败');
            }
        }
    }
}

// ============================================
// Application Initialization
// ============================================

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Create global app instance
    window.catCafeApp = new CatCafeApp();
    window.catCafeApp.init();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CatCafeApp;
}
