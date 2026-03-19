/**
 * Cat Café - UI Components
 * Handles rendering messages, agent status, typing indicators, and @mention autocomplete
 */

// Agent configuration
const AGENTS = {
    ragdoll: {
        id: 'ragdoll',
        name: '布偶猫',
        aliases: ['布偶猫', '布偶', 'ragdoll'],
        avatar: '🐱',
        className: 'ragdoll',
        description: '优雅的绅士'
    },
    maine: {
        id: 'maine',
        name: '缅因猫',
        aliases: ['缅因猫', '缅因', 'maine'],
        avatar: '😺',
        className: 'maine',
        description: '强壮的探险家'
    },
    siamese: {
        id: 'siamese',
        name: '暹罗猫',
        aliases: ['暹罗猫', '暹罗', 'siamese'],
        avatar: '🐈',
        className: 'siamese',
        description: '机智的智者'
    }
};

// Toast notification system
const Toast = {
    container: null,
    
    init() {
        this.container = document.getElementById('toast-container');
    },
    
    show(message, type = 'info', duration = 3000) {
        if (!this.container) {
            this.init();
        }
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${message}</span>
        `;
        
        this.container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },
    
    success(message) {
        this.show(message, 'success');
    },
    
    error(message) {
        this.show(message, 'error');
    },
    
    info(message) {
        this.show(message, 'info');
    }
};

/**
 * Create a message bubble element
 * @param {Object} message - Message object with content, sender, timestamp
 * @returns {HTMLElement} Message element
 */
function createMessageBubble(message) {
    const messageEl = document.createElement('div');
    messageEl.className = 'message';
    
    // Determine message type
    const isUser = message.sender === 'user';
    const agent = !isUser ? AGENTS[message.agentId] || AGENTS.ragdoll : null;
    
    messageEl.classList.add(isUser ? 'user' : `agent-${agent?.id || 'ragdoll'}`);
    
    // Avatar
    const avatarEl = document.createElement('div');
    avatarEl.className = `message-avatar ${isUser ? 'user' : agent?.className || 'ragdoll'}`;
    avatarEl.textContent = isUser ? '👤' : agent?.avatar || '🐱';
    
    // Content container
    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    
    // Header
    const headerEl = document.createElement('div');
    headerEl.className = 'message-header';
    
    const authorEl = document.createElement('span');
    authorEl.className = 'message-author';
    authorEl.textContent = isUser ? '你' : agent?.name || 'AI猫咪';
    
    const timeEl = document.createElement('span');
    timeEl.className = 'message-time';
    timeEl.textContent = formatTimestamp(message.timestamp);
    
    headerEl.appendChild(authorEl);
    headerEl.appendChild(timeEl);
    
    // Message bubble
    const bubbleEl = document.createElement('div');
    bubbleEl.className = 'message-bubble';
    
    // Parse and render content with mentions
    const textEl = document.createElement('div');
    textEl.className = 'message-text';
    textEl.innerHTML = parseMentions(message.content);
    
    bubbleEl.appendChild(textEl);
    
    // Assemble
    contentEl.appendChild(headerEl);
    contentEl.appendChild(bubbleEl);
    
    messageEl.appendChild(avatarEl);
    messageEl.appendChild(contentEl);
    
    return messageEl;
}

/**
 * Parse @mentions in message content
 * @param {string} content - Raw message content
 * @returns {string} HTML with highlighted mentions
 */
function parseMentions(content) {
    if (!content) return '';
    
    // Escape HTML first
    let safeContent = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Replace mentions with styled spans
    Object.values(AGENTS).forEach(agent => {
        agent.aliases.forEach(alias => {
            const mention = `@${alias}`;
            const regex = new RegExp(mention.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
            safeContent = safeContent.replace(regex, 
                `<span class="mention ${agent.className}">${mention}</span>`);
        });
    });
    
    // Convert newlines to <br>
    safeContent = safeContent.replace(/\n/g, '<br>');
    
    return safeContent;
}

/**
 * Extract mentions from message content
 * @param {string} content - Message content
 * @returns {string[]} Array of agent IDs mentioned
 */
function extractMentions(content) {
    const mentions = [];
    const mentioned = new Set();
    
    Object.values(AGENTS).forEach(agent => {
        agent.aliases.forEach(alias => {
            if (content.includes(`@${alias}`) && !mentioned.has(agent.id)) {
                mentions.push(agent.id);
                mentioned.add(agent.id);
            }
        });
    });
    
    return mentions;
}

/**
 * Format timestamp for display
 * @param {string|number|Date} timestamp - Timestamp to format
 * @returns {string} Formatted time string
 */
function formatTimestamp(timestamp) {
    const date = timestamp ? new Date(timestamp) : new Date();
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) {
        return '刚刚';
    }
    
    // Less than 1 hour
    if (diff < 3600000) {
        return `${Math.floor(diff / 60000)}分钟前`;
    }
    
    // Less than 24 hours
    if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)}小时前`;
    }
    
    // Format as date
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

/**
 * Update agent status display
 * @param {string} agentId - Agent ID
 * @param {string} status - Status: 'idle', 'thinking', 'typing', 'error'
 * @param {string} message - Optional status message
 */
function updateAgentStatus(agentId, status, message = '') {
    const card = document.querySelector(`.agent-card[data-agent="${agentId}"]`);
    if (!card) return;
    
    card.setAttribute('data-status', status);
    
    const badge = card.querySelector('.agent-status-badge');
    if (badge) {
        badge.className = `agent-status-badge ${status}`;
        
        const statusText = {
            idle: '空闲',
            thinking: '思考中',
            typing: '输入中',
            error: '出错了'
        };
        
        badge.textContent = message || statusText[status] || status;
    }
    
    // Animate avatar on activity
    const avatar = card.querySelector('.agent-avatar');
    if (avatar && (status === 'thinking' || status === 'typing')) {
        avatar.style.animation = 'gentle-bounce 1s ease-in-out infinite';
    } else {
        avatar.style.animation = '';
    }
}

/**
 * Show typing indicator
 * @param {string} agentId - Agent ID that is typing
 * @param {boolean} isTyping - Whether agent is typing
 */
function showTypingIndicator(agentId, isTyping = true) {
    const indicator = document.getElementById('typing-indicator');
    const agent = AGENTS[agentId];
    
    if (!indicator || !agent) return;
    
    if (isTyping) {
        indicator.classList.remove('hidden');
        const agentEl = indicator.querySelector('.typing-agent');
        const textEl = indicator.querySelector('.typing-text');
        
        if (agentEl) agentEl.textContent = agent.avatar;
        if (textEl) textEl.textContent = `${agent.name}正在输入`;
        
        // Scroll to bottom
        scrollToBottom();
    } else {
        indicator.classList.add('hidden');
    }
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.classList.add('hidden');
    }
}

/**
 * Scroll messages to bottom
 */
function scrollToBottom() {
    const messagesContainer = document.getElementById('messages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

/**
 * Setup @mention autocomplete
 * @param {HTMLTextAreaElement} input - Text input element
 * @param {Function} onSelect - Callback when mention is selected
 */
function setupMentionAutocomplete(input, onSelect) {
    const dropdown = document.getElementById('mention-dropdown');
    if (!dropdown) return;
    
    let selectedIndex = -1;
    let mentionStart = -1;
    
    const items = dropdown.querySelectorAll('.mention-item');
    
    function updateSelection() {
        items.forEach((item, index) => {
            item.classList.toggle('selected', index === selectedIndex);
        });
    }
    
    function showDropdown() {
        dropdown.classList.remove('hidden');
        selectedIndex = 0;
        updateSelection();
    }
    
    function hideDropdown() {
        dropdown.classList.add('hidden');
        selectedIndex = -1;
        mentionStart = -1;
    }
    
    function insertMention(agentId) {
        const agent = AGENTS[agentId];
        if (!agent) return;
        
        const value = input.value;
        const before = value.substring(0, mentionStart);
        const after = value.substring(input.selectionStart);
        const mention = `@${agent.name} `;
        
        input.value = before + mention + after;
        input.selectionStart = input.selectionEnd = mentionStart + mention.length;
        input.focus();
        
        hideDropdown();
        
        if (onSelect) {
            onSelect(agentId);
        }
        
        // Trigger input event for auto-resize
        input.dispatchEvent(new Event('input'));
    }
    
    input.addEventListener('input', (e) => {
        const cursorPos = input.selectionStart;
        const value = input.value;
        
        // Find @ before cursor
        const textBeforeCursor = value.substring(0, cursorPos);
        const lastAtIndex = textBeforeCursor.lastIndexOf('@');
        
        if (lastAtIndex !== -1) {
            const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1);
            
            // Check if there's a space or newline after @
            if (!textAfterAt.includes(' ') && !textAfterAt.includes('\n')) {
                mentionStart = lastAtIndex;
                showDropdown();
                
                // Filter items based on typed text
                const filter = textAfterAt.toLowerCase();
                let hasVisible = false;
                
                items.forEach((item, index) => {
                    const name = item.querySelector('.mention-name').textContent.toLowerCase();
                    const alias = item.querySelector('.mention-alias').textContent.toLowerCase();
                    const matches = name.includes(filter) || alias.includes(filter);
                    
                    item.style.display = matches ? 'flex' : 'none';
                    if (matches) hasVisible = true;
                });
                
                if (!hasVisible) {
                    hideDropdown();
                }
                
                return;
            }
        }
        
        hideDropdown();
    });
    
    input.addEventListener('keydown', (e) => {
        if (dropdown.classList.contains('hidden')) return;
        
        const visibleItems = Array.from(items).filter(item => item.style.display !== 'none');
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                selectedIndex = (selectedIndex + 1) % visibleItems.length;
                updateSelection();
                break;
            case 'ArrowUp':
                e.preventDefault();
                selectedIndex = (selectedIndex - 1 + visibleItems.length) % visibleItems.length;
                updateSelection();
                break;
            case 'Enter':
            case 'Tab':
                e.preventDefault();
                if (selectedIndex >= 0 && visibleItems[selectedIndex]) {
                    const agentId = visibleItems[selectedIndex].getAttribute('data-agent');
                    insertMention(agentId);
                }
                break;
            case 'Escape':
                e.preventDefault();
                hideDropdown();
                break;
        }
    });
    
    // Click to select
    items.forEach(item => {
        item.addEventListener('click', () => {
            const agentId = item.getAttribute('data-agent');
            insertMention(agentId);
        });
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && e.target !== input) {
            hideDropdown();
        }
    });
}

/**
 * Create thread list item element
 * @param {Object} thread - Thread object
 * @param {boolean} isActive - Whether this thread is currently active
 * @returns {HTMLElement} Thread item element
 */
function createThreadItem(thread, isActive = false) {
    const item = document.createElement('div');
    item.className = `thread-item ${isActive ? 'active' : ''}`;
    item.setAttribute('data-thread-id', thread.id);
    
    const icon = document.createElement('span');
    icon.className = 'thread-icon';
    icon.textContent = '💬';
    
    const info = document.createElement('div');
    info.className = 'thread-info';
    
    const title = document.createElement('div');
    title.className = 'thread-title';
    title.textContent = thread.title || '新对话';
    
    const preview = document.createElement('div');
    preview.className = 'thread-preview';
    preview.textContent = thread.lastMessage || '还没有消息';
    
    info.appendChild(title);
    info.appendChild(preview);
    
    const time = document.createElement('span');
    time.className = 'thread-time';
    time.textContent = formatTimestamp(thread.updatedAt);
    
    item.appendChild(icon);
    item.appendChild(info);
    item.appendChild(time);
    
    return item;
}

/**
 * Update thread list
 * @param {Array} threads - Array of thread objects
 * @param {string} activeThreadId - Currently active thread ID
 */
function updateThreadList(threads, activeThreadId) {
    const container = document.getElementById('threads');
    if (!container) return;
    
    container.innerHTML = '';
    
    threads.forEach(thread => {
        const item = createThreadItem(thread, thread.id === activeThreadId);
        container.appendChild(item);
    });
}

/**
 * Auto-resize textarea
 * @param {HTMLTextAreaElement} textarea - Textarea element
 */
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

/**
 * Set connection status indicator
 * @param {string} status - 'online', 'offline', 'connecting'
 */
function setConnectionStatus(status) {
    const indicator = document.getElementById('connection-status');
    if (!indicator) return;
    
    indicator.className = `status ${status}`;
    
    const titles = {
        online: '已连接',
        offline: '未连接',
        connecting: '连接中...'
    };
    
    indicator.title = titles[status] || status;
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AGENTS,
        Toast,
        createMessageBubble,
        parseMentions,
        extractMentions,
        formatTimestamp,
        updateAgentStatus,
        showTypingIndicator,
        hideTypingIndicator,
        scrollToBottom,
        setupMentionAutocomplete,
        createThreadItem,
        updateThreadList,
        autoResizeTextarea,
        setConnectionStatus
    };
}
