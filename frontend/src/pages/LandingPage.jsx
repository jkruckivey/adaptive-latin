import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import LandingPageComponent from '../components/LandingPage'

export default function LandingPage({ onStart, onCreateCourse }) {
    const [showNameEntry, setShowNameEntry] = useState(false)
    const [learnerName, setLearnerName] = useState('')
    const [error, setError] = useState(null)
    const navigate = useNavigate()

    const handleStartClick = () => {
        setShowNameEntry(true)
    }

    const handleCreateCourseClick = () => {
        navigate('/create-course')
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        if (!learnerName.trim()) {
            setError('Please enter your name')
            return
        }
        onStart(learnerName)
    }

    if (!showNameEntry) {
        return (
            <LandingPageComponent
                onStartLearning={handleStartClick}
                onCreateCourse={handleCreateCourseClick}
            />
        )
    }

    return (
        <div className="welcome-container">
            <button
                onClick={() => setShowNameEntry(false)}
                className="back-button"
                style={{
                    alignSelf: 'flex-start',
                    marginBottom: '20px',
                    background: 'transparent',
                    border: 'none',
                    color: 'white',
                    cursor: 'pointer',
                    fontSize: '1rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}
            >
                ← Back
            </button>

            <h1>Let's get started!</h1>
            <p className="welcome-subtitle">First, tell us your name</p>

            <form onSubmit={handleSubmit} className="start-form">
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
                    Continue
                </button>
            </form>
        </div>
    )
}
