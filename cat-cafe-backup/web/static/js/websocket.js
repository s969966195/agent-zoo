/**
 * Cat Café - WebSocket Client
 * Handles real-time communication with the backend
 */

class CatCafeWebSocket {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageHandlers = new Map();
        this.isConnecting = false;
        this.messageQueue = [];
        
        // Default handlers
        this.onConnect = null;
        this.onDisconnect = null;
        this.onError = null;
        this.onMessage = null;
    }
    
    /**
     * Get WebSocket URL based on current location
     * @returns {string} WebSocket URL
     */
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        // Try common WebSocket endpoints
        return `${protocol}//${host}/api/ws`;
    }
    
    /**
     * Get REST API base URL
     * @returns {string} API base URL
     */
    getApiBaseUrl() {
        return window.location.origin;
    }
    
    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            return;
        }
        
        this.isConnecting = true;
        
        if (typeof setConnectionStatus === 'function') {
            setConnectionStatus('connecting');
        }
        
        try {
            const url = this.getWebSocketUrl();
            console.log('Connecting to WebSocket:', url);
            
            this.ws = new WebSocket(url);
            
            this.ws.onopen = this.handleOpen.bind(this);
            this.ws.onmessage = this.handleMessage.bind(this);
            this.ws.onclose = this.handleClose.bind(this);
            this.ws.onerror = this.handleError.bind(this);
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.handleError(error);
        }
    }
    
    /**
     * Handle WebSocket open event
     */
    handleOpen() {
        console.log('WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        
        if (typeof setConnectionStatus === 'function') {
            setConnectionStatus('online');
        }
        
        if (typeof Toast !== 'undefined') {
            Toast.success('已连接到猫咪们 🐱');
        }
        
        // Send any queued messages
        while (this.messageQueue.length > 0) {
            const msg = this.messageQueue.shift();
            this.send(msg);
        }
        
        if (this.onConnect) {
            this.onConnect();
        }
    }
    
    /**
     * Handle incoming WebSocket message
     * @param {MessageEvent} event - WebSocket message event
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            
            // Handle different message types
            this.handleTypedMessage(data);
            
            // Call generic message handler
            if (this.onMessage) {
                this.onMessage(data);
            }
            
            // Call specific type handler
            const handler = this.messageHandlers.get(data.type);
            if (handler) {
                handler(data);
            }
            
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }
    
    /**
     * Handle typed messages from server
     * @param {Object} data - Message data
     */
    handleTypedMessage(data) {
        switch (data.type) {
            case 'connected':
                console.log('Server acknowledged connection:', data.message);
                break;
                
            case 'text':
                // Agent text message
                if (typeof createMessageBubble === 'function') {
                    const messagesContainer = document.getElementById('messages');
                    if (messagesContainer) {
                        const messageEl = createMessageBubble({
                            content: data.content,
                            agentId: data.agent_id,
                            sender: 'agent',
                            timestamp: data.timestamp || new Date().toISOString()
                        });
                        messagesContainer.appendChild(messageEl);
                        scrollToBottom();
                    }
                }
                break;
                
            case 'typing':
                // Agent started typing
                if (typeof showTypingIndicator === 'function') {
                    showTypingIndicator(data.agent_id, true);
                }
                if (typeof updateAgentStatus === 'function') {
                    updateAgentStatus(data.agent_id, 'typing');
                }
                break;
                
            case 'thinking':
                // Agent is thinking
                if (typeof updateAgentStatus === 'function') {
                    updateAgentStatus(data.agent_id, 'thinking');
                }
                break;
                
            case 'done':
                // Agent finished
                if (typeof hideTypingIndicator === 'function') {
                    hideTypingIndicator();
                }
                if (typeof updateAgentStatus === 'function') {
                    updateAgentStatus(data.agent_id, 'idle');
                }
                break;
                
            case 'error':
                // Error occurred
                console.error('Server error:', data.error);
                if (typeof Toast !== 'undefined') {
                    Toast.error(data.error || '出错了，猫咪们遇到了困难');
                }
                if (typeof updateAgentStatus === 'function' && data.agent_id) {
                    updateAgentStatus(data.agent_id, 'error', data.error);
                }
                break;
                
            case 'thread_update':
                // Thread was updated
                if (typeof updateThreadList === 'function') {
                    // Fetch updated thread list
                    this.fetchThreads();
                }
                break;
                
            case 'agent_status':
                // Agent status update
                if (typeof updateAgentStatus === 'function') {
                    updateAgentStatus(data.agent_id, data.status, data.message);
                }
                break;
                
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    /**
     * Handle WebSocket close event
     * @param {CloseEvent} event - Close event
     */
    handleClose(event) {
        console.log('WebSocket closed:', event.code, event.reason);
        this.isConnecting = false;
        
        if (typeof setConnectionStatus === 'function') {
            setConnectionStatus('offline');
        }
        
        if (this.onDisconnect) {
            this.onDisconnect(event);
        }
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            if (typeof Toast !== 'undefined') {
                Toast.error('连接断开，请刷新页面重试');
            }
        }
    }
    
    /**
     * Handle WebSocket error
     * @param {Event} error - Error event
     */
    handleError(error) {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        
        if (typeof setConnectionStatus === 'function') {
            setConnectionStatus('offline');
        }
        
        if (this.onError) {
            this.onError(error);
        }
    }
    
    /**
     * Send message through WebSocket
     * @param {Object} data - Data to send
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            // Queue message for when connection is established
            this.messageQueue.push(data);
            console.log('Message queued - WebSocket not connected');
        }
    }
    
    /**
     * Register message type handler
     * @param {string} type - Message type
     * @param {Function} handler - Handler function
     */
    on(type, handler) {
        this.messageHandlers.set(type, handler);
    }
    
    /**
     * Unregister message type handler
     * @param {string} type - Message type
     */
    off(type) {
        this.messageHandlers.delete(type);
    }
    
    /**
     * Disconnect WebSocket
     */
    disconnect() {
        this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
    
    /**
     * Check if connected
     * @returns {boolean}
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
    
    /**
     * Subscribe to a thread
     * @param {string} threadId - Thread ID to subscribe to
     */
    subscribeThread(threadId) {
        this.send({
            type: 'subscribe',
            thread_id: threadId
        });
    }
    
    /**
     * Unsubscribe from a thread
     * @param {string} threadId - Thread ID to unsubscribe from
     */
    unsubscribeThread(threadId) {
        this.send({
            type: 'unsubscribe',
            thread_id: threadId
        });
    }
    
    // ============================================
    // REST API Methods
    // ============================================
    
    /**
     * Send a message via REST API
     * @param {string} content - Message content
     * @param {string[]} agentIds - Agent IDs to mention
     * @param {string} threadId - Thread ID (optional)
     * @returns {Promise<Object>} Response data
     */
    async sendMessage(content, agentIds = [], threadId = null) {
        const url = `${this.getApiBaseUrl()}/api/messages`;
        
        const body = {
            content,
            agent_ids: agentIds,
            thread_id: threadId
        };
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            });
            
            if (!response.ok) {
                const error = await response.text();
                throw new Error(error || `HTTP ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    }
    
    /**
     * Fetch threads list
     * @returns {Promise<Array>} Array of threads
     */
    async fetchThreads() {
        const url = `${this.getApiBaseUrl()}/api/threads`;
        
        try {
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Error fetching threads:', error);
            return [];
        }
    }
    
    /**
     * Fetch messages for a thread
     * @param {string} threadId - Thread ID
     * @returns {Promise<Array>} Array of messages
     */
    async fetchMessages(threadId) {
        if (!threadId) return [];
        
        const url = `${this.getApiBaseUrl()}/api/threads/${threadId}/messages`;
        
        try {
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Error fetching messages:', error);
            return [];
        }
    }
    
    /**
     * Create a new thread
     * @param {string} title - Thread title
     * @returns {Promise<Object>} Created thread
     */
    async createThread(title = '新对话') {
        const url = `${this.getApiBaseUrl()}/api/threads`;
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Error creating thread:', error);
            throw error;
        }
    }
    
    /**
     * Stop thread execution
     * @param {string} threadId - Thread ID
     * @returns {Promise<boolean>} Success
     */
    async stopThread(threadId) {
        const url = `${this.getApiBaseUrl()}/api/threads/${threadId}/cancel`;
        
        try {
            const response = await fetch(url, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return true;
            
        } catch (error) {
            console.error('Error stopping thread:', error);
            return false;
        }
    }
    
    /**
     * Delete a thread
     * @param {string} threadId - Thread ID
     * @returns {Promise<boolean>} Success
     */
    async deleteThread(threadId) {
        const url = `${this.getApiBaseUrl()}/api/threads/${threadId}`;
        
        try {
            const response = await fetch(url, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return true;
            
        } catch (error) {
            console.error('Error deleting thread:', error);
            return false;
        }
    }
    
    /**
     * Update thread title
     * @param {string} threadId - Thread ID
     * @param {string} title - New title
     * @returns {Promise<Object>} Updated thread
     */
    async updateThreadTitle(threadId, title) {
        const url = `${this.getApiBaseUrl()}/api/threads/${threadId}`;
        
        try {
            const response = await fetch(url, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Error updating thread:', error);
            throw error;
        }
    }
    
    /**
     * Fetch agent status
     * @returns {Promise<Object>} Agent status map
     */
    async fetchAgentStatus() {
        const url = `${this.getApiBaseUrl()}/api/agents/status`;
        
        try {
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Error fetching agent status:', error);
            return {};
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CatCafeWebSocket;
}
