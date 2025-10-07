const natural = require('natural');
const tokenizer = new natural.WordTokenizer();
const sentiment = new natural.SentimentAnalyzer('English', natural.PorterStemmer, 'afinn');

// Process text with NLP techniques
const processWithNLP = async (text) => {
  try {
    // Tokenize the text
    const tokens = tokenizer.tokenize(text);
    
    // Analyze sentiment
    const sentimentScore = sentiment.getSentiment(tokens);
    let sentimentLabel = 'neutral';
    
    if (sentimentScore > 0.2) {
      sentimentLabel = 'positive';
    } else if (sentimentScore < -0.2) {
      sentimentLabel = 'negative';
    }
    
    // Extract entities (simple implementation)
    const entities = extractEntities(text);
    
    // Determine intent (simple implementation)
    const intent = determineIntent(text);
    
    return {
      sentiment: sentimentLabel,
      entities,
      intent
    };
  } catch (error) {
    console.error('Error in NLP processing:', error);
    return {
      sentiment: 'neutral',
      entities: [],
      intent: 'unknown'
    };
  }
};

// Simple entity extraction (this would be more sophisticated in a real system)
const extractEntities = (text) => {
  const entities = [];
  
  // Look for dates
  const dateRegex = /\b\d{1,2}\/\d{1,2}\/\d{2,4}\b|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(st|nd|rd|th)?,? \d{2,4}\b/gi;
  const dates = text.match(dateRegex) || [];
  
  // Look for emails
  const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
  const emails = text.match(emailRegex) || [];
  
  // Look for URLs
  const urlRegex = /https?:\/\/[^\s]+/g;
  const urls = text.match(urlRegex) || [];
  
  return [...dates, ...emails, ...urls];
};

// Simple intent detection (this would be more sophisticated in a real system)
const determineIntent = (text) => {
  const lowerText = text.toLowerCase();
  
  if (lowerText.includes('hello') || lowerText.includes('hi') || lowerText.includes('hey')) {
    return 'greeting';
  }
  
  if (lowerText.includes('bye') || lowerText.includes('goodbye')) {
    return 'farewell';
  }
  
  if (lowerText.includes('thank')) {
    return 'gratitude';
  }
  
  if (lowerText.includes('help') || lowerText.includes('assist') || lowerText.includes('support')) {
    return 'help_request';
  }
  
  if (lowerText.includes('?')) {
    return 'question';
  }
  
  return 'statement';
};

module.exports = { processWithNLP };