import { useState, useEffect } from 'react'

function CourseSetup({ courseData, onNext, onCancel, onSaveDraft }) {
  const [formData, setFormData] = useState({
    title: courseData.title || '',
    domain: courseData.domain || '',
    description: courseData.description || '',
    targetAudience: courseData.targetAudience || ''
  })

  const [errors, setErrors] = useState({})

  const domains = [
    'Mathematics',
    'Science',
    'Language Learning',
    'History',
    'Programming',
    'Arts',
    'Music',
    'Business',
    'Health & Medicine',
    'Other'
  ]

  const targetAudiences = [
    'middle-school',
    'high-school',
    'college',
    'adult-learners',
    'professionals',
    'self-learners'
  ]

  const audienceLabels = {
    'middle-school': 'Middle School',
    'high-school': 'High School',
    'college': 'College/University',
    'adult-learners': 'Adult Learners',
    'professionals': 'Professionals',
    'self-learners': 'Self-Directed Learners'
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }))
    }
  }

  const validate = () => {
    const newErrors = {}

    if (!formData.title.trim()) {
      newErrors.title = 'Course title is required'
    } else if (formData.title.length < 5) {
      newErrors.title = 'Course title must be at least 5 characters'
    }

    if (!formData.domain) {
      newErrors.domain = 'Please select a subject area'
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Course description is required'
    } else if (formData.description.length < 50) {
      newErrors.description = 'Description must be at least 50 characters'
    }

    if (!formData.targetAudience) {
      newErrors.targetAudience = 'Please select a target audience'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleNext = () => {
    if (validate()) {
      onNext(formData)
    }
  }

  return (
    <div className="wizard-form">
      <h2>Create Your Course</h2>
      <p className="subtitle">
        Let's start with the basics. What are you teaching, and who are you teaching it to?
      </p>

      <div className="form-group">
        <label>
          Course Title <span className="required">*</span>
        </label>
        <input
          type="text"
          value={formData.title}
          onChange={(e) => handleChange('title', e.target.value)}
          placeholder="e.g., Introduction to Algebra, Spanish for Beginners"
          maxLength={100}
        />
        {errors.title && <div className="validation-error">{errors.title}</div>}
        <div className="hint">Choose a clear, descriptive title (5-100 characters)</div>
      </div>

      <div className="form-group">
        <label>
          Subject Area <span className="required">*</span>
        </label>
        <select
          value={formData.domain}
          onChange={(e) => handleChange('domain', e.target.value)}
        >
          <option value="">Select a subject...</option>
          {domains.map(domain => (
            <option key={domain} value={domain}>{domain}</option>
          ))}
        </select>
        {errors.domain && <div className="validation-error">{errors.domain}</div>}
      </div>

      <div className="form-group">
        <label>
          Course Description <span className="required">*</span>
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => handleChange('description', e.target.value)}
          placeholder="Describe what students will learn in this course. What skills will they gain? What topics will you cover?"
          rows={5}
          maxLength={1000}
        />
        {errors.description && <div className="validation-error">{errors.description}</div>}
        <div className="hint">
          {formData.description.length}/1000 characters (minimum 50)
        </div>
      </div>

      <div className="form-group">
        <label>
          Target Audience <span className="required">*</span>
        </label>
        <div className="radio-group">
          {targetAudiences.map(audience => (
            <label key={audience} className="radio-option">
              <input
                type="radio"
                name="targetAudience"
                value={audience}
                checked={formData.targetAudience === audience}
                onChange={(e) => handleChange('targetAudience', e.target.value)}
              />
              <span>{audienceLabels[audience]}</span>
            </label>
          ))}
        </div>
        {errors.targetAudience && <div className="validation-error">{errors.targetAudience}</div>}
      </div>

      <div className="wizard-actions">
        <div className="left-actions">
          <button
            onClick={onCancel}
            className="wizard-button secondary"
          >
            Cancel
          </button>
        </div>
        <div className="right-actions">
          <button
            onClick={onSaveDraft}
            className="wizard-button secondary"
          >
            Save Draft
          </button>
          <button
            onClick={handleNext}
            className="wizard-button primary"
          >
            Next: Plan Concepts →
          </button>
        </div>
      </div>
    </div>
  )
}

export default CourseSetup
