import { useState } from 'react'
import './ConceptPlanner.css'

function ConceptPlanner({ courseData, onNext, onBack, onSaveDraft }) {
  const [concepts, setConcepts] = useState(
    courseData.concepts && courseData.concepts.length > 0
      ? courseData.concepts
      : [{ id: 1, title: '', prerequisites: [] }]
  )
  const [errors, setErrors] = useState({})

  const addConcept = () => {
    const newId = Math.max(...concepts.map(c => c.id), 0) + 1
    setConcepts([...concepts, { id: newId, title: '', prerequisites: [] }])
  }

  const removeConcept = (id) => {
    if (concepts.length === 1) {
      alert('You must have at least one concept')
      return
    }

    setConcepts(concepts.filter(c => c.id !== id))
  }

  const updateConcept = (id, field, value) => {
    setConcepts(concepts.map(c =>
      c.id === id ? { ...c, [field]: value } : c
    ))
    // Clear error
    if (errors[`concept-${id}`]) {
      setErrors(prev => ({ ...prev, [`concept-${id}`]: null }))
    }
  }

  const togglePrerequisite = (conceptId, prereqId) => {
    setConcepts(concepts.map(c => {
      if (c.id === conceptId) {
        const prerequisites = c.prerequisites.includes(prereqId)
          ? c.prerequisites.filter(id => id !== prereqId)
          : [...c.prerequisites, prereqId]
        return { ...c, prerequisites }
      }
      return c
    }))
  }

  const validate = () => {
    const newErrors = {}

    concepts.forEach((concept, index) => {
      if (!concept.title.trim()) {
        newErrors[`concept-${concept.id}`] = `Concept ${index + 1} title is required`
      } else if (concept.title.length < 5) {
        newErrors[`concept-${concept.id}`] = `Concept ${index + 1} title must be at least 5 characters`
      }
    })

    if (concepts.length < 2) {
      newErrors.general = 'You must create at least 2 concepts'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleNext = () => {
    if (validate()) {
      // Initialize concept data for each concept
      const initializedConcepts = concepts.map((concept, index) => ({
        ...concept,
        conceptId: `concept-${String(index + 1).padStart(3, '0')}`,
        learningObjectives: [],
        teachingContent: '',
        vocabulary: [],
        assessments: []
      }))

      onNext({ concepts: initializedConcepts })
    }
  }

  return (
    <div className="wizard-form concept-planner">
      <h2>Plan Your Concepts</h2>
      <p className="subtitle">
        Break your course into logical concepts or units. Each concept should cover a specific topic or skill.
      </p>

      {errors.general && (
        <div className="alert alert-error">{errors.general}</div>
      )}

      <div className="concepts-list">
        {concepts.map((concept, index) => (
          <div key={concept.id} className="concept-card">
            <div className="concept-header">
              <h3>Concept {index + 1}</h3>
              {concepts.length > 1 && (
                <button
                  onClick={() => removeConcept(concept.id)}
                  className="remove-button"
                  title="Remove concept"
                >
                  ×
                </button>
              )}
            </div>

            <div className="form-group">
              <label>Concept Title</label>
              <input
                type="text"
                value={concept.title}
                onChange={(e) => updateConcept(concept.id, 'title', e.target.value)}
                placeholder="e.g., Introduction to Variables, First Declension Nouns"
                maxLength={100}
              />
              {errors[`concept-${concept.id}`] && (
                <div className="validation-error">{errors[`concept-${concept.id}`]}</div>
              )}
            </div>

            {index > 0 && (
              <div className="form-group">
                <label>Prerequisites</label>
                <div className="prerequisite-options">
                  {concepts.slice(0, index).map(prereqConcept => (
                    <label key={prereqConcept.id} className="checkbox-option">
                      <input
                        type="checkbox"
                        checked={concept.prerequisites.includes(prereqConcept.id)}
                        onChange={() => togglePrerequisite(concept.id, prereqConcept.id)}
                      />
                      <span>
                        Concept {concepts.findIndex(c => c.id === prereqConcept.id) + 1}: {prereqConcept.title || '(Untitled)'}
                      </span>
                    </label>
                  ))}
                </div>
                {concept.prerequisites.length === 0 && (
                  <div className="hint">No prerequisites - this concept can be learned independently</div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={addConcept}
        className="add-concept-button"
      >
        + Add Another Concept
      </button>

      <div className="planning-tips">
        <h4>💡 Tips for Planning Concepts</h4>
        <ul>
          <li>Start with foundational concepts and build progressively</li>
          <li>Each concept should take 30-90 minutes to complete</li>
          <li>Aim for 3-7 concepts per course</li>
          <li>Use clear, descriptive titles that tell learners what they'll learn</li>
        </ul>
      </div>

      <div className="wizard-actions">
        <div className="left-actions">
          <button
            onClick={onBack}
            className="wizard-button secondary"
          >
            ← Back
          </button>
        </div>
        <div className="right-actions">
          <button
            onClick={onSaveDraft}
            className="wizard-button secondary"
          >
            Save Draft
          </button>
          <button
            onClick={handleNext}
            className="wizard-button primary"
          >
            Next: Build Content →
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConceptPlanner
