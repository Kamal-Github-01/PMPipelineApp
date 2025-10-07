import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import { AuthContext } from './AuthContext';

export const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const { token, user } = useContext(AuthContext);
  const [chats, setChats] = useState([]);
  const [currentChat, setCurrentChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [socket, setSocket] = useState(null);
  const [typingUsers, setTypingUsers] = useState({});

  // Initialize socket connection
  useEffect(() => {
    if (token && user) {
      const newSocket = io('/', {
        auth: {
          token
        }
      });

      setSocket(newSocket);

      // Socket event listeners
      newSocket.on('connect', () => {
        console.log('Socket connected');
      });

      newSocket.on('error', (error) => {
        console.error('Socket error:', error);
        setError(error.message);
      });

      newSocket.on('new_message', (data) => {
        if (currentChat && data.chatId === currentChat._id) {
          setMessages((prevMessages) => [...prevMessages, data.message]);
        }
        
        // Update chat list to show latest message
        setChats((prevChats) => 
          prevChats.map((chat) => 
            chat._id === data.chatId 
              ? { ...chat, updatedAt: new Date().toISOString() } 
              : chat
          )
        );
      });

      newSocket.on('user_typing', (data) => {
        if (currentChat && data.chatId === currentChat._id) {
          setTypingUsers((prev) => ({ ...prev, [data.userId]: true }));
        }
      });

      newSocket.on('user_stop_typing', (data) => {
        if (currentChat && data.chatId === currentChat._id) {
          setTypingUsers((prev) => {
            const newState = { ...prev };
            delete newState[data.userId];
            return newState;
          });
        }
      });

      return () => {
        newSocket.disconnect();
      };
    }
  }, [token, user, currentChat]);

  // Load user's chats
  const loadChats = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const res = await axios.get('/api/chat');
      setChats(res.data);
      
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load chats');
      setLoading(false);
    }
  };

  // Load a specific chat
  const loadChat = async (chatId) => {
    try {
      setLoading(true);
      setError(null);
      
      const res = await axios.get(`/api/chat/${chatId}`);
      setCurrentChat(res.data);
      setMessages(res.data.messages);
      
      // Join chat room via socket
      if (socket) {
        socket.emit('join_chat', chatId);
      }
      
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load chat');
      setLoading(false);
    }
  };

  // Create a new chat
  const createChat = async (participants, title) => {
    try {
      setLoading(true);
      setError(null);
      
      const res = await axios.post('/api/chat', { participants, title });
      setChats((prevChats) => [res.data, ...prevChats]);
      
      setLoading(false);
      return res.data;
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to create chat');
      setLoading(false);
      return null;
    }
  };

  // Send a message
  const sendMessage = async (chatId, content) => {
    try {
      setError(null);
      
      if (socket) {
        // Send via socket for real-time updates
        socket.emit('send_message', { chatId, content });
      } else {
        // Fallback to REST API if socket is not available
        const res = await axios.post(`/api/chat/${chatId}/message`, { content });
        
        // Update messages
        setMessages((prevMessages) => [
          ...prevMessages, 
          res.data.userMessage,
          res.data.aiMessage
        ]);
      }
      
      return true;
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to send message');
      return false;
    }
  };

  // Set typing indicator
  const setTyping = (chatId, isTyping) => {
    if (socket) {
      if (isTyping) {
        socket.emit('typing', { chatId });
      } else {
        socket.emit('stop_typing', { chatId });
      }
    }
  };

  // Delete a chat
  const deleteChat = async (chatId) => {
    try {
      setError(null);
      
      await axios.delete(`/api/chat/${chatId}`);
      setChats((prevChats) => prevChats.filter((chat) => chat._id !== chatId));
      
      if (currentChat && currentChat._id === chatId) {
        setCurrentChat(null);
        setMessages([]);
      }
      
      return true;
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to delete chat');
      return false;
    }
  };

  return (
    <ChatContext.Provider
      value={{
        chats,
        currentChat,
        messages,
        loading,
        error,
        typingUsers,
        loadChats,
        loadChat,
        createChat,
        sendMessage,
        setTyping,
        deleteChat
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};