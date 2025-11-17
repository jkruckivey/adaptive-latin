import { useState } from 'react'
import { api } from '../../api'
import LearningOutcomeBuilder from './LearningOutcomeBuilder'
import './ConceptPlanner.css'

function ModulePlanner({ courseData, onNext, onBack, onSaveDraft }) {
  const [modules, setModules] = useState(
    courseData.modules && courseData.modules.length > 0
      ? courseData.modules
      : [{ id: 1, title: '', moduleLearningOutcomes: ['', ''], concepts: [{ id: 1, title: '', prerequisites: [], learningObjectives: ['', '', ''] }] }]
  )
  const [expandedModules, setExpandedModules] = useState([1])
  const [errors, setErrors] = useState({})
  const [generatingForModule, setGeneratingForModule] = useState(null)
  const [generatingForConcept, setGeneratingForConcept] = useState(null)

  const addModule = () => {
    const newId = Math.max(...modules.map(m => m.id), 0) + 1
    setModules([...modules, {
      id: newId,
      title: '',
      moduleLearningOutcomes: ['', ''],
      concepts: [{ id: 1, title: '', prerequisites: [], learningObjectives: ['', '', ''] }]
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

  const addConcept = (moduleId) => {
    setModules(modules.map(m => {
      if (m.id === moduleId) {
        const newConceptId = Math.max(...m.concepts.map(c => c.id), 0) + 1
        return {
          ...m,
          concepts: [...m.concepts, { id: newConceptId, title: '', prerequisites: [], learningObjectives: ['', '', ''] }]
        }
      }
      return m
    }))
  }

  const removeConcept = (moduleId, conceptId) => {
    setModules(modules.map(m => {
      if (m.id === moduleId) {
        if (m.concepts.length === 1) {
          alert('Each module must have at least one concept')
          return m
        }
        return {
          ...m,
          concepts: m.concepts.filter(c => c.id !== conceptId)
        }
      }
      return m
    }))
  }

  const updateConcept = (moduleId, conceptId, field, value) => {
    setModules(modules.map(m => {
      if (m.id === moduleId) {
        return {
          ...m,
          concepts: m.concepts.map(c =>
            c.id === conceptId ? { ...c, [field]: value } : c
          )
        }
      }
      return m
    }))
    // Clear error
    if (errors[`concept-${moduleId}-${conceptId}`]) {
      setErrors(prev => ({ ...prev, [`concept-${moduleId}-${conceptId}`]: null }))
    }
  }

  const handleGenerateMLOs = async (moduleId) => {
    const module = modules.find(m => m.id === moduleId)
    if (!module.title || !courseData.title) {
      alert('Please enter a module title and ensure course title is set')
      return
    }

    if (!courseData.courseLearningOutcomes || courseData.courseLearningOutcomes.filter(o => o.trim()).length === 0) {
      alert('Please define Course Learning Outcomes first (go back to Course Setup)')
      return
    }

    setGeneratingForModule(moduleId)
    try {
      const response = await api.generateModuleLearningOutcomes(
        module.title,
        courseData.title,
        courseData.courseLearningOutcomes.filter(o => o.trim()),
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

  const handleGenerateConceptObjectives = async (moduleId, conceptId) => {
    const module = modules.find(m => m.id === moduleId)
    const concept = module.concepts.find(c => c.id === conceptId)

    if (!concept.title || !module.title || !courseData.title) {
      alert('Please enter a concept title, module title, and ensure course title is set')
      return
    }

    if (!module.moduleLearningOutcomes || module.moduleLearningOutcomes.filter(o => o.trim()).length === 0) {
      alert('Please define Module Learning Outcomes first')
      return
    }

    const conceptKey = `${moduleId}-${conceptId}`
    setGeneratingForConcept(conceptKey)
    try {
      const response = await api.generateConceptLearningObjectives(
        concept.title,
        module.title,
        module.moduleLearningOutcomes.filter(o => o.trim()),
        courseData.title,
        courseData.domain,
        courseData.taxonomy
      )

      if (response.success && response.objectives) {
        updateConcept(moduleId, conceptId, 'learningObjectives', response.objectives)
      }
    } catch (error) {
      console.error('Error generating concept objectives:', error)
      alert(`Failed to generate concept objectives: ${error.message}`)
    } finally {
      setGeneratingForConcept(null)
    }
  }

  const togglePrerequisite = (moduleId, conceptId, prereqModuleId, prereqConceptId) => {
    const prereqString = `module-${prereqModuleId}-concept-${prereqConceptId}`

    setModules(modules.map(m => {
      if (m.id === moduleId) {
        return {
          ...m,
          concepts: m.concepts.map(c => {
            if (c.id === conceptId) {
              const prerequisites = c.prerequisites.includes(prereqString)
                ? c.prerequisites.filter(p => p !== prereqString)
                : [...c.prerequisites, prereqString]
              return { ...c, prerequisites }
            }
            return c
          })
        }
      }
      return m
    }))
  }

  const validate = () => {
    const newErrors = {}

    modules.forEach((module, moduleIndex) => {
      if (!module.title.trim()) {
        newErrors[`module-${module.id}`] = `Module ${moduleIndex + 1} title is required`
      } else if (module.title.length < 5) {
        newErrors[`module-${module.id}`] = `Module ${moduleIndex + 1} title must be at least 5 characters`
      }

      // Validate module learning outcomes
      const validMLOs = module.moduleLearningOutcomes.filter(o => o.trim())
      if (validMLOs.length < 2) {
        newErrors[`module-${module.id}-mlos`] = `Module ${moduleIndex + 1} must have at least 2 learning outcomes`
      }

      // Validate concepts
      module.concepts.forEach((concept, conceptIndex) => {
        if (!concept.title.trim()) {
          newErrors[`concept-${module.id}-${concept.id}`] = `Module ${moduleIndex + 1}, Concept ${conceptIndex + 1} title is required`
        } else if (concept.title.length < 5) {
          newErrors[`concept-${module.id}-${concept.id}`] = `Module ${moduleIndex + 1}, Concept ${conceptIndex + 1} title must be at least 5 characters`
        }

        // Validate concept learning objectives
        const validObjectives = (concept.learningObjectives || []).filter(o => o.trim())
        if (validObjectives.length < 3) {
          newErrors[`concept-${module.id}-${concept.id}-objectives`] = `Module ${moduleIndex + 1}, Concept ${conceptIndex + 1} must have at least 3 learning objectives`
        }
      })
    })

    if (modules.length < 1) {
      newErrors.general = 'You must create at least 1 module'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleNext = () => {
    if (validate()) {
      // Initialize module data with concept IDs
      const initializedModules = modules.map((module, moduleIndex) => ({
        ...module,
        moduleId: `module-${String(moduleIndex + 1).padStart(3, '0')}`,
        concepts: module.concepts.map((concept, conceptIndex) => ({
          ...concept,
          conceptId: `concept-${String(conceptIndex + 1).padStart(3, '0')}`,
          learningObjectives: concept.learningObjectives || [],
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
        Organize your course into modules. Each module groups related concepts and has its own learning outcomes.
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
                <>
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
                      description="Module-level outcomes are more specific than course outcomes. They describe what students will achieve within this particular module and should clearly align with one or more Course Learning Outcomes (CLOs)."
                      onGenerateSuggestions={() => handleGenerateMLOs(module.id)}
                      isGenerating={generatingForModule === module.id}
                    />
                    {errors[`module-${module.id}-mlos`] && (
                      <div className="validation-error">{errors[`module-${module.id}-mlos`]}</div>
                    )}
                  </div>

                  <div className="concepts-section">
                    <h4>Concepts in this Module</h4>
                    {module.concepts.map((concept, conceptIndex) => (
                      <div key={concept.id} className="concept-item-card">
                        <div className="concept-item-header">
                          <h5>Concept {moduleIndex + 1}.{conceptIndex + 1}</h5>
                          {module.concepts.length > 1 && (
                            <button
                              onClick={() => removeConcept(module.id, concept.id)}
                              className="remove-button small"
                              type="button"
                            >
                              Remove
                            </button>
                          )}
                        </div>

                        <div className="form-group">
                          <label>Concept Title <span className="required">*</span></label>
                          <input
                            type="text"
                            value={concept.title}
                            onChange={(e) => updateConcept(module.id, concept.id, 'title', e.target.value)}
                            placeholder="e.g., Linear Functions, Quadratic Equations"
                            maxLength={100}
                          />
                          {errors[`concept-${module.id}-${concept.id}`] && (
                            <div className="validation-error">
                              {errors[`concept-${module.id}-${concept.id}`]}
                            </div>
                          )}
                        </div>

                        <div className="form-group">
                          <LearningOutcomeBuilder
                            outcomes={concept.learningObjectives || ['', '', '']}
                            onChange={(objectives) => updateConcept(module.id, concept.id, 'learningObjectives', objectives)}
                            taxonomy={courseData.taxonomy || 'blooms'}
                            domain={courseData.domain}
                            courseTitle={concept.title}
                            minOutcomes={3}
                            maxOutcomes={5}
                            label="Concept Learning Objectives"
                            description="Concept-level objectives are the most specific and granular. They describe the discrete skills or knowledge students will master in this individual concept, supporting the module outcomes."
                            onGenerateSuggestions={() => handleGenerateConceptObjectives(module.id, concept.id)}
                            isGenerating={generatingForConcept === `${module.id}-${concept.id}`}
                          />
                        </div>

                        {/* Prerequisites */}
                        <div className="form-group">
                          <label>Prerequisites (Optional)</label>
                          <p className="hint">Select concepts that students should complete before this one</p>
                          <div className="prerequisites-grid">
                            {modules.flatMap((m, mIdx) =>
                              m.concepts.map((c, cIdx) => {
                                const isCurrentConcept = m.id === module.id && c.id === concept.id
                                const isInSameModule = m.id === module.id
                                const isLaterConcept = m.id === module.id && cIdx >= conceptIndex
                                const prereqString = `module-${m.id}-concept-${c.id}`
                                const isSelected = concept.prerequisites.includes(prereqString)

                                if (isCurrentConcept) return null

                                return (
                                  <label
                                    key={prereqString}
                                    className={`prerequisite-option ${isLaterConcept ? 'disabled' : ''}`}
                                  >
                                    <input
                                      type="checkbox"
                                      checked={isSelected}
                                      onChange={() => togglePrerequisite(module.id, concept.id, m.id, c.id)}
                                      disabled={isLaterConcept}
                                    />
                                    <span>
                                      Module {mIdx + 1}.{cIdx + 1}: {c.title || 'Untitled Concept'}
                                    </span>
                                  </label>
                                )
                              })
                            )}
                          </div>
                        </div>
                      </div>
                    ))}

                    <button
                      onClick={() => addConcept(module.id)}
                      className="add-button"
                      type="button"
                    >
                      + Add Concept to Module {moduleIndex + 1}
                    </button>
                  </div>
                </>
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
