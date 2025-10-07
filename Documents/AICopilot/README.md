# AI-Powered Chat System

A comprehensive chat application that demonstrates NLP, LLM integration, event-driven architecture, and role-based access control.

## Key Features

- **Natural Language Processing (NLP)**: Analyzes messages for sentiment, entities, and intent
- **LLM Integration**: Uses OpenAI's GPT models to generate AI responses
- **Event-Driven Architecture**: Real-time communication using Socket.io
- **Role-Based Access Control**: Different permission levels for users, moderators, and admins

## Tech Stack

- **Backend**: Node.js, Express
- **Frontend**: React
- **Database**: MongoDB
- **Real-time Communication**: Socket.io
- **Authentication**: JWT
- **NLP**: Natural.js
- **LLM**: OpenAI API

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- MongoDB
- Redis (optional, for scaling)
- OpenAI API key

### Installation

1. Clone the repository
2. Install server dependencies:


---------------------------------------------

Notes



3. Access the application at `http://localhost:3000`

## Architecture

### NLP Processing

The system uses Natural.js to analyze messages for:
- Sentiment analysis (positive, negative, neutral)
- Entity extraction (dates, emails, URLs)
- Intent detection (greeting, question, help request, etc.)

### LLM Integration

The system integrates with OpenAI's GPT models to:
- Generate contextually relevant responses
- Maintain conversation history for better context
- Provide helpful and accurate information

### Event-Driven Architecture

The system uses Socket.io to implement an event-driven architecture:
- Real-time message delivery
- Typing indicators
- Presence awareness
- Event-based notifications

### Role-Based Access Control

The system implements three user roles:
- **User**: Basic chat functionality
- **Moderator**: Can moderate chats and messages
- **Admin**: Full system access and user management

## API Endpoints

### Authentication
- `POST /api/auth/register`: Register a new user
- `POST /api/auth/login`: Login a user
- `GET /api/auth/me`: Get current user

### Chat
- `GET /api/chat`: Get all chats for a user
- `GET /api/chat/:id`: Get a specific chat
- `POST /api/chat`: Create a new chat
- `POST /api/chat/:id/message`: Send a message in a chat
- `DELETE /api/chat/:id`: Delete a chat

## Socket.io Events

- `join_chat`: Join a chat room
- `leave_chat`: Leave a chat room
- `send_message`: Send a message
- `new_message`: Receive a new message
- `typing`: User is typing
- `user_typing`: Notify that a user is typing
- `stop_typing`: User stopped typing
- `user_stop_typing`: Notify that a user stopped typing

## License

MIT
