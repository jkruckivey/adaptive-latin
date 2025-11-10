import { useState, useEffect } from 'react'
import './CurriculumRoadmap.css'

function CurriculumRoadmap({ courseData, onClose }) {
  const [analysis, setAnalysis] = useState(null)

  useEffect(() => {
    // Analyze the course for topic coverage
    analyzeCoverage()
  }, [courseData])

  const analyzeCoverage = () => {
    const concepts = courseData.concepts || []

    // Extract all topics from objectives and vocabulary
    const allTopics = []
    const topicsByConceptIndex = []

    concepts.forEach((concept, index) => {
      const conceptTopics = extractTopics(concept)
      topicsByConceptIndex.push(conceptTopics)
      allTopics.push(...conceptTopics)
    })

    // Find patterns and gaps
    const patterns = detectPatterns(allTopics)
    const gaps = identifyGaps(patterns, allTopics, concepts.length)

    setAnalysis({
      totalConcepts: concepts.length,
      topicsByConceptIndex,
      patterns,
      gaps,
      progressionScore: calculateProgressionScore(concepts)
    })
  }

  const extractTopics = (concept) => {
    const topics = []

    // Extract from title
    const titleWords = (concept.title || '').toLowerCase().split(/\s+/)
    topics.push(...titleWords.filter(w => w.length > 3))

    // Extract from objectives
    const objectives = concept.learningObjectives || []
    objectives.forEach(obj => {
      const words = obj.toLowerCase().split(/\s+/)
      topics.push(...words.filter(w => w.length > 4))
    })

    // Extract from vocabulary terms
    const vocab = concept.vocabulary || []
    vocab.forEach(v => {
      if (v.term) topics.push(v.term.toLowerCase())
    })

    return [...new Set(topics)] // Remove duplicates
  }

  const detectPatterns = (topics) => {
    const patterns = {
      numbered: [],
      repeated: {},
      categories: []
    }

    // Detect numbered sequences (e.g., "first", "second", "third")
    const numberWords = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh']
    numberWords.forEach((num, i) => {
      if (topics.some(t => t.includes(num))) {
        patterns.numbered.push({ number: i + 1, word: num, found: true })
      }
    })

    // Detect repeated concepts with numbers (e.g., "declension", "conjugation")
    topics.forEach(topic => {
      const match = topic.match(/(\w+)/)
      if (match) {
        const base = match[1]
        if (base.length > 4) {
          patterns.repeated[base] = (patterns.repeated[base] || 0) + 1
        }
      }
    })

    // Find frequently repeated base words
    const frequent = Object.entries(patterns.repeated)
      .filter(([word, count]) => count >= 2)
      .sort((a, b) => b[1] - a[1])

    patterns.categories = frequent.map(([word, count]) => ({ word, count }))

    return patterns
  }

  const identifyGaps = (patterns, topics, conceptCount) => {
    const gaps = []

    // Check for incomplete number sequences
    if (patterns.numbered.length > 0) {
      const maxFound = Math.max(...patterns.numbered.map(n => n.number))

      // Check if it's a sequence like "5 declensions" or "4 conjugations"
      patterns.categories.forEach(cat => {
        if (cat.count >= 2 && cat.count < 5) {
          // Common sequences: 5 declensions, 4 conjugations, 3 genders, etc.
          const expectedCounts = {
            'declension': 5,
            'conjugation': 4,
            'tense': 6,
            'case': 5,
            'gender': 3,
            'number': 2
          }

          const expected = expectedCounts[cat.word]
          if (expected && cat.count < expected) {
            gaps.push({
              type: 'incomplete_sequence',
              topic: cat.word,
              found: cat.count,
              expected: expected,
              message: `Only ${cat.count} of ${expected} ${cat.word}s covered`
            })
          }
        }
      })
    }

    // Check concept count
    if (conceptCount < 3) {
      gaps.push({
        type: 'too_few_concepts',
        message: 'Consider adding more concepts for comprehensive coverage',
        severity: 'warning'
      })
    }

    // Check for prerequisite gaps
    // (concepts that seem advanced without foundational concepts)

    return gaps
  }

  const calculateProgressionScore = (concepts) => {
    let score = 0

    // Points for having concepts
    score += Math.min(concepts.length * 10, 50)

    // Points for well-defined objectives
    const avgObjectives = concepts.reduce((sum, c) =>
      sum + (c.learningObjectives || []).length, 0) / concepts.length
    if (avgObjectives >= 3) score += 20

    // Points for content depth
    const avgContentLength = concepts.reduce((sum, c) =>
      sum + (c.teachingContent || '').length, 0) / concepts.length
    if (avgContentLength >= 500) score += 20

    // Points for good prerequisite structure
    const hasPrereqs = concepts.some(c => (c.prerequisites || []).length > 0)
    if (hasPrereqs) score += 10

    return Math.min(score, 100)
  }

  if (!analysis) {
    return (
      <div className="roadmap-container">
        <div className="roadmap-loading">
          <div className="spinner"></div>
          <p>Analyzing curriculum...</p>
        </div>
      </div>
    )
  }

  const concepts = courseData.concepts || []

  return (
    <div className="roadmap-container">
      <div className="roadmap-header">
        <h2>Curriculum Roadmap</h2>
        <button onClick={onClose} className="close-button">×</button>
      </div>

      <div className="roadmap-content">
        {/* Progression Score */}
        <div className="roadmap-section">
          <h3>Course Strength Score</h3>
          <div className="score-display">
            <div className="score-circle">
              <svg viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="#e0e0e0" strokeWidth="8"/>
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke={analysis.progressionScore >= 70 ? '#28a745' : '#ffc107'}
                  strokeWidth="8"
                  strokeDasharray={`${analysis.progressionScore * 2.83} 283`}
                  strokeLinecap="round"
                  transform="rotate(-90 50 50)"
                />
              </svg>
              <div className="score-text">{analysis.progressionScore}</div>
            </div>
            <div className="score-description">
              {analysis.progressionScore >= 80 && "Excellent curriculum structure"}
              {analysis.progressionScore >= 60 && analysis.progressionScore < 80 && "Good foundation, consider expanding"}
              {analysis.progressionScore < 60 && "Add more content for comprehensive coverage"}
            </div>
          </div>
        </div>

        {/* Visual Roadmap */}
        <div className="roadmap-section">
          <h3>Learning Path</h3>
          <div className="concept-flow">
            {concepts.map((concept, index) => {
              const prereqs = concept.prerequisites || []
              const hasPrereqs = prereqs.length > 0

              return (
                <div key={index} className="concept-node-container">
                  {hasPrereqs && (
                    <div className="prerequisite-connections">
                      {prereqs.map(prereqId => {
                        const prereqIndex = concepts.findIndex(c => c.id === prereqId)
                        return (
                          <div key={prereqId} className="prereq-line">
                            ↓ requires Concept {prereqIndex + 1}
                          </div>
                        )
                      })}
                    </div>
                  )}

                  <div className="concept-node">
                    <div className="concept-number">{index + 1}</div>
                    <div className="concept-info">
                      <div className="concept-title">{concept.title}</div>
                      <div className="concept-meta">
                        <span className="meta-item">
                          {(concept.learningObjectives || []).length} objectives
                        </span>
                        <span className="meta-item">
                          {(concept.vocabulary || []).length} terms
                        </span>
                      </div>
                      {analysis.topicsByConceptIndex[index] && (
                        <div className="concept-topics">
                          {analysis.topicsByConceptIndex[index].slice(0, 5).map((topic, i) => (
                            <span key={i} className="topic-tag">{topic}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {index < concepts.length - 1 && (
                    <div className="flow-arrow">↓</div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Coverage Analysis */}
        {analysis.patterns.categories.length > 0 && (
          <div className="roadmap-section">
            <h3>Topic Coverage</h3>
            <div className="coverage-analysis">
              {analysis.patterns.categories.map((cat, i) => (
                <div key={i} className="coverage-item">
                  <span className="coverage-topic">{cat.word}</span>
                  <span className="coverage-count">{cat.count} concept{cat.count !== 1 ? 's' : ''}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Gaps & Suggestions */}
        {analysis.gaps.length > 0 && (
          <div className="roadmap-section">
            <h3>Suggestions for Improvement</h3>
            <div className="gaps-list">
              {analysis.gaps.map((gap, i) => (
                <div key={i} className={`gap-item ${gap.severity || 'info'}`}>
                  <div className="gap-icon">
                </div>
                  <div className="gap-content">
                    <div className="gap-message">{gap.message}</div>
                    {gap.expected && (
                      <div className="gap-detail">
                        Consider adding {gap.expected - gap.found} more concept{gap.expected - gap.found !== 1 ? 's' : ''}
                        {gap.topic && ` covering ${gap.topic}`}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {analysis.gaps.length === 0 && analysis.progressionScore >= 70 && (
          <div className="roadmap-section">
            <div className="success-message">
              Your curriculum looks well-structured! Learners will progress through {concepts.length} concepts
              with clear learning objectives.
            </div>
          </div>
        )}
      </div>

      <div className="roadmap-actions">
        <button onClick={onClose} className="wizard-button primary">
          Continue to Review
        </button>
      </div>
    </div>
  )
}

export default CurriculumRoadmap
