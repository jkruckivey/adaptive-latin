import { useState } from 'react'
import './CourseReview.css'

function CourseReview({ courseData, onBack, onPublish, onSaveDraft }) {
  const [visibility, setVisibility] = useState('unlisted')
  const [isPublishing, setIsPublishing] = useState(false)

  const handlePublish = async () => {
    setIsPublishing(true)
    try {
      await onPublish({ ...courseData, visibility })
    } catch (error) {
      alert('Failed to publish course. Please try again.')
      setIsPublishing(false)
    }
  }

  const getConceptStats = (concept) => {
    const objectives = (concept.learningObjectives || []).filter(o => o.trim()).length
    const vocab = (concept.vocabulary || []).filter(v => v.term && v.definition).length
    const contentLength = (concept.teachingContent || '').length

    return { objectives, vocab, contentLength }
  }

  return (
    <div className="wizard-form course-review">
      <h2>Review Your Course</h2>
      <p className="subtitle">
        Double-check everything looks good before publishing.
      </p>

      {/* Course Overview */}
      <div className="review-section">
        <h3>Course Information</h3>
        <div className="review-item">
          <span className="review-label">Title:</span>
          <span className="review-value">{courseData.title}</span>
        </div>
        <div className="review-item">
          <span className="review-label">Subject:</span>
          <span className="review-value">{courseData.domain}</span>
        </div>
        <div className="review-item">
          <span className="review-label">Target Audience:</span>
          <span className="review-value">{courseData.targetAudience}</span>
        </div>
        <div className="review-item">
          <span className="review-label">Description:</span>
          <span className="review-value description">{courseData.description}</span>
        </div>
      </div>

      {/* Concepts Summary */}
      <div className="review-section">
        <h3>Concepts ({(courseData.concepts || []).length})</h3>
        {(courseData.concepts || []).map((concept, index) => {
          const stats = getConceptStats(concept)
          const isComplete = stats.objectives >= 3 && stats.vocab >= 5 && stats.contentLength >= 500

          return (
            <div key={index} className={`concept-summary ${isComplete ? 'complete' : 'incomplete'}`}>
              <div className="concept-summary-header">
                <span className="concept-number">Concept {index + 1}</span>
                <span className="concept-title">{concept.title}</span>
                {isComplete ? (
                  <span className="status-badge complete">✓ Complete</span>
                ) : (
                  <span className="status-badge incomplete">⚠ Incomplete</span>
                )}
              </div>
              <div className="concept-stats">
                <span className={stats.objectives >= 3 ? 'stat-ok' : 'stat-warning'}>
                  {stats.objectives}/3+ Learning Objectives
                </span>
                <span className={stats.vocab >= 5 ? 'stat-ok' : 'stat-warning'}>
                  {stats.vocab}/5+ Vocabulary Terms
                </span>
                <span className={stats.contentLength >= 500 ? 'stat-ok' : 'stat-warning'}>
                  {stats.contentLength}/500+ chars Teaching Content
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Publishing Options */}
      <div className="review-section">
        <h3>Publishing Options</h3>
        <div className="visibility-options">
          <label className={`visibility-option ${visibility === 'private' ? 'selected' : ''}`}>
            <input
              type="radio"
              name="visibility"
              value="private"
              checked={visibility === 'private'}
              onChange={(e) => setVisibility(e.target.value)}
            />
            <div className="option-content">
              <div className="option-title">🔒 Private</div>
              <div className="option-description">Only you can access this course</div>
            </div>
          </label>

          <label className={`visibility-option ${visibility === 'unlisted' ? 'selected' : ''}`}>
            <input
              type="radio"
              name="visibility"
              value="unlisted"
              checked={visibility === 'unlisted'}
              onChange={(e) => setVisibility(e.target.value)}
            />
            <div className="option-content">
              <div className="option-title">🔗 Unlisted</div>
              <div className="option-description">Anyone with the link can access</div>
            </div>
          </label>

          <label className={`visibility-option ${visibility === 'public' ? 'selected' : ''}`}>
            <input
              type="radio"
              name="visibility"
              value="public"
              checked={visibility === 'public'}
              onChange={(e) => setVisibility(e.target.value)}
              disabled
            />
            <div className="option-content">
              <div className="option-title">🌍 Public (Coming Soon)</div>
              <div className="option-description">Searchable in course library</div>
            </div>
          </label>
        </div>
      </div>

      {/* Preview Note */}
      <div className="preview-note">
        <p>💡 After publishing, you can preview your course and make edits before sharing with learners.</p>
      </div>

      <div className="wizard-actions">
        <div className="left-actions">
          <button onClick={onBack} className="wizard-button secondary">
            ← Back to Content
          </button>
        </div>
        <div className="right-actions">
          <button onClick={onSaveDraft} className="wizard-button secondary">
            Save Draft
          </button>
          <button
            onClick={handlePublish}
            className="wizard-button primary"
            disabled={isPublishing}
          >
            {isPublishing ? 'Publishing...' : 'Publish Course 🚀'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default CourseReview
