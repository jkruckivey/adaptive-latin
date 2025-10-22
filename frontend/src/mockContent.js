// Demo content sequence showing various content types
export const demoContentSequence = [
  {
    type: 'lesson',
    title: 'First Declension Nouns',
    sections: [
      {
        heading: 'What is a Declension?',
        paragraphs: [
          'A declension is a pattern of endings that nouns follow in Latin. Think of it like a template that tells you how to change a word based on its function in a sentence.',
          'In English, we use word order to show meaning. In Latin, we use endings!'
        ],
        callout: {
          type: 'key',
          text: 'Latin word order is flexible because the endings tell us who does what - not the position in the sentence.'
        }
      },
      {
        heading: 'First Declension Basics',
        bullets: [
          'End in -a in the nominative singular',
          'End in -ae in the genitive singular',
          'Almost always feminine gender',
          'Example: puella, puellae (f.) = girl'
        ]
      },
      {
        heading: 'The Five Cases',
        paragraphs: [
          'Latin nouns change endings based on five cases, each showing a different grammatical function:'
        ],
        bullets: [
          'Nominative - Subject (who/what does the action)',
          'Genitive - Possession (whose? of whom?)',
          'Dative - Indirect object (to/for whom?)',
          'Accusative - Direct object (whom/what receives action)',
          'Ablative - Various functions (by/with/from)'
        ]
      }
    ]
  },
  {
    type: 'paradigm-table',
    title: 'Complete Paradigm: Puella (girl)',
    noun: 'puella, puellae (f.)',
    forms: [
      { case: 'Nominative', singular: 'puella', plural: 'puellae', function: 'Subject' },
      { case: 'Genitive', singular: 'puellae', plural: 'puellārum', function: 'Possession' },
      { case: 'Dative', singular: 'puellae', plural: 'puellīs', function: 'Indirect object' },
      { case: 'Accusative', singular: 'puellam', plural: 'puellās', function: 'Direct object' },
      { case: 'Ablative', singular: 'puellā', plural: 'puellīs', function: 'Various uses' }
    ],
    explanation: 'Notice that puellae appears three times (gen. sg., dat. sg., nom. pl.). Context determines which case is meant!'
  },
  {
    type: 'example-set',
    title: 'Examples in Context',
    examples: [
      {
        latin: 'Puella est.',
        translation: 'The girl is.',
        notes: 'Puella is nominative - the subject'
      },
      {
        latin: 'Vita puellae est bona.',
        translation: "The girl's life is good.",
        notes: 'Puellae is genitive singular - showing possession'
      },
      {
        latin: 'Aquam puellae do.',
        translation: 'I give water to the girl.',
        notes: 'Puellae is dative - the indirect object (to whom)'
      },
      {
        latin: 'Puellam video.',
        translation: 'I see the girl.',
        notes: 'Puellam is accusative - the direct object'
      }
    ]
  },
  {
    type: 'multiple-choice',
    question: 'What case is "puellam" in the sentence: "Puellam video"?',
    options: [
      'Nominative (subject)',
      'Genitive (possession)',
      'Accusative (direct object)',
      'Ablative (various uses)'
    ],
    correctAnswer: 2
  },
  {
    type: 'fill-blank',
    sentence: 'Vita ___ est bona. (The life of the girl is good.)',
    blanks: ['genitive singular form of puella'],
    correctAnswers: ['puellae']
  },
  {
    type: 'dialogue',
    question: 'Explain why "puellae" in "Vita puellae" is genitive singular and not nominative plural.',
    context: 'Remember: context and other words in the sentence help you determine which case a form represents.'
  }
]

// Mock function to simulate AI choosing next content
export function getNextContent(currentIndex, userProgress) {
  if (currentIndex >= demoContentSequence.length) {
    return {
      type: 'text',
      html: '<h2>Congratulations! 🎉</h2><p>You\'ve completed the demo sequence. In the full system, the AI would continue with more lessons, exercises, and assessments tailored to your progress.</p>'
    }
  }

  return demoContentSequence[currentIndex]
}

// Mock function to evaluate answers
export function evaluateAnswer(contentType, userAnswer, correctAnswer) {
  // Simplified evaluation for demo
  let score = 0.5 // Default
  let feedback = 'Your answer has been evaluated.'

  if (contentType === 'multiple-choice') {
    score = userAnswer === correctAnswer ? 1.0 : 0.0
    feedback = userAnswer === correctAnswer
      ? 'Excellent! That\'s exactly right. Puellam ends in -am, which is the accusative singular ending.'
      : 'Not quite. Remember to look at the ending: -am indicates accusative case (direct object).'
  }

  return {
    type: 'assessment-result',
    score,
    feedback,
    correctAnswer: contentType === 'multiple-choice' ? demoContentSequence[3].options[correctAnswer] : null,
    calibration: {
      type: 'calibrated',
      message: 'Your confidence matches your performance - great self-awareness!'
    }
  }
}
