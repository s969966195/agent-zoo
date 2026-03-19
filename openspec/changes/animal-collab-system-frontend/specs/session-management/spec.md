## ADDED Requirements

### Requirement: Start new conversation
The system SHALL provide an easy way to start a new conversation with animal agents.

#### Scenario: Initiate new chat
- **WHEN** user clicks "New Chat" or "+" button
- **THEN** a dialog or panel opens showing available animal agents
- **AND** user can select one or more animals to chat with

#### Scenario: Create conversation with selected animals
- **WHEN** user confirms animal selection
- **THEN** a new conversation is created with a generated or editable title
- **AND** the chat interface opens with a welcome message from the animals

#### Scenario: Quick start with default
- **WHEN** user clicks quick-start option
- **THEN** a conversation is created with default animal agent(s)
- **AND** the chat begins immediately

### Requirement: Terminate conversation
The system SHALL allow users to gracefully end or leave conversations.

#### Scenario: End conversation
- **WHEN** user clicks "End Chat" or close button
- **THEN** a confirmation dialog appears explaining the action
- **AND** options are provided to "Save & End", "End Without Saving", or "Cancel"

#### Scenario: Auto-save on end
- **WHEN** user chooses "Save & End"
- **THEN** the conversation is saved to history
- **AND** the user is returned to the main/dashboard view

#### Scenario: Discard conversation
- **WHEN** user chooses "End Without Saving"
- **THEN** the conversation is discarded
- **AND** a brief undo notification is shown (cartoon-styled toast)

### Requirement: Session indicators
The system SHALL show the current session status and active participants.

#### Scenario: Display active session
- **WHEN** user is in an active conversation
- **THEN** a header shows the conversation title and active animal agents
- **AND** online/presence indicators show which agents are "active"

#### Scenario: Session timeout warning
- **WHEN** a session has been idle for an extended period
- **THEN** a friendly, cartoon-styled warning appears
- **AND** user can choose to continue or end the session

### Requirement: Conversation state management
The system SHALL handle conversation states (active, paused, ended) gracefully.

#### Scenario: Resume conversation
- **WHEN** user returns to an ongoing conversation
- **THEN** the full chat history is restored
- **AND** the conversation continues seamlessly

#### Scenario: Multiple concurrent sessions
- **WHEN** user has multiple active conversations
- **THEN** a tab or list interface allows switching between them
- **AND** unread message counts are shown for inactive conversations
