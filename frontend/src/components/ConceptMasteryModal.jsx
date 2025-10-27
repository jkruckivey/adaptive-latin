import './ConceptMasteryModal.css'

function ConceptMasteryModal({ conceptId, masteryScore, onContinue }) {
  const conceptNumber = conceptId?.split('-')[1] || '001'

  return (
    <div className="mastery-modal-overlay">
      <div className="mastery-modal">
        <div className="mastery-celebration">
          <div className="mastery-icon">🎉</div>
          <h1 className="mastery-title">Concept Mastered!</h1>
          <p className="mastery-subtitle">
            You've demonstrated mastery of Concept {conceptNumber}
          </p>
        </div>

        <div className="mastery-details">
          <div className="mastery-stat">
            <div className="stat-icon">⭐</div>
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
