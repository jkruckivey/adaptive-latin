import { useState } from 'react'
import { api } from '../../api'
import './CourseReview.css'

function CourseReview({ courseData, onBack, onPublish, onSaveDraft }) {
  const [visibility, setVisibility] = useState('unlisted')
  const [isPublishing, setIsPublishing] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  const handlePublish = async () => {
    setIsPublishing(true)
    try {
      await onPublish({ ...courseData, visibility })
    } catch (error) {
      alert('Failed to publish course. Please try again.')
      setIsPublishing(false)
    }
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      // Generate a temporary course ID for export
      const tempCourseId = courseData.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')

      // Create a temporary export structure matching what the backend expects
      const exportData = {
        export_version: "1.0",
        exported_at: new Date().toISOString(),
        course: {
          course_id: tempCourseId,
          title: courseData.title,
          domain: courseData.domain,
          taxonomy: courseData.taxonomy || 'blooms',
          course_learning_outcomes: courseData.courseLearningOutcomes || [],
          description: courseData.description,
          target_audience: courseData.targetAudience,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        modules: (courseData.modules || []).map(module => ({
          id: module.moduleId,
          title: module.title,
          module_learning_outcomes: module.moduleLearningOutcomes || [],
          concepts: (module.concepts || []).map(concept => ({
            concept_id: concept.conceptId,
            title: concept.title,
            learning_objectives: concept.learningObjectives || [],
            prerequisites: concept.prerequisites || []
          }))
        })),
        external_resources: []
      }

      // Create and download JSON file
      const blob = new Blob([JSON.stringify({ export: exportData }, null, 2)], {
        type: 'application/json'
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${tempCourseId}-export-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      alert('Course exported successfully!')
    } catch (error) {
      console.error('Export error:', error)
      alert('Failed to export course. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  const getConceptStats = (concept) => {
    const vocab = (concept.vocabulary || []).filter(v => v.term && v.definition).length
    const contentLength = (concept.teachingContent || '').length

    return { vocab, contentLength }
  }

  // Flatten concepts from modules with module context
  const getAllConcepts = () => {
    return (courseData.modules || []).flatMap((module, moduleIndex) =>
      (module.concepts || []).map((concept, conceptIndex) => ({
        ...concept,
        moduleTitle: module.title,
        moduleIndex: moduleIndex + 1,
        conceptIndex: conceptIndex + 1
      }))
    )
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
          <span className="review-label">Learning Framework:</span>
          <span className="review-value">
            {courseData.taxonomy === 'blooms' ? "Bloom's Taxonomy" :
             courseData.taxonomy === 'finks' ? "Fink's Taxonomy" :
             "Both Frameworks"}
          </span>
        </div>
        {/* Backward compatibility for old courses */}
        {courseData.description && (
          <div className="review-item">
            <span className="review-label">Description:</span>
            <span className="review-value description">{courseData.description}</span>
          </div>
        )}
        {courseData.targetAudience && (
          <div className="review-item">
            <span className="review-label">Target Audience:</span>
            <span className="review-value">{courseData.targetAudience}</span>
          </div>
        )}
      </div>

      {/* Course Learning Outcomes */}
      {courseData.courseLearningOutcomes && courseData.courseLearningOutcomes.filter(o => o.trim()).length > 0 && (
        <div className="review-section">
          <h3>Course Learning Outcomes (CLOs)</h3>
          <ul className="outcomes-list">
            {courseData.courseLearningOutcomes.filter(o => o.trim()).map((outcome, i) => (
              <li key={i} className="outcome-item">{outcome}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Required Materials */}
      {courseData.sources && courseData.sources.filter(s => s.requirementLevel === 'required').length > 0 && (
        <div className="review-section required-materials-section">
          <h3>Required Materials ({courseData.sources.filter(s => s.requirementLevel === 'required').length})</h3>
          <p className="section-note">Students must complete these materials before accessing modules</p>
          <div className="required-materials-list">
            {courseData.sources.filter(s => s.requirementLevel === 'required').map((source, i) => (
              <div key={i} className="required-material-card">
                <div className="material-header">
                  <span className="material-icon"></span>
                  <div className="material-info">
                    <div className="material-title">{source.title}</div>
                    <div className="material-url">{source.url}</div>
                    {source.scope !== 'course' && (
                      <div className="material-scope">
                        Scoped to: {source.scope}
                      </div>
                    )}
                  </div>
                </div>
                {source.verificationMethod && source.verificationMethod !== 'none' && (
                  <div className="verification-info">
                    <strong>Verification:</strong> {
                      source.verificationMethod === 'comprehension-quiz' ? `Comprehension Quiz (${source.verificationData?.comprehensionQuestions?.length || 0} questions)` :
                      source.verificationMethod === 'discussion-prompt' ? 'Discussion Prompt Required' :
                      source.verificationMethod === 'self-attestation' ? 'Self-Attestation' :
                      'None'
                    }
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modules & Concepts Summary */}
      <div className="review-section">
        <h3>Course Structure</h3>
        {(courseData.modules || []).map((module, moduleIndex) => (
          <div key={moduleIndex} className="module-summary">
            <div className="module-header">
              <h4>Module {moduleIndex + 1}: {module.title}</h4>
              <span className="concept-count">
                {(module.concepts || []).length} concept{(module.concepts || []).length !== 1 ? 's' : ''}
              </span>
            </div>

            {(module.concepts || []).map((concept, conceptIndex) => {
              const stats = getConceptStats(concept)
              const isComplete = stats.vocab >= 5 && stats.contentLength >= 500

              return (
                <div key={conceptIndex} className={`concept-summary ${isComplete ? 'complete' : 'incomplete'}`}>
                  <div className="concept-summary-header">
                    <span className="concept-number">{moduleIndex + 1}.{conceptIndex + 1}</span>
                    <span className="concept-title">{concept.title}</span>
                    {isComplete ? (
                      <span className="status-badge complete">✓ Complete</span>
                    ) : (
                      <span className="status-badge incomplete">⚠ Incomplete</span>
                    )}
                  </div>
                  <div className="concept-stats">
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
        ))}
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
              <div className="option-title">Private</div>
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
              <div className="option-title">Unlisted</div>
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
              <div className="option-title">Public (Coming Soon)</div>
              <div className="option-description">Searchable in course library</div>
            </div>
          </label>
        </div>
      </div>

      {/* Preview Note */}
      <div className="preview-note">
        <p>After publishing, you can preview your course and make edits before sharing with learners.</p>
      </div>

      <div className="wizard-actions">
        <div className="left-actions">
          <button onClick={onBack} className="wizard-button secondary">
            ← Back to Content
          </button>
        </div>
        <div className="right-actions">
          <button
            onClick={handleExport}
            className="wizard-button secondary"
            disabled={isExporting}
            title="Export course as JSON file for backup or sharing"
          >
            {isExporting ? 'Exporting...' : '📥 Export JSON'}
          </button>
          <button onClick={onSaveDraft} className="wizard-button secondary">
            Save Draft
          </button>
          <button
            onClick={handlePublish}
            className="wizard-button primary"
            disabled={isPublishing}
          >
            {isPublishing ? 'Publishing...' : 'Publish Course'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default CourseReview
