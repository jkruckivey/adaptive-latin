import { useState, useEffect } from 'react'
import { api } from '../../api'
import ActionVerbHelper from './ActionVerbHelper'
import { checkOutcomeQuality, domainExamples } from '../../utils/taxonomyData'
import './LearningOutcomeBuilder.css'

function LearningOutcomeBuilder({
  outcomes,
  onChange,
  taxonomy,
  domain,
  courseTitle,
  minOutcomes = 3,
  maxOutcomes = 5,
  label = "Course Learning Outcomes",
  description = "What will students be able to do after completing this course?",
  onGenerateSuggestions,
  isGenerating = false,
  courseFormat = "cohort",
  moduleNumber = 1,
  moduleTitle = ""
}) {
  const [showVerbHelper, setShowVerbHelper] = useState(false)
  const [currentEditIndex, setCurrentEditIndex] = useState(null)
  const [showExamples, setShowExamples] = useState(false)
  const [qualityFeedback, setQualityFeedback] = useState({})
  const [simulationHtml, setSimulationHtml] = useState(null)
  const [generatingSimulation, setGeneratingSimulation] = useState(false)
  const [selectedSimulationType, setSelectedSimulationType] = useState('learning-outcomes-map')

  // Update quality feedback when outcomes change
  useEffect(() => {
    const feedback = {}
    outcomes.forEach((outcome, index) => {
      if (outcome.trim()) {
        feedback[index] = checkOutcomeQuality(outcome)
      }
    })
    setQualityFeedback(feedback)
  }, [outcomes])

  const addOutcome = () => {
    if (outcomes.length < maxOutcomes) {
      onChange([...outcomes, ''])
    }
  }

  const updateOutcome = (index, value) => {
    const updated = [...outcomes]
    updated[index] = value
    onChange(updated)
  }

  const removeOutcome = (index) => {
    const updated = outcomes.filter((_, i) => i !== index)
    onChange(updated)
  }

  const handleVerbSelect = (verb) => {
    if (currentEditIndex !== null) {
      const current = outcomes[currentEditIndex]
      // Insert verb at cursor or append
      const newValue = current ? `${current.trim()} ${verb.toLowerCase()}` : `Students will be able to ${verb.toLowerCase()}`
      updateOutcome(currentEditIndex, newValue)
    }
  }

  const openVerbHelper = (index) => {
    setCurrentEditIndex(index)
    setShowVerbHelper(true)
  }

  const getExamples = () => {
    if (!domain || !domainExamples[domain]) return []
    return taxonomy === 'blooms' ? domainExamples[domain].blooms :
           taxonomy === 'finks' ? domainExamples[domain].finks :
           [...domainExamples[domain].blooms, ...domainExamples[domain].finks]
  }

  const examples = getExamples()

  const useExample = (example) => {
    const emptyIndex = outcomes.findIndex(o => !o.trim())
    if (emptyIndex !== -1) {
      updateOutcome(emptyIndex, example)
    } else if (outcomes.length < maxOutcomes) {
      onChange([...outcomes, example])
    }
    setShowExamples(false)
  }

  const handleGenerateSimulation = async () => {
    const validOutcomes = outcomes.filter(o => o.trim())
    if (validOutcomes.length === 0) {
      alert('Please add at least one learning outcome first')
      return
    }

    setGeneratingSimulation(true)
    try {
      let simulationData

      if (selectedSimulationType === 'learning-outcomes-map') {
        simulationData = {
          module_number: moduleNumber,
          module_title: moduleTitle || courseTitle || 'Preview Module',
          module_outcomes: validOutcomes.map((text, i) => ({
            text,
            clos: ['CLO 1'] // Default connection for preview
          })),
          course_outcomes: [
            { code: 'CLO 1', text: 'Course-level outcome (example)' }
          ]
        }
      } else if (selectedSimulationType === 'pre-assessment-quiz') {
        simulationData = {
          module_title: moduleTitle || courseTitle || 'Preview Module',
          questions: validOutcomes.slice(0, 3).map(outcome => ({
            question: `How familiar are you with: ${outcome}?`,
            options: ['Not familiar', 'Somewhat familiar', 'Very familiar', 'Expert level'],
            info: 'This helps gauge your starting knowledge level'
          }))
        }
      } else if (selectedSimulationType === 'concept-preview') {
        simulationData = {
          module_title: moduleTitle || courseTitle || 'Preview Module',
          key_points: validOutcomes.slice(0, 4).map(o => o.replace(/^Students will be able to /, '')),
          learning_objectives: validOutcomes
        }
      }

      const response = await api.generateSimulation(
        selectedSimulationType,
        courseFormat,
        simulationData
      )

      if (response.success) {
        setSimulationHtml(response.html)
      }
    } catch (error) {
      console.error('Error generating simulation:', error)
      alert(`Failed to generate simulation: ${error.message}`)
    } finally {
      setGeneratingSimulation(false)
    }
  }

  return (
    <div className="learning-outcome-builder">
      <div className="builder-header">
        <h3>{label}</h3>
        <p className="builder-description">{description}</p>
      </div>

      <div className="builder-actions">
        {onGenerateSuggestions && (
          <button
            onClick={onGenerateSuggestions}
            className="action-button ai-button"
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating...' : 'Generate Suggestions with AI'}
          </button>
        )}
        <div className="simulation-controls">
          <select
            value={selectedSimulationType}
            onChange={(e) => setSelectedSimulationType(e.target.value)}
            className="simulation-type-select"
            disabled={generatingSimulation}
          >
            <option value="learning-outcomes-map">Learning Outcomes Map</option>
            <option value="pre-assessment-quiz">Pre-Assessment Quiz</option>
            <option value="concept-preview">Concept Preview</option>
          </select>
          <button
            onClick={handleGenerateSimulation}
            className="action-button secondary"
            disabled={generatingSimulation || outcomes.filter(o => o.trim()).length === 0}
            title={
              generatingSimulation ? 'Generating simulation...' :
              outcomes.filter(o => o.trim()).length === 0 ? 'Add at least one learning outcome to preview a simulation' :
              'Generate an interactive preview of your learning outcomes'
            }
          >
            {generatingSimulation ? 'Generating...' : 'Preview Simulation'}
          </button>
        </div>
        {examples.length > 0 && (
          <button
            onClick={() => setShowExamples(!showExamples)}
            className="action-button secondary"
          >
            {showExamples ? 'Hide' : 'Show'} Examples
          </button>
        )}
      </div>

      {showExamples && examples.length > 0 && (
        <div className="examples-panel">
          <h4>Example {label} for {domain}</h4>
          <div className="examples-list">
            {examples.map((example, i) => (
              <div key={i} className="example-item">
                <p>{example}</p>
                <button
                  onClick={() => useExample(example)}
                  className="use-example-button"
                >
                  Use This
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {simulationHtml && (
        <div className="simulation-preview-panel">
          <div className="preview-header">
            <h4>Interactive Simulation Preview</h4>
            <button
              onClick={() => setSimulationHtml(null)}
              className="close-preview-button"
            >
              Close Preview
            </button>
          </div>
          <div
            className="simulation-preview-content"
            dangerouslySetInnerHTML={{ __html: simulationHtml }}
          />
        </div>
      )}

      <div className="outcomes-list">
        {outcomes.map((outcome, index) => (
          <div key={index} className="outcome-item">
            <div className="outcome-header">
              <label>Learning Outcome {index + 1}</label>
              {outcomes.length > minOutcomes && (
                <button
                  onClick={() => removeOutcome(index)}
                  className="remove-button"
                >
                  Remove
                </button>
              )}
            </div>

            <div className="outcome-input-group">
              <textarea
                value={outcome}
                onChange={(e) => updateOutcome(index, e.target.value)}
                placeholder="Students will be able to..."
                rows={2}
                className="outcome-input"
              />
              <button
                onClick={() => openVerbHelper(index)}
                className="verb-helper-button"
                title="Open action verb helper"
              >
                Verbs
              </button>
            </div>

            {/* Quality Feedback */}
            {qualityFeedback[index] && qualityFeedback[index].length > 0 && (
              <div className="quality-feedback">
                {qualityFeedback[index].map((feedback, i) => (
                  <div key={i} className={`feedback-item feedback-${feedback.type}`}>
                    <span className="feedback-icon">
                      {feedback.type === 'success' ? '✓' :
                       feedback.type === 'warning' ? '⚠' : 'ℹ'}
                    </span>
                    <span className="feedback-message">{feedback.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {outcomes.length < maxOutcomes && (
        <button onClick={addOutcome} className="add-outcome-button">
          + Add Another Outcome ({outcomes.length}/{maxOutcomes})
        </button>
      )}

      <div className="builder-hints">
        <p><strong>Writing Tips:</strong></p>
        <ul>
          <li>Start with "Students will be able to..." or similar learner-centered language</li>
          <li>Use measurable action verbs from {taxonomy === 'blooms' ? "Bloom's" : taxonomy === 'finks' ? "Fink's" : "Bloom's or Fink's"} taxonomy</li>
          <li>Avoid vague verbs like "understand," "know," or "learn"</li>
          <li>Be specific about what students will do and in what context</li>
          <li>Course outcomes should be broad; module outcomes will be more specific</li>
        </ul>
      </div>

      {/* Verb Helper Modal */}
      {showVerbHelper && (
        <div className="modal-overlay" onClick={() => setShowVerbHelper(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <ActionVerbHelper
              taxonomy={taxonomy}
              onSelectVerb={handleVerbSelect}
              onClose={() => setShowVerbHelper(false)}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default LearningOutcomeBuilder
