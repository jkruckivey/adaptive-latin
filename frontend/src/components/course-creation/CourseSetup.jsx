import { useState, useEffect } from 'react'
import { api } from '../../api'
import TaxonomySelector from './TaxonomySelector'
import LearningOutcomeBuilder from './LearningOutcomeBuilder'
import LearningOutcomeGenerator from './LearningOutcomeGenerator'

function CourseSetup({ courseData, onNext, onCancel, onSaveDraft }) {
  const [formData, setFormData] = useState({
    title: courseData.title || '',
    domain: courseData.domain || '',
    description: courseData.description || '',
    targetAudience: courseData.targetAudience || '',
    taxonomy: courseData.taxonomy || 'blooms',
    courseLearningOutcomes: courseData.courseLearningOutcomes || ['', '', '']
  })

  const [errors, setErrors] = useState({})
  const [showGenerator, setShowGenerator] = useState(false)

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

    // Validate Course Learning Outcomes
    const validOutcomes = formData.courseLearningOutcomes.filter(o => o.trim())
    if (validOutcomes.length < 3) {
      newErrors.courseLearningOutcomes = 'At least 3 course learning outcomes are required'
    } else if (validOutcomes.length > 5) {
      newErrors.courseLearningOutcomes = 'Maximum 5 course learning outcomes allowed'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleGenerateSuggestions = () => {
    if (!formData.title || !formData.domain) {
      alert('Please enter a course title and select a domain first')
      return
    }

    setShowGenerator(true)
  }

  const handleAcceptOutcomes = (outcomes) => {
    setFormData(prev => ({
      ...prev,
      courseLearningOutcomes: outcomes
    }))
    setShowGenerator(false)
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
        Let's start by defining your course and its learning outcomes using best practices for effective course design.
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
        <label>Course Description</label>
        <textarea
          value={formData.description}
          onChange={(e) => handleChange('description', e.target.value)}
          placeholder="Brief description of the course content and objectives..."
          rows={3}
        />
        <div className="hint">Optional: Helps AI generate better learning outcomes</div>
      </div>

      <div className="form-group">
        <label>Target Audience</label>
        <input
          type="text"
          value={formData.targetAudience}
          onChange={(e) => handleChange('targetAudience', e.target.value)}
          placeholder="e.g., Undergraduate students, Professionals, Beginners"
        />
        <div className="hint">Optional: Who is this course designed for?</div>
      </div>

      {/* Taxonomy Selection */}
      <TaxonomySelector
        selectedTaxonomy={formData.taxonomy}
        onSelect={(taxonomy) => handleChange('taxonomy', taxonomy)}
      />

      {/* Course Learning Outcomes */}
      <div className="form-group">
        <LearningOutcomeBuilder
          outcomes={formData.courseLearningOutcomes}
          onChange={(outcomes) => handleChange('courseLearningOutcomes', outcomes)}
          taxonomy={formData.taxonomy}
          domain={formData.domain}
          courseTitle={formData.title}
          minOutcomes={3}
          maxOutcomes={5}
          label="Course Learning Outcomes (CLOs)"
          description="Course-level outcomes describe what students will be able to do upon completing the entire course. These are broad, overarching goals that encompass the full scope of learning. Module outcomes will align with and support these CLOs."
          onGenerateSuggestions={handleGenerateSuggestions}
          isGenerating={false}
        />
        {errors.courseLearningOutcomes && (
          <div className="validation-error">{errors.courseLearningOutcomes}</div>
        )}
      </div>

      {/* Generator Modal */}
      {showGenerator && (
        <div className="modal-overlay" onClick={() => setShowGenerator(false)}>
          <div className="modal-content large" onClick={(e) => e.stopPropagation()}>
            <LearningOutcomeGenerator
              description={`Course: ${formData.title}\nDomain: ${formData.domain}\n${formData.description ? `Description: ${formData.description}\n` : ''}${formData.targetAudience ? `Target Audience: ${formData.targetAudience}` : ''}`}
              taxonomy={formData.taxonomy}
              level="course"
              existingOutcomes={formData.courseLearningOutcomes.filter(o => o.trim())}
              onAccept={handleAcceptOutcomes}
              onCancel={() => setShowGenerator(false)}
            />
          </div>
        </div>
      )}

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
