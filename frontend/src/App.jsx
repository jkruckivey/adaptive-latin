import { useState, useEffect } from 'react'
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import CourseSelectionPage from './pages/CourseSelectionPage'
import OnboardingPage from './pages/OnboardingPage'
import LearningPage from './pages/LearningPage'
import AdminPage from './pages/AdminPage'
import CourseCreationPage from './pages/CourseCreationPage'
import { api } from './api'
import './App.css'

function App() {
  const [learnerId, setLearnerId] = useState(null)
  const [learnerName, setLearnerName] = useState('')
  const [selectedCourseId, setSelectedCourseId] = useState(null)
  const [selectedCourseTitle, setSelectedCourseTitle] = useState(null)
  const [courseMetadata, setCourseMetadata] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const navigate = useNavigate()
  const location = useLocation()

  // Load session on startup
  useEffect(() => {
    const storedLearnerId = localStorage.getItem('learnerId')
    const storedProfile = localStorage.getItem('learnerProfile')
    const storedCourseId = localStorage.getItem('selectedCourseId')
    const storedCourseTitle = localStorage.getItem('selectedCourseTitle')

    if (storedLearnerId && storedProfile) {
      setLearnerId(storedLearnerId)
      if (storedCourseId) {
        setSelectedCourseId(storedCourseId)
        setSelectedCourseTitle(storedCourseTitle)
      }
      // Redirect to learn if on root
      if (location.pathname === '/') {
        navigate('/learn')
      }
    } else {
      // Clear stale data
      localStorage.removeItem('learnerId')
      localStorage.removeItem('selectedCourseId')
      localStorage.removeItem('selectedCourseTitle')
    }
    setIsLoading(false)
  }, [])

  // Load course metadata when course is selected
  useEffect(() => {
    const loadCourseMetadata = async () => {
      if (selectedCourseId) {
        try {
          const data = await api.getCourse(selectedCourseId)
          if (data.success) {
            setCourseMetadata(data.course)
          }
        } catch (err) {
          console.error('Failed to load course metadata:', err)
        }
      }
    }
    loadCourseMetadata()
  }, [selectedCourseId])

  const handleStart = (name) => {
    setLearnerName(name)
    navigate('/courses')
  }

  const handleCourseSelected = (courseId, courseTitle) => {
    setSelectedCourseId(courseId)
    setSelectedCourseTitle(courseTitle)
    navigate('/onboarding')
  }

  const handleOnboardingComplete = async (profile) => {
    try {
      const id = `learner-${Date.now()}`
      const response = await api.startLearner(id, learnerName, profile, selectedCourseId)

      if (response.success) {
        setLearnerId(id)
        localStorage.setItem('learnerId', id)
        localStorage.setItem('learnerProfile', JSON.stringify(profile))
        localStorage.setItem('selectedCourseId', selectedCourseId)
        localStorage.setItem('selectedCourseTitle', selectedCourseTitle)
        navigate('/learn')
      } else {
        console.error('Failed to start learning session:', response.message)
        alert('Failed to start session. Please try again.')
      }
    } catch (err) {
      console.error('Start error:', err)
      alert('Connection error. Please try again.')
    }
  }

  const handleReset = () => {
    if (confirm('Are you sure you want to reset your progress and return to the home page?')) {
      localStorage.removeItem('learnerId')
      localStorage.removeItem('learnerProfile')
      localStorage.removeItem('selectedCourseId')
      localStorage.removeItem('selectedCourseTitle')
      setLearnerId(null)
      setSelectedCourseId(null)
      setSelectedCourseTitle(null)
      setLearnerName('')
      navigate('/')
    }
  }

  if (isLoading) {
    return <div className="loading-screen">Loading...</div>
  }

  return (
    <Routes>
      <Route
        path="/"
        element={
          learnerId ? <Navigate to="/learn" /> : <LandingPage onStart={handleStart} />
        }
      />
      <Route
        path="/courses"
        element={
          <CourseSelectionPage onCourseSelected={handleCourseSelected} />
        }
      />
      <Route
        path="/onboarding"
        element={
          <OnboardingPage
            learnerName={learnerName}
            courseTitle={selectedCourseTitle}
            courseMetadata={courseMetadata}
            onComplete={handleOnboardingComplete}
          />
        }
      />
      <Route
        path="/learn"
        element={
          learnerId ? (
            <LearningPage
              learnerId={learnerId}
              selectedCourseId={selectedCourseId}
              selectedCourseTitle={selectedCourseTitle}
              onReset={handleReset}
            />
          ) : (
            <Navigate to="/" />
          )
        }
      />
      <Route path="/admin" element={<AdminPage />} />
      <Route path="/create-course" element={<CourseCreationPage />} />
    </Routes>
  )
}

export default App
