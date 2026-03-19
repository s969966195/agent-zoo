## ADDED Requirements

### Requirement: Conversation persistence
The system SHALL persist conversation history locally and/or remotely so users can access past conversations.

#### Scenario: Save conversation
- **WHEN** a conversation ends or at regular intervals
- **THEN** all messages are saved to storage
- **AND** conversation metadata (participants, start time, title) is stored

#### Scenario: Load conversation history
- **WHEN** user opens the history view
- **THEN** a list of past conversations is displayed
- **AND** each conversation shows title, date, and participant preview

### Requirement: Conversation list view
The system SHALL display a scrollable list of past conversations with search and filter capabilities.

#### Scenario: View all conversations
- **WHEN** user navigates to history
- **THEN** conversations are displayed in reverse chronological order (newest first)
- **AND** each item shows title, date, animal participants, and message count

#### Scenario: Search conversations
- **WHEN** user enters search terms in the history search box
- **THEN** conversations are filtered to show only those matching the query
- **AND** matching terms are highlighted in results

#### Scenario: Filter by animal
- **WHEN** user selects an animal filter (e.g., only show chats with "Rabbit" agent)
- **THEN** only conversations involving that animal agent are displayed

### Requirement: Conversation detail view
The system SHALL allow users to view the full content of past conversations.

#### Scenario: Open conversation
- **WHEN** user clicks on a conversation from the list
- **THEN** the full conversation is displayed in read-only mode
- **AND** the original cartoon styling and avatars are preserved

#### Scenario: Return to history
- **WHEN** user clicks back from a conversation detail
- **THEN** they return to the conversation list
- **AND** scroll position is maintained

### Requirement: Conversation management
The system SHALL allow users to rename, delete, or favorite conversations.

#### Scenario: Rename conversation
- **WHEN** user clicks the rename action on a conversation
- **THEN** an inline edit mode is activated
- **AND** the new name is saved on blur or Enter key

#### Scenario: Delete conversation
- **WHEN** user clicks delete on a conversation
- **THEN** a confirmation dialog appears with cartoon styling
- **AND** upon confirmation, the conversation is permanently removed

#### Scenario: Favorite conversation
- **WHEN** user clicks the favorite/star action
- **THEN** the conversation is marked as favorite
- **AND** favorite conversations appear at the top of the list or in a dedicated section
