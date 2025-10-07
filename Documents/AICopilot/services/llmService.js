const { OpenAI } = require('openai');

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// Generate AI response using OpenAI
const generateAIResponse = async (userMessage, chatHistory, userId) => {
  try {
    // Format chat history for OpenAI
    const formattedHistory = chatHistory
      .slice(-10) // Only use the last 10 messages for context
      .map(msg => ({
        role: msg.isAI ? 'assistant' : 'user',
        content: msg.content
      }));
    
    // Add the current message
    formattedHistory.push({
      role: 'user',
      content: userMessage
    });
    
    // Call OpenAI API
    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful AI assistant in a chat application. Provide concise, accurate, and helpful responses.'
        },
        ...formattedHistory
      ],
      max_tokens: 500,
      temperature: 0.7
    });
    
    return response.choices[0].message.content;
  } catch (error) {
    console.error('Error generating AI response:', error);
    return 'I apologize, but I encountered an error processing your request. Please try again later.';
  }
};

module.exports = { generateAIResponse };