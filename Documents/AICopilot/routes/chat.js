const express = require('express');
const router = express.Router();
const Chat = require('../models/Chat');
const { authMiddleware, roleMiddleware } = require('../middleware/auth');
const { processWithNLP } = require('../services/nlpService');
const { generateAIResponse } = require('../services/llmService');

// Get all chats for a user
router.get('/', authMiddleware, async (req, res) => {
  try {
    const chats = await Chat.find({ participants: req.user.id })
      .sort({ updatedAt: -1 })
      .populate('participants', 'username email');
    
    res.json(chats);
  } catch (error) {
    console.error('Error getting chats:', error.message);
    res.status(500).send('Server error');
  }
});

// Get a single chat by ID
router.get('/:id', authMiddleware, async (req, res) => {
  try {
    const chat = await Chat.findById(req.params.id)
      .populate('participants', 'username email')
      .populate('messages.sender', 'username email');
    
    // Check if chat exists
    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }
    
    // Check if user is a participant
    if (!chat.participants.some(p => p._id.toString() === req.user.id)) {
      return res.status(403).json({ message: 'Not authorized to view this chat' });
    }
    
    res.json(chat);
  } catch (error) {
    console.error('Error getting chat:', error.message);
    res.status(500).send('Server error');
  }
});

// Create a new chat
router.post('/', authMiddleware, async (req, res) => {
  try {
    const { participants, title } = req.body;
    
    // Ensure current user is included in participants
    const allParticipants = [...new Set([req.user.id, ...participants])];
    
    const newChat = new Chat({
      participants: allParticipants,
      title: title || 'New Chat'
    });
    
    await newChat.save();
    
    res.json(newChat);
  } catch (error) {
    console.error('Error creating chat:', error.message);
    res.status(500).send('Server error');
  }
});

// Send a message in a chat
router.post('/:id/message', authMiddleware, async (req, res) => {
  try {
    const { content } = req.body;
    const chatId = req.params.id;
    
    // Find the chat
    const chat = await Chat.findById(chatId);
    
    // Check if chat exists
    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }
    
    // Check if user is a participant
    if (!chat.participants.includes(req.user.id)) {
      return res.status(403).json({ message: 'Not authorized to send messages in this chat' });
    }
    
    // Process message with NLP
    const nlpAnalysis = await processWithNLP(content);
    
    // Create the new message
    const newMessage = {
      sender: req.user.id,
      content,
      nlpAnalysis
    };
    
    // Add message to chat
    chat.messages.push(newMessage);
    chat.updatedAt = Date.now();
    await chat.save();
    
    // Generate AI response
    const aiResponse = await generateAIResponse(content, chat.messages, req.user.id);
    
    // Add AI response to chat
    const aiMessage = {
      sender: req.user.id, // We're using the same user ID but marking it as AI
      content: aiResponse,
      isAI: true,
      nlpAnalysis: await processWithNLP(aiResponse)
    };
    
    chat.messages.push(aiMessage);
    chat.updatedAt = Date.now();
    await chat.save();
    
    // Emit event for real-time updates (handled by socket.io)
    
    res.json({
      userMessage: newMessage,
      aiMessage
    });
  } catch (error) {
    console.error('Error sending message:', error.message);
    res.status(500).send('Server error');
  }
});

// Delete a chat (admin or owner only)
router.delete('/:id', authMiddleware, async (req, res) => {
  try {
    const chat = await Chat.findById(req.params.id);
    
    // Check if chat exists
    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }
    
    // Check if user is admin or a participant
    const isAdmin = req.user.role === 'admin';
    const isParticipant = chat.participants.includes(req.user.id);
    
    if (!isAdmin && !isParticipant) {
      return res.status(403).json({ message: 'Not authorized to delete this chat' });
    }
    
    await chat.remove();
    
    res.json({ message: 'Chat deleted' });
  } catch (error) {
    console.error('Error deleting chat:', error.message);
    res.status(500).send('Server error');
  }
});

module.exports = router;