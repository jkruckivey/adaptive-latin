import { useState, useEffect } from 'react'
import { api } from '../api'
import './LearnerProfileReport.css'

function LearnerProfileReport({ learnerId }) {
  const [profileData, setProfileData] = useState(null)
  const [isExpanded, setIsExpanded] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadProfile = async () => {
    if (!learnerId) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await api.getLearnerModel(learnerId)
      if (response.success) {
        setProfileData(response.learner_model)
      } else {
        setError('Failed to load profile')
      }
    } catch (err) {
      console.error('Error loading profile:', err)
      setError('Connection error')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (isExpanded && !profileData) {
      loadProfile()
    }
  }, [isExpanded, learnerId])

  const profile = profileData?.profile || {}
  const priorKnowledge = profile.priorKnowledge || {}

  const grammarLabels = {
    loved: 'Enthusiastic about grammar',
    okay: 'Has basic grammar foundation',
    confused: 'Found grammar confusing',
    forgotten: 'Needs grammar refresher'
  }

  const styleLabels = {
    connections: 'Connections to prior knowledge',
    stories: 'Contextual learning through stories',
    patterns: 'Pattern recognition & systems',
    repetition: 'Practice & repetition'
  }

  return (
    <div className="profile-report">
      <div className="profile-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h3>Learner Profile Report</h3>
        <button className="expand-toggle">
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>

      {isExpanded && (
        <div className="profile-content">
          {isLoading && <div className="loading">Loading profile data...</div>}

          {error && <div className="error">{error}</div>}

          {profileData && (
            <>
              <div className="profile-section">
                <h4>Basic Information</h4>
                <div className="profile-item">
                  <span className="label">Learner ID:</span>
                  <span className="value">{profileData.learner_id}</span>
                </div>
                {profileData.learner_name && (
                  <div className="profile-item">
                    <span className="label">Name:</span>
                    <span className="value">{profileData.learner_name}</span>
                  </div>
                )}
                <div className="profile-item">
                  <span className="label">Created:</span>
                  <span className="value">{new Date(profileData.created_at).toLocaleString()}</span>
                </div>
              </div>

              {Object.keys(profile).length > 0 && (
                <>
                  <div className="profile-section">
                    <h4>Background & Motivation</h4>
                    <div className="profile-item">
                      <span className="value">{profile.background || 'Not provided'}</span>
                    </div>
                  </div>

                  <div className="profile-section">
                    <h4>Language Experience</h4>
                    <div className="profile-item">
                      <span className="label">Languages studied:</span>
                      <span className="value">{priorKnowledge.languageDetails || 'None specified'}</span>
                    </div>
                    {priorKnowledge.hasRomanceLanguage && (
                      <div className="profile-tag success">
                        ✓ Has studied Romance languages (Spanish/French)
                      </div>
                    )}
                    {priorKnowledge.hasInflectedLanguage && (
                      <div className="profile-tag success">
                        ✓ Has studied inflected languages (German)
                      </div>
                    )}
                  </div>

                  <div className="profile-section">
                    <h4>Grammar & Prior Knowledge</h4>
                    {profile.grammarExperience && (
                      <div className="profile-item">
                        <span className="label">Grammar comfort:</span>
                        <span className="value">{grammarLabels[profile.grammarExperience] || profile.grammarExperience}</span>
                      </div>
                    )}
                    {priorKnowledge.understandsSubjectObject !== undefined && (
                      <div className="profile-item">
                        <span className="label">Subject/Object understanding:</span>
                        <span className="value">
                          {String(priorKnowledge.understandsSubjectObject)}
                          ({priorKnowledge.subjectObjectConfidence || 'unknown'} confidence)
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="profile-section">
                    <h4>Learning Preferences</h4>
                    {profile.learningStyle && (
                      <div className="profile-item">
                        <span className="label">Preferred style:</span>
                        <span className="value">{styleLabels[profile.learningStyle] || profile.learningStyle}</span>
                      </div>
                    )}
                    {profile.interests && (
                      <div className="profile-item">
                        <span className="label">Interests:</span>
                        <span className="value">{profile.interests}</span>
                      </div>
                    )}
                  </div>

                  <div className="profile-section">
                    <h4>AI Personalization Context</h4>
                    <div className="personalization-info">
                      <p>The AI tutor uses this profile to:</p>
                      <ul>
                        {priorKnowledge.hasRomanceLanguage && (
                          <li>Connect Latin to Spanish/French you already know</li>
                        )}
                        {profile.learningStyle === 'narrative' && (
                          <li>Use story-based examples and contextual scenarios</li>
                        )}
                        {profile.learningStyle === 'varied' && (
                          <li>Mix different content types - tables, examples, and exercises</li>
                        )}
                        {profile.learningStyle === 'adaptive' && (
                          <li>Adjust content difficulty based on your performance patterns</li>
                        )}
                        {profile.interests && (
                          <li>Use examples related to {profile.interests.split(',')[0].trim()}</li>
                        )}
                        <li>Adapt difficulty based on your grammar comfort level</li>
                        <li>Adjust explanations based on what you already know</li>
                      </ul>
                    </div>
                  </div>

                  <div className="profile-section">
                    <h4>Raw JSON (for debugging)</h4>
                    <pre className="json-display">
                      {JSON.stringify(profile, null, 2)}
                    </pre>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default LearnerProfileReport
