import { useEffect, useState } from 'react'
import { api } from '../api'
import LearnerProfileReport from './LearnerProfileReport'
import './ProgressDashboard.css'

function ProgressDashboard({ learnerId, progress }) {
  const [concepts, setConcepts] = useState([])

  useEffect(() => {
    loadConcepts()
  }, [])

  const loadConcepts = async () => {
    try {
      const data = await api.getConcepts()
      if (data.success) {
        setConcepts(data.concepts)
      }
    } catch (error) {
      console.error('Failed to load concepts:', error)
    }
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
        <h3>Latin Grammar Concepts</h3>
        {concepts.length > 0 ? (
          <ul>
            {concepts.map((conceptId, index) => {
              const isCurrent = progress?.current_concept === conceptId
              const isCompleted = progress?.completed_concepts?.includes(conceptId)

              return (
                <li key={conceptId} className={`concept-item ${isCurrent ? 'current' : ''} ${isCompleted ? 'completed' : ''}`}>
                  <span className="concept-number">{index + 1}</span>
                  <span className="concept-id">{conceptId}</span>
                  {isCurrent && <span className="badge current-badge">Current</span>}
                  {isCompleted && <span className="badge completed-badge">✓</span>}
                </li>
              )
            })}
          </ul>
        ) : (
          <p className="loading-text">Loading concepts...</p>
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
