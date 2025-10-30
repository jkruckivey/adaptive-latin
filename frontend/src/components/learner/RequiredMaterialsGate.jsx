import { useState, useEffect } from 'react'
import ComprehensionQuiz from './ComprehensionQuiz'
import DiscussionPrompt from './DiscussionPrompt'
import SelfAttestation from './SelfAttestation'
import './RequiredMaterialsGate.css'

function RequiredMaterialsGate({
  courseId,
  moduleId,
  requiredMaterials,
  onComplete,
  learnerId
}) {
  const [completedMaterials, setCompletedMaterials] = useState(new Set())
  const [currentMaterial, setCurrentMaterial] = useState(null)
  const [showMaterialViewer, setShowMaterialViewer] = useState(false)

  // Load completion status from localStorage
  useEffect(() => {
    const storageKey = `completions_${learnerId}_${courseId}_${moduleId}`
    const stored = localStorage.getItem(storageKey)
    if (stored) {
      setCompletedMaterials(new Set(JSON.parse(stored)))
    }
  }, [learnerId, courseId, moduleId])

  // Save completion status to localStorage
  const saveCompletion = (materialId) => {
    const updated = new Set([...completedMaterials, materialId])
    setCompletedMaterials(updated)

    const storageKey = `completions_${learnerId}_${courseId}_${moduleId}`
    localStorage.setItem(storageKey, JSON.stringify([...updated]))
  }

  const handleMaterialComplete = (materialId) => {
    saveCompletion(materialId)
    setCurrentMaterial(null)
    setShowMaterialViewer(false)
  }

  const openMaterial = (material) => {
    setCurrentMaterial(material)
    setShowMaterialViewer(true)
  }

  const allComplete = requiredMaterials.every(m => completedMaterials.has(m.id))

  const handleProceed = () => {
    if (allComplete) {
      onComplete()
    }
  }

  const getMaterialIcon = (type) => {
    switch (type) {
      case 'pdf': return '📄'
      case 'video': return '🎥'
      case 'image': return '🖼️'
      default: return '🌐'
    }
  }

  const getVerificationLabel = (method) => {
    switch (method) {
      case 'comprehension-quiz': return 'Complete Quiz'
      case 'discussion-prompt': return 'Respond to Prompt'
      case 'self-attestation': return 'Confirm Reading'
      default: return 'View Material'
    }
  }

  if (showMaterialViewer && currentMaterial) {
    return (
      <div className="material-viewer-container">
        <div className="material-viewer-header">
          <h2>{currentMaterial.title}</h2>
          <button
            onClick={() => setShowMaterialViewer(false)}
            className="close-viewer-button"
          >
            ← Back to Materials
          </button>
        </div>

        <div className="material-content">
          {/* Material Display */}
          <div className="material-display">
            <div className="material-link-section">
              <p>Please review this material before completing the verification:</p>
              <a
                href={currentMaterial.url}
                target="_blank"
                rel="noopener noreferrer"
                className="material-link"
              >
                {getMaterialIcon(currentMaterial.type)} Open {currentMaterial.type.toUpperCase()}
              </a>
              {currentMaterial.description && (
                <p className="material-description">{currentMaterial.description}</p>
              )}
            </div>

            {/* Verification Interface */}
            <div className="verification-interface">
              <h3>Verification Required</h3>

              {currentMaterial.verificationMethod === 'comprehension-quiz' && (
                <ComprehensionQuiz
                  questions={currentMaterial.verificationData?.comprehensionQuestions || []}
                  onComplete={() => handleMaterialComplete(currentMaterial.id)}
                  materialTitle={currentMaterial.title}
                />
              )}

              {currentMaterial.verificationMethod === 'discussion-prompt' && (
                <DiscussionPrompt
                  prompt={currentMaterial.verificationData?.discussionPrompt || ''}
                  onComplete={() => handleMaterialComplete(currentMaterial.id)}
                  materialTitle={currentMaterial.title}
                />
              )}

              {currentMaterial.verificationMethod === 'self-attestation' && (
                <SelfAttestation
                  attestationText={currentMaterial.verificationData?.attestationText || 'I have read and understood this material'}
                  onComplete={() => handleMaterialComplete(currentMaterial.id)}
                  materialTitle={currentMaterial.title}
                />
              )}

              {currentMaterial.verificationMethod === 'none' && (
                <div className="no-verification">
                  <p>No verification required for this material.</p>
                  <button
                    onClick={() => handleMaterialComplete(currentMaterial.id)}
                    className="mark-complete-button"
                  >
                    Mark as Complete
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="required-materials-gate">
      <div className="gate-header">
        <h2>⭐ Required Materials</h2>
        <p className="gate-subtitle">
          Complete these materials before accessing this module
        </p>
      </div>

      <div className="progress-indicator">
        <div className="progress-text">
          {completedMaterials.size} of {requiredMaterials.length} completed
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${(completedMaterials.size / requiredMaterials.length) * 100}%` }}
          />
        </div>
      </div>

      <div className="materials-list">
        {requiredMaterials.map((material) => {
          const isComplete = completedMaterials.has(material.id)

          return (
            <div
              key={material.id}
              className={`material-card ${isComplete ? 'completed' : 'incomplete'}`}
            >
              <div className="material-card-header">
                <div className="material-icon-title">
                  <span className="material-icon-large">
                    {getMaterialIcon(material.type)}
                  </span>
                  <div className="material-info">
                    <h3>{material.title}</h3>
                    {material.description && (
                      <p className="material-desc">{material.description}</p>
                    )}
                  </div>
                </div>
                {isComplete && (
                  <span className="completion-badge">✓ Complete</span>
                )}
              </div>

              <div className="material-card-actions">
                {!isComplete ? (
                  <button
                    onClick={() => openMaterial(material)}
                    className="start-material-button"
                  >
                    {getVerificationLabel(material.verificationMethod)} →
                  </button>
                ) : (
                  <button
                    onClick={() => openMaterial(material)}
                    className="review-material-button"
                  >
                    Review Material
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="gate-footer">
        {!allComplete ? (
          <div className="incomplete-notice">
            <p>⚠️ Complete all required materials to proceed</p>
          </div>
        ) : (
          <div className="complete-notice">
            <p>✓ All materials completed! You can now access this module.</p>
            <button
              onClick={handleProceed}
              className="proceed-button"
            >
              Proceed to Module →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default RequiredMaterialsGate
