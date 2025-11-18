import { useState, useEffect } from 'react'
import { api } from '../api'
import UserInsights from './admin/UserInsights'
import CourseEditor from './admin/CourseEditor'
import './AdminDashboard.css'

function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('insights')
  const [courses, setCourses] = useState([])
  const [selectedCourse, setSelectedCourse] = useState('')

  useEffect(() => {
    loadCourses()
  }, [])

  const loadCourses = async () => {
    try {
      const response = await api.listCourses()
      if (response.courses) {
        setCourses(response.courses)
        // Set default to first course if not already set
        if (!selectedCourse && response.courses.length > 0) {
          setSelectedCourse(response.courses[0].course_id)
        }
      }
    } catch (error) {
      console.error('Failed to load courses:', error)
    }
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h1>Admin Dashboard</h1>
        <div className="course-selector">
          <label htmlFor="course-select">Course:</label>
          <select
            id="course-select"
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
          >
            {courses.map(course => (
              <option key={course.course_id} value={course.course_id}>
                {course.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="admin-tabs">
        <button
          className={`admin-tab ${activeTab === 'insights' ? 'active' : ''}`}
          onClick={() => setActiveTab('insights')}
        >
          User Insights
        </button>
        <button
          className={`admin-tab ${activeTab === 'editor' ? 'active' : ''}`}
          onClick={() => setActiveTab('editor')}
        >
          Course Editor
        </button>
      </div>

      <div className="admin-content">
        {activeTab === 'insights' && <UserInsights courseId={selectedCourse} />}
        {activeTab === 'editor' && <CourseEditor courseId={selectedCourse} />}
      </div>
    </div>
  )
}

export default AdminDashboard
