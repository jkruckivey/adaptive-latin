import { useState, useEffect } from 'react'
import { api } from '../api'
import './CourseSelector.css'

function CourseSelector({ onCourseSelected, onSkip, onBack }) {
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
        <div className="spinner"></div>
        <p>Loading courses...</p>
      </div>
    )
  }

  if (courses.length === 0) {
    return (
      <div className="course-selector">
        <h2>No Courses Available</h2>
        <p>No courses found. Please create a course first.</p>
      </div>
    )
  }

  if (courses.length === 1) {
    return (
      <div className="course-selector single-course">
        {onBack && (
          <button onClick={onBack} className="back-button-selector">
            ← Back
          </button>
        )}

        <h2>Ready to Start Learning</h2>
        <div className="course-card selected">
          <div className="course-header">
            <h3>{courses[0].title}</h3>
            <span className="course-type-badge">{courses[0].type}</span>
          </div>

          <p className="course-domain">{courses[0].domain}</p>

          {courses[0].description && (
            <p className="course-description">{courses[0].description}</p>
          )}

          <div className="course-meta">
            {courses[0].concepts_count && (
              <span className="meta-item">
                <span className="meta-icon">📚</span>
                {courses[0].concepts_count} concepts
              </span>
            )}
            {courses[0].estimated_hours && (
              <span className="meta-item">
                <span className="meta-icon">⏱️</span>
                ~{courses[0].estimated_hours} hours
              </span>
            )}
          </div>
        </div>

        <button onClick={handleContinue} className="continue-button">
          Start Learning
        </button>
      </div>
    )
  }

  return (
    <div className="course-selector">
      {onBack && (
        <button onClick={onBack} className="back-button-selector">
          ← Back
        </button>
      )}

      <h2>Browse Courses</h2>
      <p className="selector-hint">Choose a course to begin your learning journey</p>

      <div className="courses-grid">
        {courses.map((course) => (
          <div
            key={course.course_id}
            className={`course-card ${selectedCourse?.course_id === course.course_id ? 'selected' : ''}`}
            onClick={() => setSelectedCourse(course)}
          >
            <div className="course-header">
              <h3>{course.title}</h3>
              <span className="course-type-badge">{course.type}</span>
            </div>

            <p className="course-domain">{course.domain}</p>

            {course.description && (
              <p className="course-description">{course.description}</p>
            )}

            <div className="course-meta">
              {course.concepts_count && (
                <span className="meta-item">
                  <span className="meta-icon">📚</span>
                  {course.concepts_count} concepts
                </span>
              )}
              {course.estimated_hours && (
                <span className="meta-item">
                  <span className="meta-icon">⏱️</span>
                  ~{course.estimated_hours} hours
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="selector-actions">
        <button
          onClick={handleContinue}
          disabled={!selectedCourse}
          className="continue-button"
        >
          Start Learning {selectedCourse && `- ${selectedCourse.title}`}
        </button>
      </div>
    </div>
  )
}

export default CourseSelector
