import { useState, useEffect } from 'react'
import { api } from '../../api'
import './CourseEditor.css'

function CourseEditor({ courseId }) {
  const [modules, setModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingModule, setEditingModule] = useState(null)
  const [editingConcept, setEditingConcept] = useState(null)
  const [saveStatus, setSaveStatus] = useState(null)

  useEffect(() => {
    loadCourse()
  }, [courseId])

  const loadCourse = async () => {
    setLoading(true)
    try {
      const response = await api.getModules('learner-001', courseId)
      if (response.success && response.modules) {
        // Load full details for each module and concept
        const modulesWithDetails = await Promise.all(
          response.modules.map(async (module) => {
            const conceptDetails = await Promise.all(
              module.concepts.map(async (conceptId) => {
                try {
                  const metadata = await api.getConceptMetadata(conceptId, 'learner-001', courseId)
                  return { ...metadata, concept_id: conceptId }
                } catch (err) {
                  return { concept_id: conceptId, title: conceptId }
                }
              })
            )
            return { ...module, conceptDetails }
          })
        )
        setModules(modulesWithDetails)
      }
    } catch (error) {
      console.error('Failed to load course:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleModuleEdit = (module) => {
    setEditingModule({
      id: module.id,
      title: module.title,
      module_learning_outcomes: [...module.module_learning_outcomes]
    })
  }

  const handleConceptEdit = (moduleId, concept) => {
    setEditingConcept({
      moduleId,
      concept_id: concept.concept_id,
      title: concept.title,
      learning_objectives: concept.learning_objectives || []
    })
  }

  const saveModuleChanges = async () => {
    try {
      const response = await fetch(`http://localhost:8000/admin/modules/${editingModule.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: courseId,
          title: editingModule.title,
          module_learning_outcomes: editingModule.module_learning_outcomes
        })
      })

      if (response.ok) {
        setSaveStatus({ type: 'success', message: 'Module updated successfully!' })
        setEditingModule(null)
        await loadCourse()
        setTimeout(() => setSaveStatus(null), 3000)
      } else {
        throw new Error('Failed to save module')
      }
    } catch (error) {
      setSaveStatus({ type: 'error', message: 'Failed to save changes' })
      console.error('Failed to save module:', error)
    }
  }

  const saveConceptChanges = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/admin/concepts/${editingConcept.concept_id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            course_id: courseId,
            module_id: editingConcept.moduleId,
            title: editingConcept.title,
            learning_objectives: editingConcept.learning_objectives
          })
        }
      )

      if (response.ok) {
        setSaveStatus({ type: 'success', message: 'Concept updated successfully!' })
        setEditingConcept(null)
        await loadCourse()
        setTimeout(() => setSaveStatus(null), 3000)
      } else {
        throw new Error('Failed to save concept')
      }
    } catch (error) {
      setSaveStatus({ type: 'error', message: 'Failed to save changes' })
      console.error('Failed to save concept:', error)
    }
  }

  if (loading) {
    return <div className="loading">Loading course structure...</div>
  }

  return (
    <div className="course-editor">
      <div className="editor-header">
        <h2>Course Editor</h2>
        {saveStatus && (
          <div className={`save-status ${saveStatus.type}`}>
            {saveStatus.message}
          </div>
        )}
      </div>

      <div className="modules-editor">
        {modules.map((module, moduleIndex) => (
          <div key={module.id} className="module-editor-card">
            <div className="module-editor-header">
              <div>
                <h3>
                  Module {moduleIndex + 1}: {module.title}
                </h3>
                <p className="module-id">{module.id}</p>
              </div>
              <button
                className="btn-edit"
                onClick={() => handleModuleEdit(module)}
              >
                Edit Module
              </button>
            </div>

            <div className="mlos-section">
              <h4>Module Learning Outcomes ({module.module_learning_outcomes.length})</h4>
              <ul className="mlos-list">
                {module.module_learning_outcomes.map((mlo, idx) => (
                  <li key={idx}>{mlo}</li>
                ))}
              </ul>
            </div>

            <div className="concepts-section">
              <h4>Concepts ({module.conceptDetails?.length || 0})</h4>
              <div className="concepts-grid">
                {module.conceptDetails?.map((concept) => (
                  <div key={concept.concept_id} className="concept-editor-card">
                    <div className="concept-header">
                      <span className="concept-id-badge">{concept.concept_id}</span>
                      <button
                        className="btn-edit-small"
                        onClick={() => handleConceptEdit(module.id, concept)}
                      >
                        Edit
                      </button>
                    </div>
                    <p className="concept-title">{concept.title}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {editingModule && (
        <div className="modal-overlay" onClick={() => setEditingModule(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Edit Module</h3>

            <div className="form-group">
              <label>Module Title</label>
              <input
                type="text"
                value={editingModule.title}
                onChange={(e) =>
                  setEditingModule({ ...editingModule, title: e.target.value })
                }
              />
            </div>

            <div className="form-group">
              <label>Module Learning Outcomes</label>
              {editingModule.module_learning_outcomes.map((mlo, idx) => (
                <div key={idx} className="mlo-input-group">
                  <input
                    type="text"
                    value={mlo}
                    onChange={(e) => {
                      const newMLOs = [...editingModule.module_learning_outcomes]
                      newMLOs[idx] = e.target.value
                      setEditingModule({ ...editingModule, module_learning_outcomes: newMLOs })
                    }}
                  />
                  <button
                    className="btn-remove"
                    onClick={() => {
                      const newMLOs = editingModule.module_learning_outcomes.filter(
                        (_, i) => i !== idx
                      )
                      setEditingModule({ ...editingModule, module_learning_outcomes: newMLOs })
                    }}
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                className="btn-add"
                onClick={() => {
                  setEditingModule({
                    ...editingModule,
                    module_learning_outcomes: [...editingModule.module_learning_outcomes, '']
                  })
                }}
              >
                Add MLO
              </button>
            </div>

            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setEditingModule(null)}>
                Cancel
              </button>
              <button className="btn-save" onClick={saveModuleChanges}>
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {editingConcept && (
        <div className="modal-overlay" onClick={() => setEditingConcept(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Edit Concept</h3>

            <div className="form-group">
              <label>Concept ID</label>
              <input type="text" value={editingConcept.concept_id} disabled />
            </div>

            <div className="form-group">
              <label>Concept Title</label>
              <input
                type="text"
                value={editingConcept.title}
                onChange={(e) =>
                  setEditingConcept({ ...editingConcept, title: e.target.value })
                }
              />
            </div>

            <div className="form-group">
              <label>Learning Objectives</label>
              {editingConcept.learning_objectives.map((lo, idx) => (
                <div key={idx} className="mlo-input-group">
                  <input
                    type="text"
                    value={lo}
                    onChange={(e) => {
                      const newLOs = [...editingConcept.learning_objectives]
                      newLOs[idx] = e.target.value
                      setEditingConcept({ ...editingConcept, learning_objectives: newLOs })
                    }}
                  />
                  <button
                    className="btn-remove"
                    onClick={() => {
                      const newLOs = editingConcept.learning_objectives.filter(
                        (_, i) => i !== idx
                      )
                      setEditingConcept({ ...editingConcept, learning_objectives: newLOs })
                    }}
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                className="btn-add"
                onClick={() => {
                  setEditingConcept({
                    ...editingConcept,
                    learning_objectives: [...editingConcept.learning_objectives, '']
                  })
                }}
              >
                Add Learning Objective
              </button>
            </div>

            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setEditingConcept(null)}>
                Cancel
              </button>
              <button className="btn-save" onClick={saveConceptChanges}>
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CourseEditor
