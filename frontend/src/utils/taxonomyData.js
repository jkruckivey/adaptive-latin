// Bloom's Taxonomy - Cognitive Domain (Hierarchical)
export const bloomsTaxonomy = {
  name: "Bloom's Taxonomy",
  description: "Best for cognitive skills and traditional academic subjects",
  hierarchical: true,
  levels: [
    {
      id: 'remember',
      name: 'Remember',
      description: 'Recall facts and basic concepts',
      verbs: [
        'Define', 'Describe', 'Identify', 'Label', 'List', 'Match',
        'Name', 'Recall', 'Recognize', 'Reproduce', 'Select', 'State'
      ],
      examples: [
        'Define key vocabulary terms',
        'List the steps in the process',
        'Recall important dates and events'
      ]
    },
    {
      id: 'understand',
      name: 'Understand',
      description: 'Explain ideas or concepts',
      verbs: [
        'Classify', 'Compare', 'Contrast', 'Demonstrate', 'Explain',
        'Extend', 'Illustrate', 'Infer', 'Interpret', 'Outline',
        'Relate', 'Rephrase', 'Show', 'Summarize', 'Translate'
      ],
      examples: [
        'Explain the relationship between concepts',
        'Summarize the main ideas in your own words',
        'Illustrate the concept with examples'
      ]
    },
    {
      id: 'apply',
      name: 'Apply',
      description: 'Use information in new situations',
      verbs: [
        'Apply', 'Build', 'Choose', 'Construct', 'Develop', 'Execute',
        'Experiment', 'Identify', 'Implement', 'Interview', 'Make use of',
        'Model', 'Organize', 'Plan', 'Select', 'Solve', 'Utilize'
      ],
      examples: [
        'Apply grammatical rules to construct sentences',
        'Solve problems using learned formulas',
        'Implement the technique in a new context'
      ]
    },
    {
      id: 'analyze',
      name: 'Analyze',
      description: 'Draw connections among ideas',
      verbs: [
        'Analyze', 'Attribute', 'Break down', 'Categorize', 'Compare',
        'Contrast', 'Deconstruct', 'Differentiate', 'Discriminate',
        'Distinguish', 'Examine', 'Experiment', 'Infer', 'Organize', 'Question'
      ],
      examples: [
        'Analyze sentence structures to identify grammatical relationships',
        'Compare and contrast different approaches',
        'Distinguish between similar concepts'
      ]
    },
    {
      id: 'evaluate',
      name: 'Evaluate',
      description: 'Justify a decision or course of action',
      verbs: [
        'Appraise', 'Argue', 'Assess', 'Choose', 'Compare', 'Conclude',
        'Contrast', 'Critique', 'Defend', 'Evaluate', 'Judge', 'Justify',
        'Predict', 'Prioritize', 'Prove', 'Rank', 'Rate', 'Select', 'Support'
      ],
      examples: [
        'Evaluate translations for accuracy and style',
        'Critique the effectiveness of different methods',
        'Justify your interpretation with evidence'
      ]
    },
    {
      id: 'create',
      name: 'Create',
      description: 'Produce new or original work',
      verbs: [
        'Assemble', 'Compose', 'Construct', 'Create', 'Design', 'Develop',
        'Devise', 'Formulate', 'Generate', 'Hypothesize', 'Invent',
        'Make', 'Originate', 'Plan', 'Produce', 'Propose', 'Write'
      ],
      examples: [
        'Create original compositions in Latin',
        'Design a solution to a complex problem',
        'Compose an essay synthesizing multiple perspectives'
      ]
    }
  ]
}

// Fink's Taxonomy of Significant Learning (Non-Hierarchical)
export const finksTaxonomy = {
  name: "Fink's Taxonomy",
  description: "Best for holistic learning including affective and metacognitive dimensions",
  hierarchical: false,
  dimensions: [
    {
      id: 'foundational',
      name: 'Foundational Knowledge',
      description: 'Understanding and remembering information and ideas',
      verbs: [
        'Define', 'Describe', 'Explain', 'Identify', 'List', 'Name',
        'Recall', 'Recognize', 'Reproduce', 'State', 'Summarize', 'Tell'
      ],
      examples: [
        'Define key terminology and concepts',
        'Recall fundamental principles',
        'Explain basic theories'
      ]
    },
    {
      id: 'application',
      name: 'Application',
      description: 'Skills, critical thinking, creative thinking, and practical thinking',
      verbs: [
        'Apply', 'Calculate', 'Demonstrate', 'Execute', 'Implement',
        'Perform', 'Practice', 'Solve', 'Use', 'Operate', 'Employ'
      ],
      examples: [
        'Apply grammatical rules to construct sentences',
        'Perform linguistic analysis on texts',
        'Use learned skills in practical situations'
      ]
    },
    {
      id: 'integration',
      name: 'Integration',
      description: 'Connecting information, ideas, perspectives, people, or realms of life',
      verbs: [
        'Associate', 'Blend', 'Combine', 'Compare', 'Connect', 'Contrast',
        'Correlate', 'Differentiate', 'Integrate', 'Intermix', 'Join',
        'Link', 'Relate', 'Synthesize', 'Unite'
      ],
      examples: [
        'Connect Latin grammatical concepts to English language patterns',
        'Relate historical context to linguistic development',
        'Synthesize knowledge across different subject areas'
      ]
    },
    {
      id: 'human-dimension',
      name: 'Human Dimension',
      description: 'Learning about oneself and others',
      verbs: [
        'Acquire', 'Advise', 'Advocate', 'Behave', 'Collaborate', 'Communicate',
        'Cooperate', 'Empathize', 'Express', 'Help', 'Influence', 'Initiate',
        'Inspire', 'Interact', 'Involve', 'Lead', 'Mediate', 'Motivate',
        'Negotiate', 'Nurture', 'Promote', 'Reflect', 'Respect', 'Share', 'Support'
      ],
      examples: [
        'Collaborate with peers to analyze complex texts',
        'Reflect on personal learning strategies and preferences',
        'Communicate effectively in academic discussions'
      ]
    },
    {
      id: 'caring',
      name: 'Caring',
      description: 'Developing new feelings, interests, and values',
      verbs: [
        'Appreciate', 'Believe', 'Cherish', 'Commit to', 'Decide to',
        'Demonstrate', 'Develop', 'Discover', 'Embrace', 'Explore',
        'Express', 'Identify', 'Interpret', 'Pledge', 'Prioritize',
        'Recognize', 'Renew', 'Share', 'Value'
      ],
      examples: [
        'Appreciate the cultural significance of Latin in Western civilization',
        'Value the importance of precision in language',
        'Develop interest in classical literature and history'
      ]
    },
    {
      id: 'learning-to-learn',
      name: 'Learning How to Learn',
      description: 'Becoming a better student and self-directed learner',
      verbs: [
        'Adapt', 'Analyze learning process', 'Construct knowledge', 'Create a plan',
        'Critique own work', 'Describe strategies', 'Develop learning plan',
        'Formulate questions', 'Frame questions', 'Generalize', 'Identify resources',
        'Identify learning style', 'Inquire', 'Monitor progress', 'Predict performance',
        'Reflect', 'Research', 'Self-assess', 'Set goals'
      ],
      examples: [
        'Self-assess understanding and identify knowledge gaps',
        'Develop effective strategies for memorizing vocabulary',
        'Reflect on learning progress and adjust study methods'
      ]
    }
  ]
}

// Domain-specific examples for Course Learning Outcomes
export const domainExamples = {
  'Mathematics': {
    blooms: [
      'Analyze mathematical patterns to identify underlying relationships',
      'Apply mathematical concepts to solve real-world problems',
      'Evaluate the validity of mathematical arguments and proofs'
    ],
    finks: [
      'Apply mathematical reasoning to model and solve practical problems',
      'Connect mathematical concepts across different areas of mathematics',
      'Appreciate the elegance and power of mathematical thinking'
    ]
  },
  'Science': {
    blooms: [
      'Analyze experimental data to draw evidence-based conclusions',
      'Evaluate scientific claims using critical thinking and evidence',
      'Design experiments to test scientific hypotheses'
    ],
    finks: [
      'Apply scientific methods to investigate natural phenomena',
      'Connect scientific concepts to everyday life and current events',
      'Develop curiosity and appreciation for the natural world'
    ]
  },
  'Language Learning': {
    blooms: [
      'Analyze grammatical structures to understand language patterns',
      'Apply linguistic rules to construct grammatically correct sentences',
      'Create original compositions demonstrating mastery of language structures'
    ],
    finks: [
      'Apply language skills to communicate effectively in authentic contexts',
      'Connect linguistic patterns between the target language and native language',
      'Appreciate the cultural contexts embedded in language use',
      'Reflect on personal language learning strategies and progress'
    ]
  },
  'History': {
    blooms: [
      'Analyze historical sources to evaluate their reliability and perspective',
      'Evaluate the causes and consequences of historical events',
      'Synthesize information from multiple sources to construct historical arguments'
    ],
    finks: [
      'Connect historical events to contemporary issues and experiences',
      'Appreciate the complexity of historical narratives and perspectives',
      'Reflect on how historical understanding shapes personal worldview'
    ]
  },
  'Programming': {
    blooms: [
      'Apply programming concepts to design and implement software solutions',
      'Analyze code to identify bugs and optimize performance',
      'Create well-structured programs following best practices'
    ],
    finks: [
      'Apply problem-solving strategies to break down complex programming tasks',
      'Collaborate with peers to develop and review code',
      'Develop self-directed learning skills to master new programming languages'
    ]
  },
  'Arts': {
    blooms: [
      'Analyze artistic works to interpret meaning and technique',
      'Apply artistic principles to create original works',
      'Evaluate artistic works using established criteria and personal perspective'
    ],
    finks: [
      'Express personal perspectives and emotions through artistic creation',
      'Appreciate diverse artistic traditions and cultural contexts',
      'Reflect on personal artistic development and creative process'
    ]
  },
  'Music': {
    blooms: [
      'Analyze musical compositions to identify structure and techniques',
      'Apply music theory concepts to perform and create music',
      'Evaluate musical performances using technical and expressive criteria'
    ],
    finks: [
      'Perform music expressively to communicate meaning and emotion',
      'Connect musical elements to cultural and historical contexts',
      'Develop appreciation for diverse musical traditions'
    ]
  },
  'Business': {
    blooms: [
      'Analyze business scenarios to identify problems and opportunities',
      'Evaluate business strategies using financial and strategic criteria',
      'Create business plans that synthesize market analysis and strategic thinking'
    ],
    finks: [
      'Apply business concepts to real-world organizational challenges',
      'Collaborate effectively in team-based business projects',
      'Develop ethical decision-making skills in business contexts'
    ]
  },
  'Health & Medicine': {
    blooms: [
      'Analyze patient data to diagnose conditions and recommend treatments',
      'Evaluate medical research to determine evidence-based practices',
      'Apply clinical reasoning to make informed healthcare decisions'
    ],
    finks: [
      'Communicate effectively with patients and healthcare team members',
      'Demonstrate empathy and cultural sensitivity in patient care',
      'Reflect on ethical considerations in healthcare practice'
    ]
  },
  'Other': {
    blooms: [
      'Analyze information to identify patterns and relationships',
      'Apply learned concepts to solve problems in new contexts',
      'Evaluate arguments and evidence to make informed judgments'
    ],
    finks: [
      'Connect course concepts to personal experiences and other disciplines',
      'Develop self-directed learning skills for continued growth',
      'Appreciate the relevance and value of the subject matter'
    ]
  }
}

// Quality indicators for learning outcomes
export const qualityIndicators = {
  weak: ['understand', 'know', 'learn', 'appreciate', 'be aware of', 'become familiar with', 'gain knowledge of'],
  strong: ['analyze', 'evaluate', 'create', 'design', 'construct', 'synthesize', 'critique', 'formulate', 'assess'],
  required: {
    startsWithVerb: true,
    measurable: true,
    learnerCentric: true,
    minLength: 20
  }
}

// Helper functions
export function checkOutcomeQuality(outcome) {
  const feedback = []
  const outcomeText = outcome.toLowerCase().trim()

  // Check for weak verbs
  const weakVerbFound = qualityIndicators.weak.find(verb =>
    outcomeText.startsWith(verb) || outcomeText.includes(`will ${verb}`) || outcomeText.includes(`be able to ${verb}`)
  )
  if (weakVerbFound) {
    feedback.push({
      type: 'warning',
      message: `The verb "${weakVerbFound}" is not measurable. Try a more specific action verb.`
    })
  }

  // Check for learner-centric language
  if (!outcomeText.includes('student') && !outcomeText.includes('learner')) {
    feedback.push({
      type: 'info',
      message: 'Consider starting with "Students will be able to..." for learner-centered outcomes.'
    })
  }

  // Check length
  if (outcome.length < 20) {
    feedback.push({
      type: 'warning',
      message: 'Learning outcome seems too brief. Add more detail about what students will do.'
    })
  }

  // Check for action verb
  const hasActionVerb = [...bloomsTaxonomy.levels, ...finksTaxonomy.dimensions].some(level =>
    (level.verbs || []).some(verb => outcomeText.includes(verb.toLowerCase()))
  )

  if (!hasActionVerb) {
    feedback.push({
      type: 'warning',
      message: 'No action verb detected. Start with a measurable verb from Bloom\'s or Fink\'s taxonomy.'
    })
  }

  // Positive feedback
  if (feedback.length === 0) {
    feedback.push({
      type: 'success',
      message: 'This learning outcome looks well-structured!'
    })
  }

  return feedback
}

export function suggestAlternativeVerbs(weakVerb) {
  const alternatives = {
    'understand': ['explain', 'describe', 'interpret', 'summarize', 'classify'],
    'know': ['identify', 'define', 'list', 'recall', 'recognize'],
    'learn': ['apply', 'demonstrate', 'practice', 'implement', 'use'],
    'appreciate': ['value', 'recognize', 'express', 'demonstrate', 'advocate for']
  }

  return alternatives[weakVerb.toLowerCase()] || []
}
