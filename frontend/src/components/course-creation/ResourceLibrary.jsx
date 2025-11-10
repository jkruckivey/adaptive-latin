import { useState } from 'react'
import ComprehensionQuizBuilder from './ComprehensionQuizBuilder'
import './ResourceLibrary.css'

function ResourceLibrary({ courseData, onNext, onBack }) {
  const [sources, setSources] = useState(courseData.sources || [])
  const [newSourceUrl, setNewSourceUrl] = useState('')
  const [newSourceTitle, setNewSourceTitle] = useState('')
  const [newSourceDescription, setNewSourceDescription] = useState('')
  const [requirementLevel, setRequirementLevel] = useState('optional')
  const [verificationMethod, setVerificationMethod] = useState('none')
  const [verificationData, setVerificationData] = useState({
    comprehensionQuestions: [],
    discussionPrompt: '',
    attestationText: 'I have read and understood this material'
  })
  const [isAdding, setIsAdding] = useState(false)
  const [error, setError] = useState(null)
  const [selectedConcept, setSelectedConcept] = useState('course') // 'course' or concept index

  const handleAddSource = async () => {
    if (!newSourceUrl.trim()) {
      setError('URL is required')
      return
    }

    // Validate verification requirements
    if (requirementLevel === 'required' && verificationMethod === 'comprehension-quiz') {
      if (verificationData.comprehensionQuestions.length === 0) {
        setError('Please add at least one comprehension question for required materials')
        return
      }
      const hasEmptyQuestions = verificationData.comprehensionQuestions.some(q => !q.question.trim())
      if (hasEmptyQuestions) {
        setError('All comprehension questions must have question text')
        return
      }
    }

    if (requirementLevel === 'required' && verificationMethod === 'discussion-prompt') {
      if (!verificationData.discussionPrompt.trim()) {
        setError('Please provide a discussion prompt for required materials')
        return
      }
    }

    setIsAdding(true)
    setError(null)

    try {
      // For now, mock the metadata extraction
      // In production, this would call the backend API
      const mockMetadata = {
        id: `source-${Date.now()}`,
        url: newSourceUrl,
        title: newSourceTitle || extractTitleFromUrl(newSourceUrl),
        description: newSourceDescription || 'External resource',
        type: detectSourceType(newSourceUrl),
        added_at: new Date().toISOString(),
        status: 'ready',
        scope: selectedConcept === 'course' ? 'course' : `concept-${selectedConcept}`,
        requirementLevel: requirementLevel,
        verificationMethod: requirementLevel === 'required' ? verificationMethod : 'none',
        verificationData: requirementLevel === 'required' && verificationMethod !== 'none'
          ? { ...verificationData }
          : null
      }

      setSources([...sources, mockMetadata])

      // Reset form
      setNewSourceUrl('')
      setNewSourceTitle('')
      setNewSourceDescription('')
      setRequirementLevel('optional')
      setVerificationMethod('none')
      setVerificationData({
        comprehensionQuestions: [],
        discussionPrompt: '',
        attestationText: 'I have read and understood this material'
      })
      setError(null)
    } catch (err) {
      setError('Failed to add source. Please check the URL and try again.')
    } finally {
      setIsAdding(false)
    }
  }

  const handleRemoveSource = (sourceId) => {
    setSources(sources.filter(s => s.id !== sourceId))
  }

  const handleNext = () => {
    // Save sources to course data
    onNext({ sources })
  }

  const detectSourceType = (url) => {
    const urlLower = url.toLowerCase()
    if (urlLower.includes('youtube.com') || urlLower.includes('youtu.be')) {
      return 'video'
    }
    if (urlLower.endsWith('.pdf')) {
      return 'pdf'
    }
    if (urlLower.match(/\.(jpg|jpeg|png|gif|svg|webp)$/)) {
      return 'image'
    }
    return 'website'
  }

  const extractTitleFromUrl = (url) => {
    try {
      const urlObj = new URL(url)
      return urlObj.hostname.replace('www.', '')
    } catch {
      return 'External Resource'
    }
  }

  const getSourceIcon = (type) => {
    switch (type) {
      case 'video': return ''
      case 'pdf': return ''
      case 'image': return ''
      case 'website': return ''
      default: return ''
    }
  }

  const getSourcesByScope = (scope) => {
    return sources.filter(s => s.scope === scope)
  }

  const getRequirementBadge = (level) => {
    switch (level) {
      case 'required':
        return { text: 'Required', className: 'badge-required' }
      case 'recommended':
        return { text: 'Recommended', className: 'badge-recommended' }
      case 'optional':
        return { text: 'Optional', className: 'badge-optional' }
      default:
        return { text: 'Optional', className: 'badge-optional' }
    }
  }

  const getVerificationBadge = (method) => {
    switch (method) {
      case 'comprehension-quiz':
        return 'Quiz Required'
      case 'discussion-prompt':
        return 'Discussion Required'
      case 'self-attestation':
        return 'Self-Attestation'
      default:
        return null
    }
  }

  const courseSources = getSourcesByScope('course')

  return (
    <div className="resource-library">
      <div className="resource-library-header">
        <h2>Resource Library</h2>
        <p>Add external sources that you want the AI to reference when creating course content</p>
      </div>

      <div className="resource-library-content">
        {/* Add New Source Form */}
        <div className="add-source-form">
          <h3>Add External Source</h3>

          <div className="form-group">
            <label>Attach to:</label>
            <select
              value={selectedConcept}
              onChange={(e) => setSelectedConcept(e.target.value)}
              className="scope-select"
            >
              <option value="course">Entire Course</option>
              {(courseData.concepts || []).map((concept, index) => (
                <option key={index} value={index}>
                  {concept.title || `Concept ${index + 1}`}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>URL *</label>
            <input
              type="url"
              value={newSourceUrl}
              onChange={(e) => setNewSourceUrl(e.target.value)}
              placeholder="https://example.com/resource"
              className="url-input"
            />
            <div className="input-hint">
              YouTube videos, websites, PDFs, images, etc.
            </div>
          </div>

          <div className="form-group">
            <label>Title (optional)</label>
            <input
              type="text"
              value={newSourceTitle}
              onChange={(e) => setNewSourceTitle(e.target.value)}
              placeholder="Custom title for this source"
            />
          </div>

          <div className="form-group">
            <label>Description (optional)</label>
            <textarea
              value={newSourceDescription}
              onChange={(e) => setNewSourceDescription(e.target.value)}
              placeholder="Brief description of what this source contains"
              rows={3}
            />
          </div>

          {/* Requirement Level */}
          <div className="form-group">
            <label>Requirement Level</label>
            <select
              value={requirementLevel}
              onChange={(e) => {
                setRequirementLevel(e.target.value)
                if (e.target.value !== 'required') {
                  setVerificationMethod('none')
                }
              }}
              className="requirement-select"
            >
              <option value="optional">Optional - Supplementary material</option>
              <option value="recommended">Recommended - Strongly suggested</option>
              <option value="required">Required - Must complete before accessing module</option>
            </select>
            <div className="input-hint">
              {requirementLevel === 'required' && 'Students must complete this before proceeding'}
              {requirementLevel === 'recommended' && 'Students will see this as recommended reading'}
              {requirementLevel === 'optional' && 'Students can access this at their discretion'}
            </div>
          </div>

          {/* Verification Method (only for required materials) */}
          {requirementLevel === 'required' && (
            <div className="form-group verification-section">
              <label>Verification Method *</label>
              <select
                value={verificationMethod}
                onChange={(e) => setVerificationMethod(e.target.value)}
                className="verification-select"
              >
                <option value="none">No Verification (honor system)</option>
                <option value="self-attestation">Self-Attestation (checkbox)</option>
                <option value="comprehension-quiz">Comprehension Quiz</option>
                <option value="discussion-prompt">Discussion Prompt</option>
              </select>
              <div className="input-hint">
                How will you verify that students have engaged with this material?
              </div>
            </div>
          )}

          {/* Self-Attestation Text */}
          {requirementLevel === 'required' && verificationMethod === 'self-attestation' && (
            <div className="form-group">
              <label>Attestation Text</label>
              <input
                type="text"
                value={verificationData.attestationText}
                onChange={(e) => setVerificationData({
                  ...verificationData,
                  attestationText: e.target.value
                })}
                placeholder="I have read and understood this material"
                className="attestation-input"
              />
              <div className="input-hint">
                Students will check a box confirming this statement
              </div>
            </div>
          )}

          {/* Discussion Prompt */}
          {requirementLevel === 'required' && verificationMethod === 'discussion-prompt' && (
            <div className="form-group">
              <label>Discussion Prompt *</label>
              <textarea
                value={verificationData.discussionPrompt}
                onChange={(e) => setVerificationData({
                  ...verificationData,
                  discussionPrompt: e.target.value
                })}
                placeholder="What are the key strategic issues facing the company in this case? How would you prioritize them?"
                rows={4}
                className="discussion-input"
              />
              <div className="input-hint">
                Students must respond to this prompt before continuing
              </div>
            </div>
          )}

          {/* Comprehension Quiz */}
          {requirementLevel === 'required' && verificationMethod === 'comprehension-quiz' && (
            <ComprehensionQuizBuilder
              questions={verificationData.comprehensionQuestions}
              onChange={(questions) => setVerificationData({
                ...verificationData,
                comprehensionQuestions: questions
              })}
            />
          )}

          {error && <div className="error-message">{error}</div>}

          <button
            onClick={handleAddSource}
            disabled={isAdding || !newSourceUrl.trim()}
            className="add-source-button"
          >
            {isAdding ? 'Adding...' : '+ Add Source'}
          </button>
        </div>

        {/* Sources List */}
        <div className="sources-list">
          <h3>Added Sources ({sources.length})</h3>

          {sources.length === 0 ? (
            <div className="empty-state">
              <p>No sources added yet</p>
              <p className="empty-hint">Sources are optional but help the AI create better content tailored to your materials</p>
            </div>
          ) : (
            <>
              {/* Course-level sources */}
              {courseSources.length > 0 && (
                <div className="source-group">
                  <h4>Course-Wide Sources</h4>
                  {courseSources.map((source) => (
                    <div key={source.id} className={`source-card requirement-${source.requirementLevel || 'optional'}`}>
                      <div className="source-icon">{getSourceIcon(source.type)}</div>
                      <div className="source-info">
                        <div className="source-header">
                          <div className="source-title">{source.title}</div>
                          <div className="source-badges">
                            <span className={`requirement-badge ${getRequirementBadge(source.requirementLevel || 'optional').className}`}>
                              {getRequirementBadge(source.requirementLevel || 'optional').text}
                            </span>
                            {source.verificationMethod && source.verificationMethod !== 'none' && (
                              <span className="verification-badge">
                                {getVerificationBadge(source.verificationMethod)}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="source-url">{source.url}</div>
                        {source.description && (
                          <div className="source-description">{source.description}</div>
                        )}
                        {source.requirementLevel === 'required' && source.verificationMethod === 'comprehension-quiz' && (
                          <div className="quiz-info">
                            {source.verificationData?.comprehensionQuestions?.length || 0} comprehension question(s)
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => handleRemoveSource(source.id)}
                        className="remove-source-button"
                        title="Remove source"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Concept-specific sources */}
              {(courseData.concepts || []).map((concept, index) => {
                const conceptSources = getSourcesByScope(`concept-${index}`)
                if (conceptSources.length === 0) return null

                return (
                  <div key={index} className="source-group">
                    <h4>{concept.title || `Concept ${index + 1}`}</h4>
                    {conceptSources.map((source) => (
                      <div key={source.id} className={`source-card requirement-${source.requirementLevel || 'optional'}`}>
                        <div className="source-icon">{getSourceIcon(source.type)}</div>
                        <div className="source-info">
                          <div className="source-header">
                            <div className="source-title">{source.title}</div>
                            <div className="source-badges">
                              <span className={`requirement-badge ${getRequirementBadge(source.requirementLevel || 'optional').className}`}>
                                {getRequirementBadge(source.requirementLevel || 'optional').text}
                              </span>
                              {source.verificationMethod && source.verificationMethod !== 'none' && (
                                <span className="verification-badge">
                                  {getVerificationBadge(source.verificationMethod)}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="source-url">{source.url}</div>
                          {source.description && (
                            <div className="source-description">{source.description}</div>
                          )}
                          {source.requirementLevel === 'required' && source.verificationMethod === 'comprehension-quiz' && (
                            <div className="quiz-info">
                              {source.verificationData?.comprehensionQuestions?.length || 0} comprehension question(s)
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => handleRemoveSource(source.id)}
                          className="remove-source-button"
                          title="Remove source"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )
              })}
            </>
          )}
        </div>
      </div>

      <div className="resource-library-actions">
        <button onClick={onBack} className="secondary-button">
          ← Back
        </button>
        <button onClick={handleNext} className="primary-button">
          Continue to Content Creation →
        </button>
      </div>
    </div>
  )
}

export default ResourceLibrary
