import { useState, useEffect } from 'react'
import ChatInterface from './components/ChatInterface'
import ProgressDashboard from './components/ProgressDashboard'
import { api } from './api'
import './App.css'

function App() {
  const [learnerId, setLearnerId] = useState(null)
  const [learnerName, setLearnerName] = useState('')
  const [isStarted, setIsStarted] = useState(false)
  const [progress, setProgress] = useState(null)
  const [error, setError] = useState(null)

  // Generate or retrieve learner ID
  useEffect(() => {
    const storedLearnerId = localStorage.getItem('learnerId')
    if (storedLearnerId) {
      setLearnerId(storedLearnerId)
      setIsStarted(true)
      loadProgress(storedLearnerId)
    }
  }, [])

  const loadProgress = async (id) => {
    try {
      const data = await api.getProgress(id)
      if (data.success) {
        setProgress(data)
      }
    } catch (err) {
      console.error('Failed to load progress:', err)
    }
  }

  const handleStart = async (e) => {
    e.preventDefault()
    if (!learnerName.trim()) {
      setError('Please enter your name')
      return
    }

    try {
      const id = `learner-${Date.now()}`
      const response = await api.startLearner(id, learnerName)

      if (response.success) {
        setLearnerId(id)
        setIsStarted(true)
        localStorage.setItem('learnerId', id)
        setError(null)
      } else {
        setError(response.message || 'Failed to start learning session')
      }
    } catch (err) {
      setError('Connection error. Please try again.')
      console.error('Start error:', err)
    }
  }

  const handleReset = () => {
    if (confirm('Are you sure you want to reset your progress?')) {
      localStorage.removeItem('learnerId')
      setLearnerId(null)
      setIsStarted(false)
      setLearnerName('')
      setProgress(null)
    }
  }

  if (!isStarted) {
    return (
      <div className="app">
        <div className="welcome-container">
          <h1>🏛️ Adaptive Latin Learning</h1>
          <p className="welcome-subtitle">AI-powered personalized Latin grammar instruction</p>

          <form onSubmit={handleStart} className="start-form">
            <div className="form-group">
              <label htmlFor="name">What's your name?</label>
              <input
                id="name"
                type="text"
                value={learnerName}
                onChange={(e) => setLearnerName(e.target.value)}
                placeholder="Enter your name"
                className="name-input"
                autoFocus
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="start-button">
              Begin Learning
            </button>
          </form>

          <div className="features">
            <div className="feature">
              <span className="feature-icon">🤖</span>
              <div>
                <h3>AI Tutor</h3>
                <p>Personalized guidance with Claude</p>
              </div>
            </div>
            <div className="feature">
              <span className="feature-icon">📊</span>
              <div>
                <h3>Adaptive Pacing</h3>
                <p>Progress when ready, review when needed</p>
              </div>
            </div>
            <div className="feature">
              <span className="feature-icon">🎯</span>
              <div>
                <h3>Confidence Tracking</h3>
                <p>Build metacognitive awareness</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>🏛️ Adaptive Latin</h1>
          <button onClick={handleReset} className="reset-button">
            Reset Progress
          </button>
        </div>
      </header>

      <div className="main-content">
        <div className="chat-column">
          <ChatInterface
            learnerId={learnerId}
            onProgressUpdate={() => loadProgress(learnerId)}
          />
        </div>
        <div className="progress-column">
          <ProgressDashboard
            learnerId={learnerId}
            progress={progress}
          />
        </div>
      </div>
    </div>
  )
}

export default App
