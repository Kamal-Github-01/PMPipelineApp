import React, { useState, useEffect, useContext, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChatContext } from '../contexts/ChatContext';
import { AuthContext } from '../contexts/AuthContext';
import './ChatRoom.css';

const ChatRoom = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const { 
    currentChat, 
    messages, 
    loading, 
    error, 
    loadChat, 
    sendMessage, 
    setTyping,
    typingUsers
  } = useContext(ChatContext);
  
  const [messageInput, setMessageInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // Load chat data
  useEffect(() => {
    loadChat(id);
  }, [id, loadChat]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle typing indicator
  useEffect(() => {
    if (isTyping) {
      setTyping(id, true);
    } else {
      setTyping(id, false);
    }
    
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      setTyping(id, false);
    };
  }, [isTyping, id, setTyping]);

  const handleInputChange = (e) => {
    setMessageInput(e.target.value);
    
    // Set typing indicator
    setIsTyping(true);
    
    // Clear previous timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    // Set timeout to stop typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
    }, 2000);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (messageInput.trim() === '') return;
    
    const success = await sendMessage(id, messageInput);
    if (success) {
      setMessageInput('');
      setIsTyping(false);
      
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return <div className="loading">Loading chat...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!currentChat) {
    return <div className="not-found">Chat not found</div>;
  }

  return (
    <div className="chat-room">
      <div className="chat-header">
        <button className="back-button" onClick={() => navigate('/')}>
          &larr; Back
        </button>
        <h2>{currentChat.title}</h2>
        <div className="chat-participants">
          {currentChat.participants.map((participant) => (
            <span key={participant._id} className="participant">
              {participant.username}
            </span>
          ))}
        </div>
      </div>
      
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="no-messages">
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div 
              key={index} 
              className={`message ${message.sender._id === user._id ? 'sent' : 'received'} ${message.isAI ? 'ai-message' : ''}`}
            >
              <div className="message-header">
                <span className="message-sender">
                  {message.isAI ? 'AI Assistant' : message.sender.username}
                </span>
                <span className="message-time">
                  {formatTimestamp(message.timestamp)}
                </span>
              </div>
              <div className="message-content">{message.content}</div>
              {message.nlpAnalysis && (
                <div className="message-nlp">
                  <span className={`sentiment ${message.nlpAnalysis.sentiment}`}>
                    {message.nlpAnalysis.sentiment}
                  </span>
                  {message.nlpAnalysis.intent && (
                    <span className="intent">{message.nlpAnalysis.intent}</span>
                  )}
                </div>
              )}
            </div>
          ))
        )}
        
        {Object.keys(typingUsers).length > 0 && (
          <div className="typing-indicator">
            Someone is typing...
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form className="message-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={messageInput}
          onChange={handleInputChange}
          placeholder="Type your message..."
          className="message-input"
        />
        <button type="submit" className="send-button">
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatRoom;