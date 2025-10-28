import { useState } from 'react'
import './ResourceLibrary.css'

function ResourceLibrary({ courseData, onNext, onBack }) {
  const [sources, setSources] = useState(courseData.sources || [])
  const [newSourceUrl, setNewSourceUrl] = useState('')
  const [newSourceTitle, setNewSourceTitle] = useState('')
  const [newSourceDescription, setNewSourceDescription] = useState('')
  const [isAdding, setIsAdding] = useState(false)
  const [error, setError] = useState(null)
  const [selectedConcept, setSelectedConcept] = useState('course') // 'course' or concept index

  const handleAddSource = async () => {
    if (!newSourceUrl.trim()) {
      setError('URL is required')
      return
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
        scope: selectedConcept === 'course' ? 'course' : `concept-${selectedConcept}`
      }

      setSources([...sources, mockMetadata])

      // Reset form
      setNewSourceUrl('')
      setNewSourceTitle('')
      setNewSourceDescription('')
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
      case 'video': return '🎥'
      case 'pdf': return '📄'
      case 'image': return '🖼️'
      case 'website': return '🌐'
      default: return '📎'
    }
  }

  const getSourcesByScope = (scope) => {
    return sources.filter(s => s.scope === scope)
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
                    <div key={source.id} className="source-card">
                      <div className="source-icon">{getSourceIcon(source.type)}</div>
                      <div className="source-info">
                        <div className="source-title">{source.title}</div>
                        <div className="source-url">{source.url}</div>
                        {source.description && (
                          <div className="source-description">{source.description}</div>
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
                      <div key={source.id} className="source-card">
                        <div className="source-icon">{getSourceIcon(source.type)}</div>
                        <div className="source-info">
                          <div className="source-title">{source.title}</div>
                          <div className="source-url">{source.url}</div>
                          {source.description && (
                            <div className="source-description">{source.description}</div>
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
