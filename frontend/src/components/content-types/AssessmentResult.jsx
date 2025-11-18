import { useState } from 'react'
import { api } from '../../api'
import './AssessmentResult.css'

function AssessmentResult({ score, feedback, correctAnswer, userAnswer, calibration, onContinue, learnerId, learnerProfile }) {
  const [currentStyle, setCurrentStyle] = useState(learnerProfile?.learningStyle || 'varied')
  const [isChangingStyle, setIsChangingStyle] = useState(false)
  const [showStylePicker, setShowStylePicker] = useState(false)

  const getScoreClass = () => {
    if (score >= 0.9) return 'excellent'
    if (score >= 0.7) return 'good'
    if (score >= 0.5) return 'developing'
    return 'needs-work'
  }

  const getScoreEmoji = () => {
    if (score >= 0.9) return ''
    if (score >= 0.7) return ''
    if (score >= 0.5) return ''
    return ''
  }

  const styleLabels = {
    narrative: 'Story-based learning',
    varied: 'Varied content types',
    adaptive: 'Adaptive progression'
  }

  const handleStyleChange = async (newStyle) => {
    if (!learnerId || newStyle === currentStyle) return

    setIsChangingStyle(true)
    try {
      const result = await api.updateLearningStyle(learnerId, newStyle)
      if (result.success) {
        setCurrentStyle(newStyle)
        setShowStylePicker(false)
        // Update localStorage
        const storedProfile = JSON.parse(localStorage.getItem('learnerProfile') || '{}')
        storedProfile.learningStyle = newStyle
        localStorage.setItem('learnerProfile', JSON.stringify(storedProfile))
      }
    } catch (error) {
      console.error('Error updating learning style:', error)
    } finally {
      setIsChangingStyle(false)
    }
  }

  const isCorrect = score >= 1.0;

  return (
    <div className="assessment-result">
      {/* Combined feedback box */}
      <div className={`result-box ${isCorrect ? 'correct' : 'incorrect'}`}>
        <div className="result-status">
          <span className="status-icon">{isCorrect ? '✓' : '✗'}</span>
          <span className="status-text">{isCorrect ? 'Correct' : 'Incorrect'}</span>
        </div>

        <div className="feedback-text">
          {userAnswer && (
            <p className="user-choice">
              <strong>You chose:</strong> {userAnswer}
            </p>
          )}

          {!isCorrect && correctAnswer && (
            <p className="correct-choice">
              <strong>Correct answer:</strong> {correctAnswer}
            </p>
          )}

          {feedback && <p className="feedback-message">{feedback}</p>}
        </div>
      </div>

      {calibration && (
        <div className={`result-calibration ${calibration.type}`}>
          <div className="calibration-icon">
          </div>
          <div className="calibration-message">{calibration.message}</div>
        </div>
      )}

      {learnerId && (
        <div className="learning-style-section">
          <div className="current-style">
            <span className="style-label">Current learning preference: </span>
            <strong>{styleLabels[currentStyle]}</strong>
            <button
              onClick={() => setShowStylePicker(!showStylePicker)}
              className="change-style-button"
            >
              {showStylePicker ? 'Cancel' : 'Change'}
            </button>
          </div>

          {showStylePicker && (
            <div className="style-picker">
              <p className="style-picker-hint">Choose how you'd like to receive feedback:</p>
              {Object.entries(styleLabels).map(([style, label]) => (
                <button
                  key={style}
                  onClick={() => handleStyleChange(style)}
                  disabled={isChangingStyle || style === currentStyle}
                  className={`style-option ${style === currentStyle ? 'active' : ''}`}
                >
                  {label}
                  {style === currentStyle && ' (current)'}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="result-footer">
        <button onClick={onContinue} className="continue-button">
          Continue Learning →
        </button>
      </div>
    </div>
  )
}

export default AssessmentResult
