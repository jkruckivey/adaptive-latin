import { useEffect } from 'react'
import confetti from 'canvas-confetti'
import './ConceptMasteryModal.css'

function ConceptMasteryModal({ conceptId, masteryScore, onContinue }) {
  const conceptNumber = conceptId?.split('-')[1] || '001'

  useEffect(() => {
    // Trigger confetti explosion
    const duration = 3000
    const end = Date.now() + duration

    const frame = () => {
      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: ['#646cff', '#ffffff', '#48bb78']
      })
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: ['#646cff', '#ffffff', '#48bb78']
      })

      if (Date.now() < end) {
        requestAnimationFrame(frame)
      }
    }

    frame()
  }, [])

  return (
    <div className="mastery-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="mastery-title">
      <div className="mastery-modal">
        <div className="mastery-celebration">
          <div className="mastery-icon" aria-hidden="true"></div>
          <h1 className="mastery-title" id="mastery-title">Concept Mastered!</h1>
          <p className="mastery-subtitle">
            You've demonstrated mastery of Concept {conceptNumber}
          </p>
        </div>

        <div className="mastery-details">
          <div className="mastery-stat">
            <div className="stat-icon"></div>
            <div className="stat-content">
              <div className="stat-label">Final Score</div>
              <div className="stat-value">{Math.round(masteryScore * 100)}%</div>
            </div>
          </div>

          <div className="mastery-message">
            <p>
              Your recent performance shows you've truly understood this concept.
              Ready to move forward?
            </p>
          </div>
        </div>

        <button onClick={onContinue} className="mastery-continue-button">
          Continue to Next Concept →
        </button>
      </div>
    </div>
  )
}

export default ConceptMasteryModal
