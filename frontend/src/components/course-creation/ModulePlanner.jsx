import { useState } from 'react'
import { api } from '../../api'
import LearningOutcomeBuilder from './LearningOutcomeBuilder'
import './ConceptPlanner.css'

// Helper to safely get string from outcome (handles both string and object formats)
const getOutcomeText = (o) => {
  if (typeof o === 'string') return o
  if (o && typeof o === 'object') return o.outcome || o.text || o.description || ''
  return ''
}

function ModulePlanner({ courseData, onNext, onBack, onSaveDraft }) {
  const [modules, setModules] = useState(
    courseData.modules && courseData.modules.length > 0
      ? courseData.modules
      : [{ id: 1, title: '', moduleLearningOutcomes: ['', ''] }]
  )
  const [expandedModules, setExpandedModules] = useState([1])
  const [errors, setErrors] = useState({})
  const [generatingForModule, setGeneratingForModule] = useState(null)

  const addModule = () => {
    const newId = Math.max(...modules.map(m => m.id), 0) + 1
    setModules([...modules, {
      id: newId,
      title: '',
      moduleLearningOutcomes: ['', '']
    }])
    setExpandedModules([...expandedModules, newId])
  }

  const removeModule = (id) => {
    if (modules.length === 1) {
      alert('You must have at least one module')
      return
    }
    setModules(modules.filter(m => m.id !== id))
    setExpandedModules(expandedModules.filter(mid => mid !== id))
  }

  const updateModule = (id, field, value) => {
    setModules(modules.map(m =>
      m.id === id ? { ...m, [field]: value } : m
    ))
    // Clear error
    if (errors[`module-${id}`]) {
      setErrors(prev => ({ ...prev, [`module-${id}`]: null }))
    }
  }

  const toggleModule = (id) => {
    setExpandedModules(prev =>
      prev.includes(id) ? prev.filter(mid => mid !== id) : [...prev, id]
    )
  }

  const handleGenerateMLOs = async (moduleId) => {
    const module = modules.find(m => m.id === moduleId)
    if (!module.title || !courseData.title) {
      alert('Please enter a module title and ensure course title is set')
      return
    }

    if (!courseData.courseLearningOutcomes || courseData.courseLearningOutcomes.filter(o => getOutcomeText(o).trim()).length === 0) {
      alert('Please define Course Learning Outcomes first (go back to Course Setup)')
      return
    }

    setGeneratingForModule(moduleId)
    try {
      const response = await api.generateModuleLearningOutcomes(
        module.title,
        courseData.title,
        courseData.courseLearningOutcomes.filter(o => getOutcomeText(o).trim()).map(o => getOutcomeText(o)),
        courseData.domain,
        courseData.taxonomy
      )

      if (response.success && response.outcomes) {
        updateModule(moduleId, 'moduleLearningOutcomes', response.outcomes)
      }
    } catch (error) {
      console.error('Error generating module outcomes:', error)
      alert(`Failed to generate module outcomes: ${error.message}`)
    } finally {
      setGeneratingForModule(null)
    }
  }

  const validate = () => {
    const newErrors = {}

    modules.forEach((module, moduleIndex) => {
      if (!module.title.trim()) {
        newErrors[`module-${module.id}`] = `Module ${moduleIndex + 1} title is required`
      } else if (module.title.length < 5) {
        newErrors[`module-${module.id}`] = `Module ${moduleIndex + 1} title must be at least 5 characters`
      }

      // Validate module learning outcomes (each becomes a concept)
      const validMLOs = module.moduleLearningOutcomes.filter(o => getOutcomeText(o).trim())
      if (validMLOs.length < 2) {
        newErrors[`module-${module.id}-mlos`] = `Module ${moduleIndex + 1} must have at least 2 learning outcomes`
      }
    })

    if (modules.length < 1) {
      newErrors.general = 'You must create at least 1 module'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleNext = () => {
    if (validate()) {
      // Convert each MLO to a concept automatically
      const initializedModules = modules.map((module, moduleIndex) => ({
        ...module,
        moduleId: `module-${String(moduleIndex + 1).padStart(3, '0')}`,
        concepts: module.moduleLearningOutcomes
          .filter(mlo => getOutcomeText(mlo).trim())
          .map((mlo, conceptIndex) => ({
            id: conceptIndex + 1,
            conceptId: `concept-${String(conceptIndex + 1).padStart(3, '0')}`,
            title: getOutcomeText(mlo), // Use the MLO as the concept title
            learningObjectives: [getOutcomeText(mlo)], // MLO becomes the primary learning objective
            prerequisites: [],
            teachingContent: '',
            vocabulary: [],
            assessments: []
          }))
      }))

      onNext({ modules: initializedModules })
    }
  }

  return (
    <div className="wizard-form concept-planner">
      <h2>Plan Your Modules</h2>
      <p className="subtitle">
        Organize your course into modules. Each module learning outcome will become a concept with its own content and assessments.
      </p>

      {errors.general && (
        <div className="alert alert-error">{errors.general}</div>
      )}

      <div className="concepts-list">
        {modules.map((module, moduleIndex) => (
          <div key={module.id} className="module-card">
            <div className="module-header-section">
              <div className="module-title-row">
                <button
                  onClick={() => toggleModule(module.id)}
                  className="toggle-button"
                  type="button"
                >
                  {expandedModules.includes(module.id) ? '▼' : '▶'}
                </button>
                <h3>Module {moduleIndex + 1}</h3>
                {modules.length > 1 && (
                  <button
                    onClick={() => removeModule(module.id)}
                    className="remove-button"
                    type="button"
                  >
                    Remove Module
                  </button>
                )}
              </div>

              <div className="form-group">
                <label>Module Title <span className="required">*</span></label>
                <input
                  type="text"
                  value={module.title}
                  onChange={(e) => updateModule(module.id, 'title', e.target.value)}
                  placeholder="e.g., Functions and Modeling, Statistical Analysis"
                  maxLength={100}
                />
                {errors[`module-${module.id}`] && (
                  <div className="validation-error">{errors[`module-${module.id}`]}</div>
                )}
              </div>

              {expandedModules.includes(module.id) && (
                <div className="form-group">
                  <LearningOutcomeBuilder
                    outcomes={module.moduleLearningOutcomes}
                    onChange={(outcomes) => updateModule(module.id, 'moduleLearningOutcomes', outcomes)}
                    taxonomy={courseData.taxonomy || 'blooms'}
                    domain={courseData.domain}
                    courseTitle={module.title}
                    minOutcomes={2}
                    maxOutcomes={5}
                    label="Module Learning Outcomes (MLOs)"
                    description="Module-level outcomes are more specific than course outcomes. Each MLO will become a concept with its own teaching content and assessments."
                    onGenerateSuggestions={() => handleGenerateMLOs(module.id)}
                    isGenerating={generatingForModule === module.id}
                  />
                  {errors[`module-${module.id}-mlos`] && (
                    <div className="validation-error">{errors[`module-${module.id}-mlos`]}</div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <button onClick={addModule} className="add-button" type="button">
        + Add Module
      </button>

      <div className="wizard-actions">
        <div className="left-actions">
          <button onClick={onBack} className="wizard-button secondary">
            ← Back
          </button>
        </div>
        <div className="right-actions">
          <button onClick={onSaveDraft} className="wizard-button secondary">
            Save Draft
          </button>
          <button onClick={handleNext} className="wizard-button primary">
            Next: Resource Library →
          </button>
        </div>
      </div>
    </div>
  )
}

export default ModulePlanner
