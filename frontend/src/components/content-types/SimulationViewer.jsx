import { useState, useEffect } from 'react'
import './SimulationViewer.css'

function SimulationViewer({ courseId, moduleId, simulationType, onContinue, learnerId }) {
  const [html, setHtml] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)
  const [completed, setCompleted] = useState(false)

  useEffect(() => {
    const fetchSimulation = async () => {
      try {
        setLoading(true)
        setError(null)

        const API_BASE_URL = import.meta.env.PROD
          ? 'https://adaptive-latin-backend.onrender.com'
          : '/api'

        const response = await fetch(
          `${API_BASE_URL}/courses/${courseId}/modules/${moduleId}/simulations/${simulationType}`
        )

        if (!response.ok) {
          throw new Error(`Failed to load simulation: ${response.statusText}`)
        }

        const htmlContent = await response.text()
        setHtml(htmlContent)
      } catch (err) {
        console.error('Error loading simulation:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (courseId && moduleId && simulationType) {
      fetchSimulation()
    }
  }, [courseId, moduleId, simulationType])

  // Listen for messages from simulation
  useEffect(() => {
    const handleMessage = async (event) => {
      // Verify message is from our simulation
      if (event.data.type !== 'simulation-complete') return

      console.log('Received simulation data:', event.data)
      setCompleted(true)

      // Send results to backend
      try {
        const API_BASE_URL = import.meta.env.PROD
          ? 'https://adaptive-latin-backend.onrender.com'
          : '/api'

        const response = await fetch(`${API_BASE_URL}/simulation-results`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            learner_id: learnerId,
            course_id: courseId,
            module_id: moduleId,
            simulation_type: event.data.simulationType,
            data: event.data.data,
            timestamp: new Date().toISOString()
          }),
        })

        if (response.ok) {
          const result = await response.json()
          if (result.feedback) {
            setFeedback(result.feedback)
          }
        }
      } catch (err) {
        console.error('Error saving simulation results:', err)
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [courseId, moduleId, simulationType, learnerId])

  if (loading) {
    return (
      <div className="simulation-viewer">
        <div className="simulation-loading">
          <div className="spinner"></div>
          <p>Loading simulation...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="simulation-viewer">
        <div className="simulation-error">
          <h3>Failed to Load Simulation</h3>
          <p>{error}</p>
          <button onClick={onContinue} className="continue-button">
            Continue Anyway →
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="simulation-viewer">
      <div
        className="simulation-content"
        dangerouslySetInnerHTML={{ __html: html }}
      />

      {feedback && (
        <div className="simulation-feedback">
          <h3>{feedback.title || 'Great work!'}</h3>
          <p>{feedback.message}</p>
          {feedback.insights && feedback.insights.length > 0 && (
            <div className="feedback-insights">
              <h4>Insights:</h4>
              <ul>
                {feedback.insights.map((insight, i) => (
                  <li key={i}>{insight}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="simulation-footer">
        <button
          onClick={onContinue}
          className="continue-button"
          disabled={!completed && simulationType === 'pre-assessment-quiz'}
        >
          {completed ? 'Continue →' : 'Complete the simulation to continue'}
        </button>
      </div>
    </div>
  )
}

export default SimulationViewer
