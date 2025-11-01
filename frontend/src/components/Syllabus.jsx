import React, { useState, useEffect } from 'react'
import { api } from '../api'
import './Syllabus.css'

function Syllabus({ learnerId, courseId = 'latin-grammar', onClose }) {
  const [loading, setLoading] = useState(true)
  const [courseData, setCourseData] = useState(null)
  const [progress, setProgress] = useState(null)
  const [conceptDetails, setConceptDetails] = useState({})
  const [error, setError] = useState(null)

  useEffect(() => {
    loadSyllabusData()
  }, [learnerId, courseId])

  const loadSyllabusData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load course metadata (includes CLOs and concept list)
      const course = await api.getCourse(courseId)
      setCourseData(course)

      // Load learner progress (includes mastery scores and current concept)
      const learnerProgress = await api.getProgress(learnerId)
      setProgress(learnerProgress)

      // Load detailed metadata for each concept (to get MLOs)
      const details = {}
      for (const concept of course.concepts || []) {
        try {
          const metadata = await api.getConceptMetadata(concept.concept_id)
          details[concept.concept_id] = metadata
        } catch (err) {
          console.warn(`Failed to load details for ${concept.concept_id}:`, err)
        }
      }
      setConceptDetails(details)

      setLoading(false)
    } catch (err) {
      console.error('Error loading syllabus:', err)
      setError(err.message)
      setLoading(false)
    }
  }

  const getConceptStatus = (conceptId) => {
    if (!progress) return 'locked'

    const currentConcept = progress.current_concept
    const conceptData = progress.concept_details?.[conceptId]

    if (conceptData?.completed) {
      return 'completed'
    } else if (conceptId === currentConcept) {
      return 'in-progress'
    } else {
      // Check if prerequisites are met
      const concept = courseData?.concepts?.find(c => c.concept_id === conceptId)
      const prerequisites = concept?.prerequisites || []

      if (prerequisites.length === 0) {
        return 'available'
      }

      const allPrereqsMet = prerequisites.every(prereq =>
        progress.concept_details?.[prereq]?.completed
      )

      return allPrereqsMet ? 'available' : 'locked'
    }
  }

  const getMasteryScore = (conceptId) => {
    const conceptData = progress?.concept_details?.[conceptId]
    return conceptData?.mastery_score || 0
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return '✓'
      case 'in-progress': return '⚡'
      case 'available': return '○'
      case 'locked': return '🔒'
      default: return ''
    }
  }

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed': return 'Completed'
      case 'in-progress': return 'In Progress'
      case 'available': return 'Available'
      case 'locked': return 'Locked'
      default: return ''
    }
  }

  const getCLOProgress = (clo, index) => {
    // Calculate progress for a CLO based on related concepts
    // For now, we'll use overall course progress
    if (!progress) return 0

    const totalConcepts = courseData?.concepts?.length || 1
    const completedConcepts = progress.concepts_completed || 0

    return Math.round((completedConcepts / totalConcepts) * 100)
  }

  if (loading) {
    return (
      <div className="syllabus-overlay">
        <div className="syllabus-modal">
          <div className="syllabus-loading">
            <div className="spinner"></div>
            <p>Loading syllabus...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="syllabus-overlay">
        <div className="syllabus-modal">
          <div className="syllabus-error">
            <h2>Error Loading Syllabus</h2>
            <p>{error}</p>
            <button onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="syllabus-overlay" onClick={onClose}>
      <div className="syllabus-modal" onClick={(e) => e.stopPropagation()}>
        <div className="syllabus-header">
          <h1>📚 {courseData?.title || 'Course Syllabus'}</h1>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="syllabus-content">
          {/* Overall Progress */}
          <div className="progress-overview">
            <div className="progress-stat">
              <span className="stat-label">Concepts Completed</span>
              <span className="stat-value">
                {progress?.concepts_completed || 0} / {courseData?.concepts?.length || 0}
              </span>
            </div>
            <div className="progress-stat">
              <span className="stat-label">Total Assessments</span>
              <span className="stat-value">{progress?.total_assessments || 0}</span>
            </div>
            <div className="progress-stat">
              <span className="stat-label">Overall Mastery</span>
              <span className="stat-value">
                {Math.round(
                  ((progress?.concepts_completed || 0) / (courseData?.concepts?.length || 1)) * 100
                )}%
              </span>
            </div>
          </div>

          {/* Course Learning Outcomes */}
          {courseData?.course_learning_outcomes && courseData.course_learning_outcomes.length > 0 && (
            <section className="clo-section">
              <h2>Course Learning Outcomes</h2>
              <div className="clo-list">
                {courseData.course_learning_outcomes.map((clo, index) => {
                  const cloProgress = getCLOProgress(clo, index)
                  return (
                    <div key={index} className="clo-item">
                      <div className="clo-header">
                        <span className="clo-number">CLO {index + 1}</span>
                        <span className="clo-progress">{cloProgress}%</span>
                      </div>
                      <p className="clo-text">{clo}</p>
                      <div className="clo-progress-bar">
                        <div
                          className="clo-progress-fill"
                          style={{ width: `${cloProgress}%` }}
                        ></div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </section>
          )}

          {/* Concepts/Modules List */}
          <section className="concepts-section">
            <h2>Modules</h2>
            <div className="concepts-list">
              {courseData?.concepts?.map((concept, index) => {
                const status = getConceptStatus(concept.concept_id)
                const mastery = getMasteryScore(concept.concept_id)
                const detail = conceptDetails[concept.concept_id]

                return (
                  <div
                    key={concept.concept_id}
                    className={`concept-card concept-${status}`}
                  >
                    <div className="concept-header">
                      <div className="concept-title-row">
                        <span className="concept-icon">{getStatusIcon(status)}</span>
                        <h3 className="concept-title">
                          Module {index + 1}: {concept.title}
                        </h3>
                      </div>
                      <div className="concept-meta">
                        <span className={`status-badge status-${status}`}>
                          {getStatusLabel(status)}
                        </span>
                        {status !== 'locked' && mastery > 0 && (
                          <span className="mastery-badge">
                            {Math.round(mastery * 100)}% Mastery
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Module Learning Outcomes */}
                    {detail?.learning_objectives && detail.learning_objectives.length > 0 && (
                      <div className="mlo-section">
                        <h4>Module Learning Outcomes</h4>
                        <ul className="mlo-list">
                          {detail.learning_objectives.map((mlo, mloIndex) => (
                            <li key={mloIndex} className="mlo-item">
                              {mlo}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Prerequisites */}
                    {detail?.prerequisites && detail.prerequisites.length > 0 && (
                      <div className="prerequisites">
                        <strong>Prerequisites:</strong>{' '}
                        {detail.prerequisites.map(prereq => {
                          const prereqConcept = courseData.concepts.find(c => c.concept_id === prereq)
                          return prereqConcept?.title || prereq
                        }).join(', ')}
                      </div>
                    )}

                    {/* Estimated Time */}
                    {detail?.estimated_mastery_time && (
                      <div className="concept-time">
                        <strong>Estimated Time:</strong> {detail.estimated_mastery_time}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
        </div>

        <div className="syllabus-footer">
          <button className="close-footer-button" onClick={onClose}>
            Close Syllabus
          </button>
        </div>
      </div>
    </div>
  )
}

export default Syllabus
