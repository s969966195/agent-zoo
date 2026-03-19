## ADDED Requirements

### Requirement: Real-time chat display
The system SHALL display messages in real-time with a cartoon-style chat interface featuring rounded message bubbles and animal avatars.

#### Scenario: User sends a message
- **WHEN** user types a message and presses send
- **THEN** the message appears in the chat with user's avatar
- **AND** the message bubble has cartoon-style rounded corners and playful colors

#### Scenario: Agent responds
- **WHEN** an animal agent sends a response
- **THEN** the message appears with the agent's animal avatar
- **AND** a typing indicator is shown while the agent is "thinking"

### Requirement: Typing indicators
The system SHALL show animated typing indicators when animal agents are preparing responses.

#### Scenario: Agent is typing
- **WHEN** an agent is generating a response
- **THEN** an animated typing indicator (bouncing dots or animal-themed animation) is displayed
- **AND** the indicator disappears when the response arrives

### Requirement: Message formatting
The system SHALL support basic text formatting including emoji, line breaks, and simple markdown.

#### Scenario: Message with formatting
- **WHEN** a message contains formatting markers (e.g., **bold**, *italic*)
- **THEN** the formatting is rendered in the chat bubble
- **AND** emojis are displayed with appropriate size for cartoon aesthetic

### Requirement: Chat input interface
The system SHALL provide a playful, cartoon-styled input area for typing messages.

#### Scenario: User focuses input
- **WHEN** user clicks on the chat input area
- **THEN** the input field animates with a playful focus state (e.g., slight bounce, border color change)
- **AND** placeholder text uses friendly, inviting language

#### Scenario: Send message action
- **WHEN** user presses Enter or clicks the send button
- **THEN** the message is sent
- **AND** the send button provides visual feedback (animation, color change)

### Requirement: Animal avatars
The system SHALL display distinctive animal avatars for each participant in the chat.

#### Scenario: Display participant avatars
- **WHEN** a message is displayed
- **THEN** the sender's avatar is shown next to the message
- **AND** user avatars are differentiated from animal agent avatars by style (e.g., user has profile icon, agents have cartoon animal faces)
