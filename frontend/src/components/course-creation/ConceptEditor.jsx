import { useState } from 'react'
import CurriculumRoadmap from './CurriculumRoadmap'
import LearningOutcomeBuilder from './LearningOutcomeBuilder'
import AssessmentBuilder from './AssessmentBuilder'
import { api } from '../../api'
import './ConceptEditor.css'

function ConceptEditor({ courseData, onNext, onBack, onSaveDraft }) {
  // Flatten concepts from modules for editing
  const flattenConcepts = (modules) => {
    return modules?.flatMap(module =>
      module.concepts.map(concept => ({
        ...concept,
        moduleId: module.moduleId,
        moduleTitle: module.title
      }))
    ) || []
  }

  // Restructure flat concepts back into modules
  const reconstructModules = (flatConcepts) => {
    const modules = {}

    flatConcepts.forEach(concept => {
      const { moduleId, moduleTitle, ...conceptData } = concept

      if (!modules[moduleId]) {
        const originalModule = courseData.modules?.find(m => m.moduleId === moduleId)
        modules[moduleId] = {
          ...originalModule,
          concepts: []
        }
      }

      modules[moduleId].concepts.push(conceptData)
    })

    return Object.values(modules)
  }

  const [currentConceptIndex, setCurrentConceptIndex] = useState(0)
  const [concepts, setConcepts] = useState(flattenConcepts(courseData.modules))
  const [errors, setErrors] = useState({})
  const [showRoadmap, setShowRoadmap] = useState(false)
  const [generatingAssessments, setGeneratingAssessments] = useState(false)

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

  const handleGenerateAssessments = async () => {
    if (!currentConcept.title) {
      alert('Cannot generate assessments without a learning outcome')
      return
    }

    setGeneratingAssessments(true)
    try {
      const response = await api.generateAssessments(
        currentConcept.title,
        taxonomy,
        courseData.domain
      )

      if (response.success && response.assessments) {
        updateConcept('assessments', response.assessments)
      } else {
        alert('Failed to generate assessments. Please try again.')
      }
    } catch (error) {
      console.error('Error generating assessments:', error)
      alert(`Failed to generate assessments: ${error.message}`)
    } finally {
      setGeneratingAssessments(false)
    }
  }

  const validateConcept = () => {
    const newErrors = {}
    const content = currentConcept.teachingContent || ''
    const vocab = currentConcept.vocabulary || []
    const assessments = currentConcept.assessments || []

    if (content.length < 500) {
      newErrors.content = 'Teaching content must be at least 500 characters'
    }

    if (vocab.length < 5) {
      newErrors.vocab = 'At least 5 vocabulary terms required'
    }

    if (assessments.length < 2) {
      newErrors.assessments = 'At least 2 assessments required (recommended: mix of types)'
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
    const reconstructedModules = reconstructModules(concepts)
    onNext({ modules: reconstructedModules })
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

      {/* Display the learning objective for this concept */}
      <div className="concept-objective-display">
        <h4>Learning Objective</h4>
        <p className="objective-text">{currentConcept.title}</p>
        <p className="objective-hint">
          This concept covers the module learning outcome defined earlier. Create teaching content and assessments to help students achieve this objective.
        </p>
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

      {/* Assessments */}
      <div className="editor-section">
        <AssessmentBuilder
          assessments={currentConcept.assessments || []}
          onChange={(assessments) => updateConcept('assessments', assessments)}
          taxonomy={taxonomy}
          learningOutcome={currentConcept.title}
          onGenerateAssessments={handleGenerateAssessments}
          isGenerating={generatingAssessments}
        />
        {errors.assessments && <div className="validation-error">{errors.assessments}</div>}
      </div>

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
