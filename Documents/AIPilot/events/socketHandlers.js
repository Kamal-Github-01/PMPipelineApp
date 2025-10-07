const jwt = require('jsonwebtoken');
const User = require('../models/User');
const Chat = require('../models/Chat');
const { processWithNLP } = require('../services/nlpService');
const { generateAIResponse } = require('../services/llmService');

// Set up socket.io event handlers
const setupSocketHandlers = (io) => {
  // Middleware for authentication
  io.use((socket, next) => {
    const token = socket.handshake.auth.token;
    
    if (!token) {
      return next(new Error('Authentication error'));
    }
    
    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      socket.user = decoded.user;
      next();
    } catch (error) {
      return next(new Error('Authentication error'));
    }
  });
  
  io.on('connection', (socket) => {
    console.log(`User connected: ${socket.user.id}`);
    
    // Join user to their personal room
    socket.join(socket.user.id);
    
    // Join chat room
    socket.on('join_chat', async (chatId) => {
      try {
        const chat = await Chat.findById(chatId);
        
        if (!chat) {
          socket.emit('error', { message: 'Chat not found' });
          return;
        }
        
        if (!chat.participants.includes(socket.user.id)) {
          socket.emit('error', { message: 'Not authorized to join this chat' });
          return;
        }
        
        socket.join(chatId);
        console.log(`User ${socket.user.id} joined chat ${chatId}`);
      } catch (error) {
        console.error('Error joining chat:', error);
        socket.emit('error', { message: 'Server error' });
      }
    });
    
    // Leave chat room
    socket.on('leave_chat', (chatId) => {
      socket.leave(chatId);
      console.log(`User ${socket.user.id} left chat ${chatId}`);
    });
    
    // Send message
    socket.on('send_message', async (data) => {
      try {
        const { chatId, content } = data;
        
        // Find the chat
        const chat = await Chat.findById(chatId);
        
        if (!chat) {
          socket.emit('error', { message: 'Chat not found' });
          return;
        }
        
        if (!chat.participants.includes(socket.user.id)) {
          socket.emit('error', { message: 'Not authorized to send messages in this chat' });
          return;
        }
        
        // Process message with NLP
        const nlpAnalysis = await processWithNLP(content);
        
        // Create the new message
        const newMessage = {
          sender: socket.user.id,
          content,
          nlpAnalysis
        };
        
        // Add message to chat
        chat.messages.push(newMessage);
        chat.updatedAt = Date.now();
        await chat.save();
        
        // Emit message to all participants in the chat
        io.to(chatId).emit('new_message', {
          chatId,
          message: {
            ...newMessage,
            sender: {
              _id: socket.user.id,
              username: socket.user.username
            }
          }
        });
        
        // Generate AI response
        const aiResponse = await generateAIResponse(content, chat.messages, socket.user.id);
        
        // Add AI response to chat
        const aiMessage = {
          sender: socket.user.id,
          content: aiResponse,
          isAI: true,
          nlpAnalysis: await processWithNLP(aiResponse)
        };
        
        chat.messages.push(aiMessage);
        chat.updatedAt = Date.now();
        await chat.save();
        
        // Emit AI response to all participants
        io.to(chatId).emit('new_message', {
          chatId,
          message: {
            ...aiMessage,
            sender: {
              _id: socket.user.id,
              username: 'AI Assistant'
            }
          }
        });
      } catch (error) {
        console.error('Error sending message:', error);
        socket.emit('error', { message: 'Server error' });
      }
    });
    
    // Typing indicator
    socket.on('typing', (data) => {
      const { chatId } = data;
      socket.to(chatId).emit('user_typing', {
        chatId,
        userId: socket.user.id
      });
    });
    
    // Stop typing indicator
    socket.on('stop_typing', (data) => {
      const { chatId } = data;
      socket.to(chatId).emit('user_stop_typing', {
        chatId,
        userId: socket.user.id
      });
    });
    
    // Disconnect
    socket.on('disconnect', () => {
      console.log(`User disconnected: ${socket.user.id}`);
    });
  });
};

module.exports = { setupSocketHandlers };