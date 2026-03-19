## ADDED Requirements

### Requirement: Animal agent profiles
The system SHALL display animal agents with distinct personas including name, avatar, species, and personality traits.

#### Scenario: View animal roster
- **WHEN** user opens the animal selection panel
- **THEN** all available animal agents are displayed as cards
- **AND** each card shows the animal's avatar, name, species, and brief personality description

#### Scenario: View animal details
- **WHEN** user clicks on an animal card
- **THEN** a detailed profile view opens
- **AND** it displays full description, traits, specialties, and example greetings

### Requirement: Distinct visual identities
The system SHALL give each animal agent a unique visual identity matching their species and personality.

#### Scenario: Animal avatar design
- **WHEN** an animal agent is displayed
- **THEN** their avatar reflects their species (rabbit, fox, elephant, etc.)
- **AND** the avatar style matches the cartoon/Zootopia aesthetic (playful, friendly, expressive)

#### Scenario: Color themes per animal
- **WHEN** an animal sends a message
- **THEN** their message bubbles use a color associated with that animal
- **AND** the color scheme reinforces their personality (e.g., warm colors for friendly animals, cool colors for calm ones)

### Requirement: Personality expression
The system SHALL allow animal agents to express their personalities through visual cues and animations.

#### Scenario: Animated reactions
- **WHEN** an animal agent reacts to a message
- **THEN** an appropriate animation plays (e.g., bouncing for excitement, head tilt for curiosity)
- **AND** the animation matches the animal's character

#### Scenario: Typing style indicators
- **WHEN** an animal is typing
- **THEN** the typing indicator reflects their personality
- **AND** for example, a rabbit might have quick, energetic bouncing dots while a turtle has slow, steady pulses

### Requirement: Animal selection and customization
The system SHALL allow users to select which animals to interact with.

#### Scenario: Select animals for chat
- **WHEN** user starts a new conversation
- **THEN** they can browse and select from available animals
- **AND** selection is visually indicated with cartoon-style checkmarks or highlights

#### Scenario: Favorite animals
- **WHEN** user frequently chats with certain animals
- **THEN** those animals can be marked as favorites
- **AND** favorites appear at the top of the selection list

### Requirement: Animal status indicators
The system SHALL show the availability and status of animal agents.

#### Scenario: Display animal status
- **WHEN** viewing the animal roster
- **THEN** each animal shows a status indicator (available, busy, offline)
- **AND** the indicator uses intuitive icons (green dot, orange clock, gray moon)

#### Scenario: Status transitions
- **WHEN** an animal's status changes during a session
- **THEN** a subtle notification appears
- **AND** the avatar may show a brief animation indicating the change
