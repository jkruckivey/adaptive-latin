import { useState, useEffect } from 'react'
import { api } from '../../api'
import './UserInsights.css'

function UserInsights({ courseId }) {
  const [learners, setLearners] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedLearner, setSelectedLearner] = useState(null)
  const [learnerDetails, setLearnerDetails] = useState(null)

  useEffect(() => {
    loadLearners()
  }, [courseId])

  const loadLearners = async () => {
    setLoading(true)
    try {
      const url = courseId
        ? `http://localhost:8000/admin/learners?course_id=${courseId}`
        : 'http://localhost:8000/admin/learners'
      const response = await fetch(url)
      const data = await response.json()

      if (data.success) {
        setLearners(data.learners)
      }
    } catch (error) {
      console.error('Failed to load learners:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadLearnerDetails = async (learnerId) => {
    try {
      const progress = await api.getProgress(learnerId)
      setLearnerDetails({ learnerId, ...progress })
    } catch (error) {
      console.error('Failed to load learner details:', error)
    }
  }

  const handleLearnerClick = (learner) => {
    setSelectedLearner(learner.learner_id)
    loadLearnerDetails(learner.learner_id)
  }

  if (loading) {
    return <div className="loading">Loading learners...</div>
  }

  return (
    <div className="user-insights">
      <div className="insights-header">
        <h2>Learner Analytics</h2>
        <div className="stats-summary">
          <div className="stat-box">
            <div className="stat-number">{learners.length}</div>
            <div className="stat-label">Total Learners</div>
          </div>
          <div className="stat-box">
            <div className="stat-number">
              {learners.filter(l => l.progress?.completed_concepts?.length > 0).length}
            </div>
            <div className="stat-label">Active Learners</div>
          </div>
          <div className="stat-box">
            <div className="stat-number">
              {Math.round(
                learners.reduce((sum, l) => sum + (l.progress?.overall_progress?.concepts_completed || 0), 0) /
                (learners.length || 1)
              )}
            </div>
            <div className="stat-label">Avg Concepts Completed</div>
          </div>
        </div>
      </div>

      <div className="insights-content">
        <div className="learners-list">
          <h3>All Learners</h3>
          <div className="learners-table">
            <div className="table-header">
              <div>Name</div>
              <div>Current Concept</div>
              <div>Completed</div>
              <div>Assessments</div>
            </div>
            {learners.map(learner => (
              <div
                key={learner.learner_id}
                className={`table-row ${selectedLearner === learner.learner_id ? 'selected' : ''}`}
                onClick={() => handleLearnerClick(learner)}
              >
                <div className="learner-name">
                  <strong>{learner.learner_name || learner.learner_id}</strong>
                </div>
                <div>{learner.progress?.current_concept || 'Not started'}</div>
                <div>{learner.progress?.overall_progress?.concepts_completed || 0}</div>
                <div>{learner.progress?.overall_progress?.total_assessments || 0}</div>
              </div>
            ))}
          </div>
        </div>

        {learnerDetails && (
          <div className="learner-details">
            <h3>Learner Details: {learnerDetails.learnerId}</h3>

            <div className="detail-section">
              <h4>Progress</h4>
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Current Concept:</span>
                  <span className="detail-value">{learnerDetails.current_concept || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Completed Concepts:</span>
                  <span className="detail-value">{learnerDetails.completed_concepts?.length || 0}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Total Assessments:</span>
                  <span className="detail-value">{learnerDetails.overall_progress?.total_assessments || 0}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Avg Score:</span>
                  <span className="detail-value">
                    {learnerDetails.overall_progress?.avg_score?.toFixed(1) || 'N/A'}%
                  </span>
                </div>
              </div>
            </div>

            {learnerDetails.completed_concepts && learnerDetails.completed_concepts.length > 0 && (
              <div className="detail-section">
                <h4>Completed Concepts</h4>
                <div className="concept-tags">
                  {learnerDetails.completed_concepts.map(concept => (
                    <span key={concept} className="concept-tag">{concept}</span>
                  ))}
                </div>
              </div>
            )}

            {learnerDetails.mastery_scores && Object.keys(learnerDetails.mastery_scores).length > 0 && (
              <div className="detail-section">
                <h4>Mastery Scores</h4>
                <div className="mastery-list">
                  {Object.entries(learnerDetails.mastery_scores).map(([concept, score]) => (
                    <div key={concept} className="mastery-item">
                      <span className="mastery-concept">{concept}</span>
                      <div className="mastery-bar-container">
                        <div
                          className="mastery-bar"
                          style={{ width: `${score}%` }}
                        />
                        <span className="mastery-score">{score}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default UserInsights
