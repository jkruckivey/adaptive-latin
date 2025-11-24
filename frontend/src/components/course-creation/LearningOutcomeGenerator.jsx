import { useState } from 'react'
import { api } from '../../api'
import './LearningOutcomeGenerator.css'

function LearningOutcomeGenerator({
  description,
  taxonomy,
  level,
  existingOutcomes = [],
  onAccept,
  onCancel
}) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedOutcomes, setGeneratedOutcomes] = useState([])
  const [editedOutcomes, setEditedOutcomes] = useState([])
  const [error, setError] = useState(null)
  const [showResults, setShowResults] = useState(false)

  const handleGenerate = async () => {
    if (!description || description.trim().length < 10) {
      setError('Please provide a description of at least 10 characters')
      return
    }

    setIsGenerating(true)
    setError(null)

    try {
      const result = await api.generateLearningOutcomes(
        description,
        taxonomy,
        level,
        5, // Generate 5 outcomes by default
        existingOutcomes.length > 0 ? existingOutcomes : null
      )

      if (result.success && result.outcomes) {
        setGeneratedOutcomes(result.outcomes)
        // Extract text from outcome objects (backend returns {text, action_verb, taxonomy_level, domain})
        setEditedOutcomes(result.outcomes.map(o => typeof o === 'string' ? o : o.text))
        setShowResults(true)
      } else {
        setError('No outcomes were generated. Please try again.')
      }
    } catch (err) {
      console.error('Generation error:', err)
      setError(err.message || 'Failed to generate outcomes. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleEdit = (index, value) => {
    const updated = [...editedOutcomes]
    updated[index] = value
    setEditedOutcomes(updated)
  }

  const handleRemove = (index) => {
    const updated = editedOutcomes.filter((_, i) => i !== index)
    setEditedOutcomes(updated)
  }

  const handleAccept = () => {
    const nonEmptyOutcomes = editedOutcomes.filter(o => o.trim().length > 0)
    if (nonEmptyOutcomes.length > 0) {
      onAccept(nonEmptyOutcomes)
    }
  }

  const handleRegenerate = () => {
    setShowResults(false)
    setGeneratedOutcomes([])
    setEditedOutcomes([])
    handleGenerate()
  }

  const getLevelLabel = () => {
    switch (level) {
      case 'course': return 'Course Learning Outcomes (CLOs)'
      case 'module': return 'Module Learning Outcomes (MLOs)'
      case 'concept': return 'Learning Objectives'
      default: return 'Learning Outcomes'
    }
  }

  const getTaxonomyLabel = () => {
    return taxonomy === 'blooms' ? "Bloom's Taxonomy" : "Fink's Taxonomy"
  }

  return (
    <div className="learning-outcome-generator">
      <div className="generator-header">
        <h3>AI Learning Outcome Generator</h3>
        <p className="generator-subtitle">
          Generate {getLevelLabel()} using {getTaxonomyLabel()}
        </p>
      </div>

      {!showResults ? (
        <div className="generator-initial">
          <div className="generator-info">
            <div className="info-item">
              <strong>Description:</strong>
              <p className="description-preview">{description || 'No description provided'}</p>
            </div>
            {existingOutcomes.length > 0 && (
              <div className="info-item">
                <strong>Existing Outcomes:</strong>
                <p className="existing-count">{existingOutcomes.length} outcome(s) already defined</p>
              </div>
            )}
          </div>

          {error && <div className="generator-error">{error}</div>}

          <div className="generator-actions">
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !description}
              className="generate-button primary"
            >
              {isGenerating ? 'Generating...' : '✨ Generate Outcomes'}
            </button>
            <button onClick={onCancel} className="cancel-button secondary">
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="generator-results">
          <div className="results-header">
            <h4>Generated Outcomes</h4>
            <p>Review and edit the generated outcomes below. You can modify, remove, or regenerate them.</p>
          </div>

          <div className="outcomes-list">
            {editedOutcomes.map((outcome, index) => (
              <div key={index} className="outcome-item">
                <div className="outcome-number">{index + 1}</div>
                <textarea
                  value={outcome}
                  onChange={(e) => handleEdit(index, e.target.value)}
                  rows={2}
                  className="outcome-input"
                />
                <button
                  onClick={() => handleRemove(index)}
                  className="remove-outcome-button"
                  title="Remove this outcome"
                  aria-label={`Remove outcome ${index + 1}`}
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          {editedOutcomes.length === 0 && (
            <div className="empty-outcomes">
              <p>All outcomes removed. Generate new ones or cancel.</p>
            </div>
          )}

          {error && <div className="generator-error">{error}</div>}

          <div className="generator-actions">
            <div className="left-actions">
              <button
                onClick={handleRegenerate}
                disabled={isGenerating}
                className="regenerate-button secondary"
              >
                🔄 Regenerate
              </button>
            </div>
            <div className="right-actions">
              <button onClick={onCancel} className="cancel-button secondary">
                Cancel
              </button>
              <button
                onClick={handleAccept}
                disabled={editedOutcomes.length === 0}
                className="accept-button primary"
              >
                Accept Outcomes →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default LearningOutcomeGenerator
