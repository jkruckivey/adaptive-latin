import { useEffect, useState } from 'react'
import './MasteryProgressBar.css'

function MasteryProgressBar({ masteryScore, masteryThreshold, conceptName, assessmentsCount }) {
  const [displayScore, setDisplayScore] = useState(masteryScore)

  // Animate progress bar when mastery score changes
  useEffect(() => {
    // Small delay for animation effect
    const timer = setTimeout(() => {
      setDisplayScore(masteryScore)
    }, 100)

    return () => clearTimeout(timer)
  }, [masteryScore])

  const percentage = Math.round(masteryScore * 100)
  const thresholdPercentage = Math.round(masteryThreshold * 100)
  const MIN_ASSESSMENTS = 3  // Match backend requirement
  const isComplete = masteryScore >= masteryThreshold && assessmentsCount >= MIN_ASSESSMENTS

  // Determine progress bar color based on mastery level
  let progressColor = '#667eea' // Default purple
  if (masteryScore >= masteryThreshold) {
    progressColor = '#48bb78' // Green when complete
  } else if (masteryScore >= masteryThreshold * 0.75) {
    progressColor = '#f6ad55' // Orange when getting close
  }

  return (
    <div className="mastery-progress-container">
      <div className="progress-header">
        <div className="progress-label">
          <span className="concept-name">{conceptName || 'Current Concept'}</span>
          {isComplete && <span className="completion-badge">✓ Mastered</span>}
        </div>
        <span className="assessment-count">{assessmentsCount} {assessmentsCount === 1 ? 'assessment' : 'assessments'}</span>
      </div>

      <div className="progress-bar-wrapper">
        <div className="progress-bar-track">
          {/* Threshold marker */}
          <div
            className="threshold-marker"
            style={{ left: `${thresholdPercentage}%` }}
            title={`${thresholdPercentage}% needed to master`}
          >
            <div className="threshold-line"></div>
            <div className="threshold-label">{thresholdPercentage}%</div>
          </div>

          {/* Progress fill */}
          <div
            className="progress-bar-fill"
            style={{
              width: `${displayScore * 100}%`,
              backgroundColor: progressColor,
              transition: 'all 0.6s ease-out'
            }}
          >
            {displayScore > 0.15 && (
              <span className="progress-fill-text">{percentage}%</span>
            )}
          </div>
        </div>

        {/* Helper text */}
        <div className="progress-hint">
          {!isComplete && assessmentsCount < MIN_ASSESSMENTS && (
            <>
              <span className="hint-icon"></span>
              <span>
                Complete at least {MIN_ASSESSMENTS} assessments to master this concept ({assessmentsCount}/{MIN_ASSESSMENTS} done)
              </span>
            </>
          )}
          {!isComplete && assessmentsCount >= MIN_ASSESSMENTS && (
            <>
              <span className="hint-icon"></span>
              <span>
                Your mastery score can go up or down based on recent performance.
                Keep practicing to reach {thresholdPercentage}%!
              </span>
            </>
          )}
          {isComplete && (
            <>
              <span className="hint-icon"></span>
              <span>
                Excellent work! You've mastered this concept. Continue to the next one!
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default MasteryProgressBar
