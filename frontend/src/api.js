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

  // Get individual concept metadata
  async getConceptMetadata(conceptId) {
    const response = await fetch(`${API_BASE_URL}/concept/${conceptId}`);
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
  },

  // Update learning style preference
  async updateLearningStyle(learnerId, learningStyle) {
    const response = await fetch(`${API_BASE_URL}/learner/${learnerId}/learning-style`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ learningStyle }),
    });
    return response.json();
  },

  // ========================================
  // Course Management APIs
  // ========================================

  // List all courses
  async listCourses() {
    const response = await fetch(`${API_BASE_URL}/courses`);
    if (!response.ok) {
      throw new Error(`Failed to list courses: ${response.statusText}`);
    }
    return response.json();
  },

  // Get course details
  async getCourse(courseId) {
    const response = await fetch(`${API_BASE_URL}/courses/${courseId}`);
    if (!response.ok) {
      throw new Error(`Failed to get course: ${response.statusText}`);
    }
    return response.json();
  },

  // Create a new course
  async createCourse(courseData) {
    // Generate course ID from title
    const courseId = courseData.title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');

    const response = await fetch(`${API_BASE_URL}/courses`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        course_id: courseId,
        title: courseData.title,
        domain: courseData.domain,
        taxonomy: courseData.taxonomy || 'blooms',
        course_learning_outcomes: courseData.courseLearningOutcomes || [],
        // Backward compatibility
        description: courseData.description || null,
        target_audience: courseData.targetAudience || null,
        concepts: (courseData.concepts || []).map(concept => ({
          title: concept.title,
          moduleLearningOutcomes: concept.moduleLearningOutcomes || concept.learningObjectives || [],
          prerequisites: concept.prerequisites || [],
          teachingContent: concept.teachingContent || '',
          vocabulary: concept.vocabulary || []
        }))
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to create course: ${response.statusText}`);
    }

    return response.json();
  },

  // Add source to course
  async addCourseSource(courseId, sourceData) {
    const response = await fetch(`${API_BASE_URL}/courses/${courseId}/sources`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: sourceData.url,
        source_type: sourceData.type,
        title: sourceData.title,
        description: sourceData.description,
        requirement_level: sourceData.requirementLevel || 'optional',
        verification_method: sourceData.verificationMethod || 'none',
        verification_data: sourceData.verificationData || null
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to add source: ${response.statusText}`);
    }

    return response.json();
  },

  // Add source to concept
  async addConceptSource(courseId, conceptId, sourceData) {
    const response = await fetch(`${API_BASE_URL}/courses/${courseId}/concepts/${conceptId}/sources`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: sourceData.url,
        source_type: sourceData.type,
        title: sourceData.title,
        description: sourceData.description,
        requirement_level: sourceData.requirementLevel || 'optional',
        verification_method: sourceData.verificationMethod || 'none',
        verification_data: sourceData.verificationData || null
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to add source: ${response.statusText}`);
    }

    return response.json();
  },

  // Delete source
  async deleteSource(courseId, sourceId) {
    const response = await fetch(`${API_BASE_URL}/courses/${courseId}/sources/${sourceId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to delete source: ${response.statusText}`);
    }

    return response.json();
  }
};
