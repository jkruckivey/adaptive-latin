import { useState } from 'react'
import './TeachingMoment.css'

function TeachingMoment({ content, onSubmit, onConfidenceChange }) {
  const [stage, setStage] = useState(1) // 1 = part1, 2 = part2, 3 = results
  const [part1Answer, setPart1Answer] = useState(null)
  const [part2Answer, setPart2Answer] = useState(null)
  const [confidence, setConfidence] = useState(null)

  const handlePart1Submit = () => {
    if (part1Answer !== null) {
      setStage(2)
    }
  }

  const handlePart2Submit = () => {
    if (part2Answer !== null && confidence !== null) {
      // Determine combination (e.g., "b1", "a3")
      const combination = part1Answer + part2Answer

      // Find scoring category
      let score = 0.5
      let feedback = ''

      if (content.scoring.excellent.combinations.some(c => matchesCombination(combination, c))) {
        score = 0.95
        feedback = content.scoring.excellent.feedback
      } else if (content.scoring.good.combinations.some(c => matchesCombination(combination, c))) {
        score = 0.80
        feedback = content.scoring.good.feedback
      } else if (content.scoring.developing.combinations.some(c => matchesCombination(combination, c))) {
        score = 0.65
        feedback = content.scoring.developing.feedback
      } else if (content.scoring.insufficient.combinations.some(c => matchesCombination(combination, c))) {
        score = 0.40
        feedback = content.scoring.insufficient.feedback
      }

      // Submit to parent
      onSubmit({
        part1Answer,
        part2Answer,
        combination,
        score,
        feedback,
        confidence
      })

      setStage(3)
    }
  }

  // Helper to match combinations with wildcards
  const matchesCombination = (actual, pattern) => {
    if (pattern === actual) return true

    // Handle wildcards like "a*" (any part2 when part1 is 'a')
    if (pattern.endsWith('*')) {
      return actual.startsWith(pattern.slice(0, -1))
    }

    // Handle wildcards like "*2" (any part1 when part2 is '2')
    if (pattern.startsWith('*')) {
      return actual.endsWith(pattern.slice(1))
    }

    return false
  }

  const handleConfidenceChange = (stars) => {
    setConfidence(stars)
    if (onConfidenceChange) {
      onConfidenceChange(stars)
    }
  }

  const part1Option = part1Answer ? content.part1.options.find(o => o.id === part1Answer) : null
  const pushbackText = part1Answer ? content.part2.pushbacks[part1Answer] : null

  return (
    <div className="teaching-moment">
      {/* Scenario Setup */}
      <div className="scenario-card">
        <div className="scenario-header">
          <span className="character-icon">👤</span>
          <span className="character-name">{content.scenario.character}</span>
        </div>
        <div className="scenario-situation">
          {content.scenario.situation}
        </div>
        <div className="scenario-misconception">
          <span className="quote-icon">"</span>
          {content.scenario.misconception}
          <span className="quote-icon">"</span>
        </div>
      </div>

      {/* Part 1: Initial Response */}
      {stage >= 1 && (
        <div className={`part-section ${stage > 1 ? 'completed' : 'active'}`}>
          <div className="part-header">
            <span className="part-number">Part 1</span>
            <span className="part-title">{content.part1.prompt}</span>
          </div>

          <div className="options-list">
            {content.part1.options.map((option) => (
              <label
                key={option.id}
                className={`option-item ${part1Answer === option.id ? 'selected' : ''} ${stage > 1 ? 'disabled' : ''}`}
              >
                <input
                  type="radio"
                  name="part1"
                  value={option.id}
                  checked={part1Answer === option.id}
                  onChange={(e) => setPart1Answer(e.target.value)}
                  disabled={stage > 1}
                />
                <span className="option-label">{option.text}</span>
              </label>
            ))}
          </div>

          {stage === 1 && (
            <button
              onClick={handlePart1Submit}
              className="submit-button"
              disabled={part1Answer === null}
            >
              Submit Response
            </button>
          )}

          {stage > 1 && part1Option && (
            <div className="selected-answer-summary">
              <strong>You said:</strong> "{part1Option.text}"
            </div>
          )}
        </div>
      )}

      {/* Part 2: Pushback & Defense */}
      {stage >= 2 && (
        <div className={`part-section ${stage > 2 ? 'completed' : 'active'}`}>
          <div className="pushback-card">
            <div className="scenario-header">
              <span className="character-icon">👤</span>
              <span className="character-name">{content.scenario.character} responds:</span>
            </div>
            <div className="pushback-text">
              <span className="quote-icon">"</span>
              {pushbackText}
              <span className="quote-icon">"</span>
            </div>
          </div>

          <div className="part-header">
            <span className="part-number">Part 2</span>
            <span className="part-title">{content.part2.prompt}</span>
          </div>

          <div className="options-list">
            {content.part2.options.map((option) => (
              <label
                key={option.id}
                className={`option-item ${part2Answer === option.id ? 'selected' : ''} ${stage > 2 ? 'disabled' : ''}`}
              >
                <input
                  type="radio"
                  name="part2"
                  value={option.id}
                  checked={part2Answer === option.id}
                  onChange={(e) => setPart2Answer(e.target.value)}
                  disabled={stage > 2}
                />
                <span className="option-label">{option.text}</span>
              </label>
            ))}
          </div>

          {stage === 2 && (
            <>
              {/* Confidence Slider */}
              <div className="confidence-section">
                <label className="confidence-label">How confident are you in this response?</label>
                <div className="confidence-stars">
                  {[1, 2, 3, 4].map((stars) => (
                    <button
                      key={stars}
                      onClick={() => handleConfidenceChange(stars)}
                      className={`star-button ${confidence === stars ? 'selected' : ''}`}
                      type="button"
                    >
                      {'⭐'.repeat(stars)}
                    </button>
                  ))}
                </div>
                <div className="confidence-labels">
                  <span>Guessing</span>
                  <span>Unsure</span>
                  <span>Confident</span>
                  <span>Very Sure</span>
                </div>
              </div>

              <button
                onClick={handlePart2Submit}
                className="submit-button"
                disabled={part2Answer === null || confidence === null}
              >
                Submit Final Response
              </button>
            </>
          )}
        </div>
      )}

      {/* Results shown by parent component (AssessmentResult) */}
    </div>
  )
}

export default TeachingMoment
