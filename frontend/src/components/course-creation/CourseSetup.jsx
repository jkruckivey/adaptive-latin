import { useState, useEffect } from 'react'
import { api } from '../../api'
import TaxonomySelector from './TaxonomySelector'
import LearningOutcomeBuilder from './LearningOutcomeBuilder'

function CourseSetup({ courseData, onNext, onCancel, onSaveDraft }) {
  const [formData, setFormData] = useState({
    title: courseData.title || '',
    domain: courseData.domain || '',
    taxonomy: courseData.taxonomy || 'blooms',
    courseLearningOutcomes: courseData.courseLearningOutcomes || ['', '', '']
  })

  const [errors, setErrors] = useState({})
  const [generatingSuggestions, setGeneratingSuggestions] = useState(false)

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

  const handleGenerateSuggestions = async () => {
    if (!formData.title || !formData.domain) {
      alert('Please enter a course title and select a domain first')
      return
    }

    setGeneratingSuggestions(true)
    try {
      const response = await api.generateLearningOutcomes(
        formData.title,
        formData.domain,
        formData.taxonomy
      )

      if (response.success && response.outcomes) {
        // Update the courseLearningOutcomes with the generated suggestions
        setFormData(prev => ({
          ...prev,
          courseLearningOutcomes: response.outcomes
        }))
      }
    } catch (error) {
      console.error('Error generating suggestions:', error)
      alert(`Failed to generate suggestions: ${error.message}`)
    } finally {
      setGeneratingSuggestions(false)
    }
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
        Let's start by defining your course and its learning outcomes using Quality Matters standards.
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
          description="What will students be able to do after completing this entire course? Write 3-5 broad, measurable outcomes."
          onGenerateSuggestions={handleGenerateSuggestions}
          isGenerating={generatingSuggestions}
        />
        {errors.courseLearningOutcomes && (
          <div className="validation-error">{errors.courseLearningOutcomes}</div>
        )}
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
