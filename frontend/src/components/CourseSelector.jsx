import { useState, useEffect } from 'react'
import { api } from '../api'
import './CourseSelector.css'

function CourseSelector({ onCourseSelected, onSkip, onCreateCourse }) {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedCourse, setSelectedCourse] = useState(null)

  useEffect(() => {
    loadCourses()
  }, [])

  const loadCourses = async () => {
    try {
      const response = await api.listCourses()
      // Response has { courses: [...], total: N } format
      if (response.courses) {
        setCourses(response.courses)
        if (response.courses.length === 1) {
          setSelectedCourse(response.courses[0])
        }
      }
      setLoading(false)
    } catch (error) {
      console.error('Failed to load courses:', error)
      setLoading(false)
    }
  }

  const handleContinue = () => {
    if (selectedCourse && onCourseSelected) {
      onCourseSelected(selectedCourse.course_id, selectedCourse.title)
    }
  }

  if (loading) {
    return (
      <div className="course-selector">
        <div className="selector-container">
          <div className="spinner"></div>
          <p>Loading courses...</p>
        </div>
      </div>
    )
  }

  if (courses.length === 0) {
    return (
      <div className="course-selector">
        <div className="selector-container">
          <h1>No Courses Available</h1>
          <p className="selector-hint">Get started by creating your first course</p>
          <div className="create-course-option" onClick={onCreateCourse || onSkip}>
            <div className="option-icon">+</div>
            <div className="option-title">Create New Course</div>
            <div className="option-description">
              Build a custom course tailored to your learning goals
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="course-selector">
      <div className="selector-container">
        <h1>Select Your Course</h1>
        <p className="selector-hint">Choose which course you'd like to study</p>

        <div className="courses-grid">
          {courses.map((course) => (
            <div
              key={course.course_id}
              className={`course-card ${selectedCourse?.course_id === course.course_id ? 'selected' : ''}`}
              onClick={() => setSelectedCourse(course)}
            >
              <h3>{course.title}</h3>
              <p className="course-domain">{course.domain}</p>
              {course.description && (
                <p className="course-description">{course.description}</p>
              )}
              <span className="course-type-badge">{course.type}</span>
            </div>
          ))}

          <div className="create-course-option" onClick={onCreateCourse || onSkip}>
            <div className="option-icon">+</div>
            <div className="option-title">Create New Course</div>
            <div className="option-description">
              Build a custom course tailored to your learning goals
            </div>
          </div>
        </div>

        <div className="selector-actions">
          <button
            onClick={handleContinue}
            disabled={!selectedCourse}
            className="continue-button"
          >
            Continue with {selectedCourse?.title || 'Selected Course'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default CourseSelector
