# Cat Café Web Interface

Phase 6 of the Cat Café multi-agent system - A beautiful, functional web UI for interacting with AI cat agents.

## 📁 Directory Structure

```
web/
├── static/
│   ├── index.html          # Main HTML file
│   ├── css/
│   │   └── styles.css      # Warm cozy theme styles
│   ├── js/
│   │   ├── app.js          # Main application logic
│   │   ├── websocket.js    # WebSocket client
│   │   └── components.js   # UI components
│   └── assets/
│       └── (avatar files)  # Placeholder for cat avatars
└── templates/
    └── (Jinja2 templates - optional)
```

## 🎨 Design System

### Color Palette

**Background Colors:**
- `--bg-primary`: #FFF8F0 (warm cream)
- `--bg-secondary`: #FFF5E6 (lighter cream)
- `--bg-card`: #FFFFFF (white cards)

**Agent Colors:**
- **布偶猫 (Ragdoll)**: Blue/purple tones (#7986CB, #C5CAE9)
- **缅因猫 (Maine Coon)**: Orange/brown tones (#FF9800, #FFCC80)
- **暹罗猫 (Siamese)**: Cream/tan tones (#8D6E63, #D7CCC8)

**Accent Colors:**
- `--accent-primary`: #F59E0B (warm amber)
- `--accent-secondary`: #FCD34D (soft gold)

### Typography

- **Display Font**: 'ZCOOL KuaiLe' - Cute Chinese display font
- **Body Font**: 'Noto Sans SC' - Clean Chinese sans-serif

## 🚀 Features

### Core Features
- ✅ Real-time messaging via WebSocket
- ✅ @mention autocomplete for agents
- ✅ Typing indicators when agents are active
- ✅ Stop button during agent execution
- ✅ Thread management (create, switch, delete)
- ✅ Agent status display
- ✅ Responsive design for mobile
- ✅ Dark mode support

### UI Components
- **Message Bubbles**: Gradient backgrounds per agent
- **Agent Cards**: Real-time status with animations
- **Thread List**: With preview and timestamps
- **Typing Indicator**: Bouncing dots animation
- **Toast Notifications**: Success/error/info messages
- **Mention Dropdown**: Smart autocomplete

## 🔌 API Integration

### WebSocket Events

**Outgoing:**
- `subscribe` - Subscribe to thread updates
- `unsubscribe` - Unsubscribe from thread

**Incoming:**
- `text` - Agent message
- `typing` - Agent started typing
- `thinking` - Agent is thinking
- `done` - Agent finished
- `error` - Error occurred
- `agent_status` - Agent status update

### REST Endpoints

- `POST /api/messages` - Send message
- `GET /api/threads` - List threads
- `POST /api/threads` - Create thread
- `GET /api/threads/{id}/messages` - Get messages
- `POST /api/threads/{id}/cancel` - Stop execution
- `GET /api/agents/status` - Get agent status

## 🐱 Agent Configuration

```javascript
const AGENTS = {
    ragdoll: {
        id: 'ragdoll',
        name: '布偶猫',
        aliases: ['布偶猫', '布偶', 'ragdoll'],
        avatar: '🐱',
        description: '优雅的绅士'
    },
    maine: {
        id: 'maine',
        name: '缅因猫',
        aliases: ['缅因猫', '缅因', 'maine'],
        avatar: '😺',
        description: '强壮的探险家'
    },
    siamese: {
        id: 'siamese',
        name: '暹罗猫',
        aliases: ['暹罗猫', '暹罗', 'siamese'],
        avatar: '🐈',
        description: '机智的智者'
    }
};
```

## 📱 Responsive Breakpoints

- **Desktop**: 1200px+ (3-column layout)
- **Tablet**: 768px - 1199px (2-column, hide agent panel)
- **Mobile**: < 768px (1-column, hide sidebars)

## 🎯 Usage

1. Open `index.html` in a browser
2. WebSocket auto-connects to `ws://localhost:8000/api/ws`
3. Type `@布偶猫`, `@缅因猫`, or `@暹罗猫` to mention agents
4. Press Enter or click Send to send message
5. Click Stop button to halt agent execution

## 🔧 Development

### File Responsibilities

- **index.html**: Structure, SVG avatars, layout
- **styles.css**: Design system, animations, responsive styles
- **components.js**: Message rendering, agent status, mentions
- **websocket.js**: WebSocket client, REST API wrapper
- **app.js**: Main app logic, event handling, thread management

### Key Classes

- `CatCafeWebSocket`: WebSocket connection management
- `CatCafeApp`: Main application controller
- `Toast`: Notification system

## ✨ Design Highlights

1. **Warm Atmosphere**: Cream backgrounds, soft shadows, gentle animations
2. **Cat Identity**: Each agent has distinct colors and personality
3. **Smooth Interactions**: Staggered reveals, hover effects, typing animations
4. **Accessibility**: Focus states, keyboard navigation, ARIA labels
5. **Mobile-First**: Touch-friendly, collapsible sidebars

## 🎭 Theme Support

The UI supports both light and dark modes:
- Toggle via theme button in header
- Automatically detects system preference
- CSS custom properties for easy theming

---

Part of the Cat Café Multi-Agent System
