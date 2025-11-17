/**
 * Maps Bloom's/Fink's taxonomy action verbs to appropriate assessment types
 *
 * Assessment types:
 * - dialogue: Socratic Q&A, good for understanding and application
 * - written: Extended response, good for analysis, synthesis, evaluation
 * - applied: Performance tasks, good for application and creation
 */

// Bloom's Taxonomy verb mappings
const bloomsVerbMap = {
  // Remember (lowest level) - dialogue works best
  remember: ['define', 'list', 'recall', 'recognize', 'identify', 'name', 'state', 'describe', 'match', 'select'],

  // Understand - dialogue and written
  understand: ['explain', 'summarize', 'paraphrase', 'describe', 'interpret', 'classify', 'compare', 'contrast', 'illustrate', 'exemplify'],

  // Apply - dialogue and applied
  apply: ['apply', 'demonstrate', 'use', 'execute', 'implement', 'solve', 'operate', 'calculate', 'construct', 'modify'],

  // Analyze - written and applied
  analyze: ['analyze', 'differentiate', 'organize', 'attribute', 'compare', 'contrast', 'deconstruct', 'distinguish', 'examine', 'categorize'],

  // Evaluate - written
  evaluate: ['evaluate', 'critique', 'judge', 'justify', 'assess', 'defend', 'argue', 'support', 'validate', 'rate'],

  // Create (highest level) - applied and written
  create: ['create', 'design', 'construct', 'develop', 'formulate', 'produce', 'invent', 'compose', 'plan', 'generate']
}

// Fink's Taxonomy verb mappings
const finksVerbMap = {
  // Foundational Knowledge - dialogue
  foundational: ['define', 'identify', 'recall', 'recognize', 'list', 'describe', 'explain', 'summarize'],

  // Application - applied and dialogue
  application: ['use', 'apply', 'implement', 'perform', 'demonstrate', 'practice', 'execute', 'solve'],

  // Integration - written and applied
  integration: ['connect', 'relate', 'integrate', 'synthesize', 'combine', 'link', 'associate'],

  // Human Dimension - written
  human: ['reflect', 'consider', 'understand', 'appreciate', 'recognize', 'empathize'],

  // Caring - written
  caring: ['value', 'appreciate', 'care about', 'develop interest', 'commit'],

  // Learning How to Learn - written
  learning: ['monitor', 'self-assess', 'reflect', 'evaluate own', 'improve', 'adapt']
}

/**
 * Extract the primary action verb from a learning outcome
 * @param {string} outcome - The learning outcome text
 * @returns {string} The primary verb (lowercase)
 */
export function extractActionVerb(outcome) {
  if (!outcome) return ''

  // Clean and lowercase
  const cleaned = outcome.trim().toLowerCase()

  // Common patterns: "Students will [verb]", "Learners will [verb]", "[Verb] the..."
  const patterns = [
    /(?:students?|learners?|participants?|you) (?:will|can|should) (\w+)/,
    /^(\w+) (?:the|a|an|how|when|where|why)/,
    /^(\w+)/
  ]

  for (const pattern of patterns) {
    const match = cleaned.match(pattern)
    if (match && match[1]) {
      return match[1]
    }
  }

  return ''
}

/**
 * Find the taxonomy level and category for a given verb
 * @param {string} verb - The action verb
 * @param {string} taxonomy - 'blooms' or 'finks'
 * @returns {object} { level, category, confidence }
 */
export function identifyTaxonomyLevel(verb, taxonomy = 'blooms') {
  if (!verb) return { level: 'unknown', category: 'unknown', confidence: 0 }

  const verbMap = taxonomy === 'blooms' ? bloomsVerbMap : finksVerbMap

  // Search for verb in taxonomy map
  for (const [level, verbs] of Object.entries(verbMap)) {
    if (verbs.includes(verb.toLowerCase())) {
      return {
        level,
        category: taxonomy === 'blooms' ? getBloomsCategory(level) : getFinkCategory(level),
        confidence: 1.0
      }
    }
  }

  // Try partial matching (e.g., "analyzing" matches "analyze")
  for (const [level, verbs] of Object.entries(verbMap)) {
    for (const v of verbs) {
      if (verb.toLowerCase().startsWith(v) || v.startsWith(verb.toLowerCase())) {
        return {
          level,
          category: taxonomy === 'blooms' ? getBloomsCategory(level) : getFinkCategory(level),
          confidence: 0.8
        }
      }
    }
  }

  return { level: 'unknown', category: 'unknown', confidence: 0 }
}

function getBloomsCategory(level) {
  const categories = {
    remember: 'Remember (Knowledge)',
    understand: 'Understand (Comprehension)',
    apply: 'Apply (Application)',
    analyze: 'Analyze (Analysis)',
    evaluate: 'Evaluate (Evaluation)',
    create: 'Create (Synthesis)'
  }
  return categories[level] || 'Unknown'
}

function getFinkCategory(level) {
  const categories = {
    foundational: 'Foundational Knowledge',
    application: 'Application',
    integration: 'Integration',
    human: 'Human Dimension',
    caring: 'Caring',
    learning: 'Learning How to Learn'
  }
  return categories[level] || 'Unknown'
}

/**
 * Recommend assessment types based on taxonomy level
 * @param {string} level - The taxonomy level
 * @param {string} taxonomy - 'blooms' or 'finks'
 * @returns {array} Array of { type, weight, rationale }
 */
export function recommendAssessmentTypes(level, taxonomy = 'blooms') {
  if (taxonomy === 'blooms') {
    const bloomsRecommendations = {
      remember: [
        { type: 'dialogue', weight: 0.7, rationale: 'Dialogue questions effectively test recall and recognition' },
        { type: 'applied', weight: 0.3, rationale: 'Simple matching or identification tasks can reinforce memory' }
      ],
      understand: [
        { type: 'dialogue', weight: 0.5, rationale: 'Socratic questioning helps assess comprehension' },
        { type: 'written', weight: 0.5, rationale: 'Explaining in own words demonstrates understanding' }
      ],
      apply: [
        { type: 'applied', weight: 0.6, rationale: 'Performance tasks directly test application skills' },
        { type: 'dialogue', weight: 0.4, rationale: 'Guided practice with feedback supports application' }
      ],
      analyze: [
        { type: 'written', weight: 0.5, rationale: 'Extended response allows demonstration of analytical thinking' },
        { type: 'applied', weight: 0.5, rationale: 'Case studies and problem decomposition test analysis' }
      ],
      evaluate: [
        { type: 'written', weight: 0.8, rationale: 'Evaluation requires justification best shown in written form' },
        { type: 'dialogue', weight: 0.2, rationale: 'Debate-style dialogue can assess evaluative thinking' }
      ],
      create: [
        { type: 'applied', weight: 0.7, rationale: 'Creation requires tangible output/performance' },
        { type: 'written', weight: 0.3, rationale: 'Written plan or proposal demonstrates creative synthesis' }
      ]
    }
    return bloomsRecommendations[level] || []
  } else {
    const finksRecommendations = {
      foundational: [
        { type: 'dialogue', weight: 0.7, rationale: 'Q&A effectively assesses foundational knowledge' },
        { type: 'applied', weight: 0.3, rationale: 'Simple recall tasks reinforce basics' }
      ],
      application: [
        { type: 'applied', weight: 0.7, rationale: 'Fink emphasizes learning by doing' },
        { type: 'dialogue', weight: 0.3, rationale: 'Guided practice with feedback' }
      ],
      integration: [
        { type: 'written', weight: 0.5, rationale: 'Integration requires connecting multiple ideas' },
        { type: 'applied', weight: 0.5, rationale: 'Complex scenarios test integrated understanding' }
      ],
      human: [
        { type: 'written', weight: 0.9, rationale: 'Reflection on human dimension requires extended response' },
        { type: 'dialogue', weight: 0.1, rationale: 'Discussion can probe self-awareness' }
      ],
      caring: [
        { type: 'written', weight: 0.9, rationale: 'Values and commitments best expressed in writing' },
        { type: 'dialogue', weight: 0.1, rationale: 'Conversation can reveal developing values' }
      ],
      learning: [
        { type: 'written', weight: 0.9, rationale: 'Metacognitive reflection requires written self-assessment' },
        { type: 'dialogue', weight: 0.1, rationale: 'Check-ins can monitor learning strategies' }
      ]
    }
    return finksRecommendations[level] || []
  }
}

/**
 * Main function: Analyze a learning outcome and recommend assessment types
 * @param {string} learningOutcome - The learning outcome text
 * @param {string} taxonomy - 'blooms' or 'finks'
 * @returns {object} Analysis with recommendations
 */
export function analyzeOutcomeAndRecommendAssessments(learningOutcome, taxonomy = 'blooms') {
  const verb = extractActionVerb(learningOutcome)
  const { level, category, confidence } = identifyTaxonomyLevel(verb, taxonomy)
  const recommendations = recommendAssessmentTypes(level, taxonomy)

  return {
    outcome: learningOutcome,
    actionVerb: verb,
    taxonomyLevel: level,
    taxonomyCategory: category,
    confidence,
    recommendedAssessments: recommendations,
    summary: generateSummary(verb, category, recommendations)
  }
}

function generateSummary(verb, category, recommendations) {
  if (recommendations.length === 0) {
    return `Could not identify the verb "${verb}". Please use a standard taxonomy verb.`
  }

  const primary = recommendations[0]
  const typeLabels = {
    dialogue: 'Dialogue (Socratic Q&A)',
    written: 'Written (Extended Response)',
    applied: 'Applied (Performance Task)'
  }

  return `The verb "${verb}" falls under ${category}. Recommended: ${typeLabels[primary.type]} (${Math.round(primary.weight * 100)}% weight). ${primary.rationale}`
}

/**
 * Get assessment type emoji
 * @param {string} type - Assessment type
 * @returns {string} Emoji
 */
export function getAssessmentTypeEmoji(type) {
  const emojis = {
    dialogue: '💬',
    written: '✍️',
    applied: '🎯'
  }
  return emojis[type] || '📝'
}

/**
 * Get all verbs for a taxonomy
 * @param {string} taxonomy - 'blooms' or 'finks'
 * @returns {array} Array of all verbs
 */
export function getAllTaxonomyVerbs(taxonomy = 'blooms') {
  const verbMap = taxonomy === 'blooms' ? bloomsVerbMap : finksVerbMap
  return Object.values(verbMap).flat()
}
