// API Base URL - use proxy in development, direct URL in production
const API_BASE_URL = import.meta.env.PROD
  ? 'https://adaptive-latin-backend.onrender.com'
  : '/api';

export const api = {
  // Health check
  async healthCheck() {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  },

  // Start a new learner
  async startLearner(learnerId, name, profile = null) {
    const response = await fetch(`${API_BASE_URL}/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        learner_id: learnerId,
        learner_name: name,
        profile: profile
      }),
    });
    return response.json();
  },

  // Send chat message
  async sendMessage(learnerId, message) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ learner_id: learnerId, message }),
    });
    return response.json();
  },

  // Get learner progress
  async getProgress(learnerId) {
    const response = await fetch(`${API_BASE_URL}/progress/${learnerId}`);
    return response.json();
  },

  // Get available concepts
  async getConcepts() {
    const response = await fetch(`${API_BASE_URL}/concepts`);
    return response.json();
  },

  // Get mastery score
  async getMastery(learnerId, conceptId) {
    const response = await fetch(`${API_BASE_URL}/mastery/${learnerId}/${conceptId}`);
    return response.json();
  },

  // Get full learner model (including profile)
  async getLearnerModel(learnerId) {
    const response = await fetch(`${API_BASE_URL}/learner/${learnerId}`);
    return response.json();
  },

  // Generate personalized content using AI
  async generateContent(learnerId, stage = 'start') {
    const response = await fetch(`${API_BASE_URL}/generate-content?learner_id=${learnerId}&stage=${stage}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    return response.json();
  },

  // Submit learner response with confidence for evaluation
  async submitResponse(learnerId, questionType, userAnswer, correctAnswer, confidence, currentConcept, questionText = null, scenarioText = null, options = null) {
    const response = await fetch(`${API_BASE_URL}/submit-response`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        learner_id: learnerId,
        question_type: questionType,
        user_answer: userAnswer,
        correct_answer: correctAnswer,
        confidence: confidence,
        current_concept: currentConcept,
        question_text: questionText,
        scenario_text: scenarioText,
        options: options
      }),
    });
    return response.json();
  },

  // Get concepts due for review (spaced repetition)
  async getDueReviews(learnerId, includeUpcoming = 0) {
    const response = await fetch(`${API_BASE_URL}/reviews/${learnerId}?include_upcoming=${includeUpcoming}`);
    return response.json();
  },

  // Get review statistics
  async getReviewStats(learnerId) {
    const response = await fetch(`${API_BASE_URL}/review-stats/${learnerId}`);
    return response.json();
  }
};
