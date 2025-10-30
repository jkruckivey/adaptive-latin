import { useState } from 'react'
import CurriculumRoadmap from './CurriculumRoadmap'
import LearningOutcomeBuilder from './LearningOutcomeBuilder'
import './ConceptEditor.css'

function ConceptEditor({ courseData, onNext, onBack, onSaveDraft }) {
  const [currentConceptIndex, setCurrentConceptIndex] = useState(0)
  const [concepts, setConcepts] = useState(courseData.concepts || [])
  const [errors, setErrors] = useState({})
  const [showRoadmap, setShowRoadmap] = useState(false)

  const currentConcept = concepts[currentConceptIndex] || {}

  // Get taxonomy from course data
  const taxonomy = courseData.taxonomy || 'blooms'
  const courseCLOs = courseData.courseLearningOutcomes || []

  const updateConcept = (field, value) => {
    const updated = concepts.map((c, i) =>
      i === currentConceptIndex ? { ...c, [field]: value } : c
    )
    setConcepts(updated)
  }

  const addVocabulary = () => {
    const vocab = currentConcept.vocabulary || []
    updateConcept('vocabulary', [...vocab, { term: '', definition: '' }])
  }

  const updateVocabulary = (index, field, value) => {
    const vocab = [...(currentConcept.vocabulary || [])]
    vocab[index] = { ...vocab[index], [field]: value }
    updateConcept('vocabulary', vocab)
  }

  const removeVocabulary = (index) => {
    const vocab = (currentConcept.vocabulary || []).filter((_, i) => i !== index)
    updateConcept('vocabulary', vocab)
  }

  const validateConcept = () => {
    const newErrors = {}
    const outcomes = (currentConcept.moduleLearningOutcomes || []).filter(o => o.trim())
    const content = currentConcept.teachingContent || ''
    const vocab = currentConcept.vocabulary || []

    if (outcomes.length < 3) {
      newErrors.outcomes = 'At least 3 module learning outcomes required'
    }

    if (content.length < 500) {
      newErrors.content = 'Teaching content must be at least 500 characters'
    }

    if (vocab.length < 5) {
      newErrors.vocab = 'At least 5 vocabulary terms required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleNextConcept = () => {
    if (validateConcept()) {
      if (currentConceptIndex < concepts.length - 1) {
        setCurrentConceptIndex(currentConceptIndex + 1)
        setErrors({})
      } else {
        // All concepts done, show roadmap before final review
        setShowRoadmap(true)
      }
    }
  }

  const handleRoadmapClose = () => {
    setShowRoadmap(false)
    onNext({ concepts })
  }

  const handlePrevConcept = () => {
    if (currentConceptIndex > 0) {
      setCurrentConceptIndex(currentConceptIndex - 1)
      setErrors({})
    }
  }

  return (
    <div className="wizard-form concept-editor">
      <div className="concept-editor-header">
        <h2>Build Content: {currentConcept.title}</h2>
        <p className="subtitle">
          Concept {currentConceptIndex + 1} of {concepts.length}
        </p>
      </div>

      {/* Concept navigation */}
      <div className="concept-navigation">
        {concepts.map((c, i) => (
          <button
            key={i}
            onClick={() => setCurrentConceptIndex(i)}
            className={`concept-nav-button ${i === currentConceptIndex ? 'active' : ''}`}
          >
            {i + 1}. {c.title}
          </button>
        ))}
      </div>

      {/* Display Course Learning Outcomes for reference */}
      {courseCLOs.length > 0 && (
        <div className="clo-reference">
          <h4>📚 Course Learning Outcomes (for alignment)</h4>
          <ul>
            {courseCLOs.filter(clo => clo.trim()).map((clo, i) => (
              <li key={i}>{clo}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Module Learning Outcomes */}
      <div className="editor-section">
        <LearningOutcomeBuilder
          outcomes={currentConcept.moduleLearningOutcomes || ['', '', '']}
          onChange={(outcomes) => updateConcept('moduleLearningOutcomes', outcomes)}
          taxonomy={taxonomy}
          domain={courseData.domain}
          courseTitle={`${currentConcept.title} (Module ${currentConceptIndex + 1})`}
          minOutcomes={3}
          maxOutcomes={7}
          label="Module Learning Outcomes (MLOs)"
          description="What will students be able to do after completing this module? These should support the course-level outcomes above."
        />
        {errors.outcomes && <div className="validation-error">{errors.outcomes}</div>}
      </div>

      {/* Teaching Content */}
      <div className="editor-section">
        <h3>Teaching Content</h3>
        <p className="section-description">
          Write the main teaching material. Include explanations, examples, and practice guidance. (Markdown supported)
        </p>

        <textarea
          value={currentConcept.teachingContent || ''}
          onChange={(e) => updateConcept('teachingContent', e.target.value)}
          placeholder="# Introduction&#10;&#10;Start with a clear explanation of the concept...&#10;&#10;## Examples&#10;&#10;Provide concrete examples..."
          rows={15}
          className="teaching-content-textarea"
        />

        <div className="char-count">
          {(currentConcept.teachingContent || '').length}/500+ characters (minimum 500)
        </div>

        {errors.content && <div className="validation-error">{errors.content}</div>}
      </div>

      {/* Vocabulary */}
      <div className="editor-section">
        <h3>Key Vocabulary</h3>
        <p className="section-description">
          Define important terms and concepts students need to know.
        </p>

        {(currentConcept.vocabulary || []).map((vocab, i) => (
          <div key={i} className="vocab-item">
            <input
              type="text"
              value={vocab.term}
              onChange={(e) => updateVocabulary(i, 'term', e.target.value)}
              placeholder="Term"
              className="vocab-term"
            />
            <input
              type="text"
              value={vocab.definition}
              onChange={(e) => updateVocabulary(i, 'definition', e.target.value)}
              placeholder="Definition"
              className="vocab-definition"
            />
            <button onClick={() => removeVocabulary(i)} className="remove-button">×</button>
          </div>
        ))}

        <button onClick={addVocabulary} className="add-button">
          + Add Vocabulary
        </button>

        {errors.vocab && <div className="validation-error">{errors.vocab}</div>}
      </div>

      {/* TODO: Assessments section - can be added in next iteration */}

      <div className="wizard-actions">
        <div className="left-actions">
          {currentConceptIndex === 0 ? (
            <button onClick={onBack} className="wizard-button secondary">
              ← Back to Planning
            </button>
          ) : (
            <button onClick={handlePrevConcept} className="wizard-button secondary">
              ← Previous Concept
            </button>
          )}
        </div>
        <div className="right-actions">
          <button onClick={onSaveDraft} className="wizard-button secondary">
            Save Draft
          </button>
          <button onClick={handleNextConcept} className="wizard-button primary">
            {currentConceptIndex < concepts.length - 1
              ? 'Next Concept →'
              : 'View Curriculum Roadmap →'
            }
          </button>
        </div>
      </div>

      {/* Curriculum Roadmap Modal */}
      {showRoadmap && (
        <div className="roadmap-modal-overlay">
          <div className="roadmap-modal">
            <CurriculumRoadmap
              courseData={{ ...courseData, concepts }}
              onClose={handleRoadmapClose}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default ConceptEditor
