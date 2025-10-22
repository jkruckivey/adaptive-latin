import './AssessmentResult.css'

function AssessmentResult({ score, feedback, correctAnswer, calibration, onContinue }) {
  const getScoreClass = () => {
    if (score >= 0.9) return 'excellent'
    if (score >= 0.7) return 'good'
    if (score >= 0.5) return 'developing'
    return 'needs-work'
  }

  const getScoreEmoji = () => {
    if (score >= 0.9) return '🎯'
    if (score >= 0.7) return '👍'
    if (score >= 0.5) return '📚'
    return '💪'
  }

  return (
    <div className="assessment-result">
      <div className={`result-score ${getScoreClass()}`}>
        <div className="score-emoji">{getScoreEmoji()}</div>
        <div className="score-value">{Math.round(score * 100)}%</div>
      </div>

      <div className="result-feedback">
        <h3>Feedback:</h3>
        <p>{feedback}</p>
      </div>

      {correctAnswer && (
        <div className="result-correct-answer">
          <h4>Correct Answer:</h4>
          <div className="correct-answer-text">{correctAnswer}</div>
        </div>
      )}

      {calibration && (
        <div className={`result-calibration ${calibration.type}`}>
          <div className="calibration-icon">
            {calibration.type === 'overconfident' && '⬆️'}
            {calibration.type === 'underconfident' && '⬇️'}
            {calibration.type === 'calibrated' && '✓'}
          </div>
          <div className="calibration-message">{calibration.message}</div>
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
