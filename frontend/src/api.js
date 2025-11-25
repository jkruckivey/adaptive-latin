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
  async startLearner(learnerId, name, profile = null, courseId = null) {
    const response = await fetch(`${API_BASE_URL}/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        learner_id: learnerId,
        learner_name: name,
        profile: profile,
        course_id: courseId
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
  async getConcepts(learnerId = null, courseId = null) {
    const params = new URLSearchParams();
    if (learnerId) params.append('learner_id', learnerId);
    if (courseId) params.append('course_id', courseId);

    const url = `${API_BASE_URL}/concepts${params.toString() ? '?' + params.toString() : ''}`;
    const response = await fetch(url);
    return response.json();
  },

  // Get individual concept metadata
  async getConceptMetadata(conceptId, learnerId = null, courseId = null) {
    const params = new URLSearchParams();
    if (learnerId) params.append('learner_id', learnerId);
    if (courseId) params.append('course_id', courseId);

    const url = `${API_BASE_URL}/concept/${conceptId}${params.toString() ? '?' + params.toString() : ''}`;
    const response = await fetch(url);
    return response.json();
  },

  // Get modules with their concepts
  async getModules(learnerId = null, courseId = null) {
    const params = new URLSearchParams();
    if (learnerId) params.append('learner_id', learnerId);
    if (courseId) params.append('course_id', courseId);

    const url = `${API_BASE_URL}/modules${params.toString() ? '?' + params.toString() : ''}`;
    const response = await fetch(url);
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
    const requestBody = {
      learner_id: learnerId,
      question_type: questionType,
      user_answer: userAnswer,
      correct_answer: correctAnswer,
      confidence: confidence,
      current_concept: currentConcept,
      question_text: questionText,
      scenario_text: scenarioText,
      options: options
    };

    console.log('submitResponse request:', requestBody);

    const response = await fetch(`${API_BASE_URL}/submit-response`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('Submit response failed:', error, 'Request was:', requestBody);
      throw new Error(error.detail || `Failed to submit response: ${response.statusText}`);
    }

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
    const data = await response.json();
    // Backend returns course data directly
    return data;
  },

  // Create a new course
  async createCourse(courseData) {
    // Generate course ID from title
    const courseId = courseData.title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');

    const requestBody = {
      course_id: courseId,
      title: courseData.title,
      domain: courseData.domain,
      taxonomy: courseData.taxonomy || 'blooms',
      course_learning_outcomes: courseData.courseLearningOutcomes || [],
      // Backward compatibility
      description: courseData.description || null,
      target_audience: courseData.targetAudience || null,
    };

    // Support both module-based and flat concept structures
    if (courseData.modules && courseData.modules.length > 0) {
      // Module-based structure (new)
      requestBody.modules = courseData.modules.map(module => ({
        moduleId: module.moduleId,
        title: module.title,
        moduleLearningOutcomes: module.moduleLearningOutcomes || [],
        concepts: (module.concepts || []).map(concept => ({
          conceptId: concept.conceptId,
          title: concept.title,
          learningObjectives: concept.learningObjectives || [],
          prerequisites: concept.prerequisites || [],
          teachingContent: concept.teachingContent || '',
          vocabulary: concept.vocabulary || []
        }))
      }));
    } else {
      // Flat concept structure (backward compatibility)
      requestBody.concepts = (courseData.concepts || []).map(concept => ({
        title: concept.title,
        moduleLearningOutcomes: concept.moduleLearningOutcomes || concept.learningObjectives || [],
        prerequisites: concept.prerequisites || [],
        teachingContent: concept.teachingContent || '',
        vocabulary: concept.vocabulary || []
      }));
    }

    const response = await fetch(`${API_BASE_URL}/courses`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to create course: ${response.statusText}`);
    }

    return response.json();
  },

  // Export course to JSON
  async exportCourse(courseId) {
    const response = await fetch(`${API_BASE_URL}/courses/${courseId}/export`);
    if (!response.ok) {
      throw new Error(`Failed to export course: ${response.statusText}`);
    }
    return response.json();
  },

  // Import course from JSON
  async importCourse(exportData, newCourseId = null, overwrite = false) {
    const response = await fetch(`${API_BASE_URL}/courses/import`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        export_data: exportData,
        new_course_id: newCourseId,
        overwrite: overwrite
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to import course: ${response.statusText}`);
    }

    return response.json();
  },

  // Parse syllabus document with AI
  async parseSyllabus(file, domain = null, taxonomy = 'blooms') {
    const formData = new FormData();
    formData.append('file', file);
    if (domain) formData.append('domain', domain);
    formData.append('taxonomy', taxonomy);

    const response = await fetch(`${API_BASE_URL}/courses/parse-syllabus`, {
      method: 'POST',
      body: formData, // Don't set Content-Type, browser will set it with boundary
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to parse syllabus: ${response.statusText}`);
    }

    return response.json();
  },

  // Generate learning outcomes with AI
  async generateLearningOutcomes(description, taxonomy = 'blooms', level = 'course', count = 5, existingOutcomes = null) {
    const response = await fetch(`${API_BASE_URL}/generate-learning-outcomes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        description,
        taxonomy,
        level,
        count,
        existing_outcomes: existingOutcomes
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to generate learning outcomes: ${response.statusText}`);
    }

    return response.json();
  },

  // Generate assessments with AI based on learning outcome
  async generateAssessments(learningOutcome, taxonomy = 'blooms', domain = 'general', numAssessments = 3) {
    const response = await fetch(`${API_BASE_URL}/generate-assessments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        learning_outcome: learningOutcome,
        taxonomy,
        domain,
        num_assessments: numAssessments
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to generate assessments: ${response.statusText}`);
    }

    return response.json();
  },

  // Import Common Cartridge (.imscc) file
  async importCartridge(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/courses/import-cartridge`, {
      method: 'POST',
      body: formData, // Don't set Content-Type, browser will set it with boundary
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to import cartridge: ${response.statusText}`);
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
  },

  // ========================================
  // AI Generation APIs
  // ========================================

  // Generate module learning outcomes with AI
  async generateModuleLearningOutcomes(moduleTitle, courseTitle, courseLearningOutcomes, domain, taxonomy = 'blooms') {
    const response = await fetch(`${API_BASE_URL}/generate-module-learning-outcomes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        module_title: moduleTitle,
        course_title: courseTitle,
        course_learning_outcomes: courseLearningOutcomes,
        domain,
        taxonomy
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to generate module outcomes: ${response.statusText}`);
    }

    return response.json();
  },

  // Generate concept learning objectives with AI
  async generateConceptLearningObjectives(conceptTitle, moduleTitle, moduleLearningOutcomes, courseTitle, domain, taxonomy = 'blooms') {
    const response = await fetch(`${API_BASE_URL}/generate-concept-learning-objectives`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        concept_title: conceptTitle,
        module_title: moduleTitle,
        module_learning_outcomes: moduleLearningOutcomes,
        course_title: courseTitle,
        domain,
        taxonomy
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to generate concept objectives: ${response.statusText}`);
    }

    return response.json();
  },

  // Generate interactive simulation
  async generateSimulation(simulationType, courseFormat, data) {
    const response = await fetch(`${API_BASE_URL}/generate-simulation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        simulation_type: simulationType,
        course_format: courseFormat,
        data: data
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to generate simulation: ${response.statusText}`);
    }

    return response.json();
  },

  // Evaluate dialogue response for multi-turn conversations
  async evaluateDialogue(learnerId, conceptId, question, context, answer, exchangeCount) {
    const response = await fetch(`${API_BASE_URL}/evaluate-dialogue`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        learner_id: learnerId,
        concept_id: conceptId,
        question: question,
        context: context || "",
        answer: answer,
        exchange_count: exchangeCount
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to evaluate dialogue: ${response.statusText}`);
    }

    return response.json();
  }
};
