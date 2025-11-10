import { useEffect, useState } from 'react'
import { api } from '../api'
import LearnerProfileReport from './LearnerProfileReport'
import './ProgressDashboard.css'

function ProgressDashboard({ learnerId, progress, courseTitle = 'Course', courseId, onConceptClick }) {
  const [modules, setModules] = useState([])
  const [concepts, setConcepts] = useState([])
  const [conceptMetadata, setConceptMetadata] = useState({})
  const [expandedModules, setExpandedModules] = useState({})

  useEffect(() => {
    loadModulesAndConcepts()
  }, [learnerId, courseId])

  const loadModulesAndConcepts = async () => {
    try {
      // Try to load modules first (module-based structure)
      const moduleData = await api.getModules(learnerId, courseId)

      if (moduleData.success && moduleData.modules && moduleData.modules.length > 0) {
        // Module-based structure
        setModules(moduleData.modules)

        // Expand first module by default
        if (moduleData.modules.length > 0) {
          setExpandedModules({ [moduleData.modules[0].id]: true })
        }

        // Load metadata for all concepts across all modules
        const metadata = {}
        for (const module of moduleData.modules) {
          for (const conceptId of module.concepts) {
            try {
              const meta = await api.getConceptMetadata(conceptId, learnerId, courseId)
              metadata[conceptId] = meta
            } catch (err) {
              console.warn(`Failed to load metadata for ${conceptId}:`, err)
            }
          }
        }
        setConceptMetadata(metadata)
      } else {
        // Fall back to flat structure
        const data = await api.getConcepts(learnerId)
        if (data.success && data.concepts) {
          setConcepts(data.concepts)

          // Load metadata for each concept
          const metadata = {}
          for (const conceptId of data.concepts) {
            try {
              const meta = await api.getConceptMetadata(conceptId, learnerId, courseId)
              metadata[conceptId] = meta
            } catch (err) {
              console.warn(`Failed to load metadata for ${conceptId}:`, err)
            }
          }
          setConceptMetadata(metadata)
        }
      }
    } catch (error) {
      console.error('Failed to load course structure:', error)
    }
  }

  const toggleModule = (moduleId) => {
    setExpandedModules(prev => ({
      ...prev,
      [moduleId]: !prev[moduleId]
    }))
  }

  return (
    <div className="progress-dashboard">
      <h2>Your Progress</h2>

      <LearnerProfileReport learnerId={learnerId} />

      {progress && (
        <div className="progress-summary">
          <div className="stat-card">
            <div className="stat-value">{progress.current_concept || 'N/A'}</div>
            <div className="stat-label">Current Concept</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{progress.overall_progress?.concepts_completed || 0}</div>
            <div className="stat-label">Concepts Completed</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{progress.overall_progress?.total_assessments || 0}</div>
            <div className="stat-label">Assessments Taken</div>
          </div>
        </div>
      )}

      <div className="concepts-list">
        <h3>{courseTitle} {modules.length > 0 ? 'Modules' : 'Concepts'}</h3>

        {/* Module-based structure */}
        {modules.length > 0 ? (
          <div className="modules-container">
            {modules.map((module, moduleIndex) => {
              const isExpanded = expandedModules[module.id]
              const moduleConceptCount = module.concepts.length
              const completedInModule = module.concepts.filter(cId =>
                progress?.completed_concepts?.includes(cId)
              ).length

              return (
                <div key={module.id} className="module-section">
                  <div
                    className="module-header"
                    onClick={() => toggleModule(module.id)}
                  >
                    <span className="module-toggle">{isExpanded ? '▼' : '▶'}</span>
                    <div className="module-info">
                      <span className="module-number">Module {moduleIndex + 1}</span>
                      <span className="module-title">{module.title}</span>
                    </div>
                    <span className="module-progress">
                      {completedInModule}/{moduleConceptCount}
                    </span>
                  </div>

                  {isExpanded && (
                    <ul className="module-concepts">
                      {module.concepts.map((conceptId, conceptIndex) => {
                        const isCurrent = progress?.current_concept === conceptId
                        const isCompleted = progress?.completed_concepts?.includes(conceptId)
                        const conceptTitle = conceptMetadata[conceptId]?.title || conceptId

                        return (
                          <li
                            key={conceptId}
                            className={`concept-item ${isCurrent ? 'current' : ''} ${isCompleted ? 'completed' : ''}`}
                            onClick={() => onConceptClick && onConceptClick(conceptId)}
                          >
                            <span className="concept-number">{moduleIndex + 1}.{conceptIndex + 1}</span>
                            <span className="concept-id">{conceptTitle}</span>
                            {isCurrent && <span className="badge current-badge">Current</span>}
                            {isCompleted && <span className="badge completed-badge">✓</span>}
                          </li>
                        )
                      })}
                    </ul>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          /* Flat structure fallback */
          concepts.length > 0 ? (
            <ul>
              {concepts.map((conceptId, index) => {
                const isCurrent = progress?.current_concept === conceptId
                const isCompleted = progress?.completed_concepts?.includes(conceptId)
                const conceptTitle = conceptMetadata[conceptId]?.title || conceptId

                return (
                  <li
                    key={conceptId}
                    className={`concept-item ${isCurrent ? 'current' : ''} ${isCompleted ? 'completed' : ''}`}
                    onClick={() => onConceptClick && onConceptClick(conceptId)}
                  >
                    <span className="concept-number">{index + 1}</span>
                    <span className="concept-id">{conceptTitle}</span>
                    {isCurrent && <span className="badge current-badge">Current</span>}
                    {isCompleted && <span className="badge completed-badge">✓</span>}
                  </li>
                )
              })}
            </ul>
          ) : (
            <p className="loading-text">Loading course structure...</p>
          )
        )}
      </div>

      <div className="info-section">
        <h3>About This System</h3>
        <ul className="info-list">
          <li>✓ AI-powered personalized instruction</li>
          <li>✓ Adaptive progression based on mastery</li>
          <li>✓ Confidence tracking for metacognition</li>
          <li>✓ Multi-modal assessment</li>
        </ul>
      </div>
    </div>
  )
}

export default ProgressDashboard
