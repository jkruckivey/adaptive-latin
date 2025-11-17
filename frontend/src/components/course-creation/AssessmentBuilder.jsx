import { useState } from 'react'
import './AssessmentBuilder.css'

function AssessmentBuilder({
  assessments = [],
  onChange,
  taxonomy = 'blooms',
  learningOutcome = '',
  onGenerateAssessments,
  isGenerating = false
}) {
  const [selectedType, setSelectedType] = useState('dialogue')
  const [expandedAssessments, setExpandedAssessments] = useState([])

  // Add new assessment of selected type
  const addAssessment = () => {
    const newAssessment = createEmptyAssessment(selectedType)
    onChange([...assessments, newAssessment])
    setExpandedAssessments([...expandedAssessments, assessments.length])
  }

  // Create empty assessment based on type
  const createEmptyAssessment = (type) => {
    const baseId = `${type}-${Date.now()}`

    if (type === 'dialogue') {
      return {
        id: baseId,
        type: 'dialogue',
        difficulty: 'intermediate',
        prompt: '',
        rubric: {
          excellent: { threshold: 0.90, description: '' },
          good: { threshold: 0.75, description: '' },
          developing: { threshold: 0.60, description: '' },
          insufficient: { threshold: 0.00, description: '' }
        },
        followUp: ''
      }
    } else if (type === 'written') {
      return {
        id: baseId,
        type: 'written',
        difficulty: 'intermediate',
        prompt: '',
        wordCountRange: { min: 150, max: 300 },
        rubric: {
          dimensions: [
            { name: 'Accuracy', weight: 0.4, description: '' },
            { name: 'Clarity', weight: 0.3, description: '' },
            { name: 'Examples', weight: 0.3, description: '' }
          ]
        },
        estimatedTime: '15-20 minutes'
      }
    } else if (type === 'applied') {
      return {
        id: baseId,
        type: 'applied',
        difficulty: 'intermediate',
        taskType: 'translation',
        prompt: '',
        rubric: {
          scoring: '',
          correctAnswers: [],
          partialCredit: ''
        },
        estimatedTime: '15-20 minutes'
      }
    }
  }

  // Update specific assessment
  const updateAssessment = (index, field, value) => {
    const updated = assessments.map((a, i) =>
      i === index ? { ...a, [field]: value } : a
    )
    onChange(updated)
  }

  // Update nested rubric field
  const updateRubricField = (index, path, value) => {
    const updated = [...assessments]
    const assessment = { ...updated[index] }

    // Handle nested path (e.g., "rubric.excellent.description")
    const keys = path.split('.')
    let obj = assessment
    for (let i = 0; i < keys.length - 1; i++) {
      obj[keys[i]] = { ...obj[keys[i]] }
      obj = obj[keys[i]]
    }
    obj[keys[keys.length - 1]] = value

    updated[index] = assessment
    onChange(updated)
  }

  // Remove assessment
  const removeAssessment = (index) => {
    onChange(assessments.filter((_, i) => i !== index))
    setExpandedAssessments(expandedAssessments.filter(i => i !== index))
  }

  // Toggle assessment expansion
  const toggleAssessment = (index) => {
    setExpandedAssessments(prev =>
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    )
  }

  // Add correct answer to applied task
  const addCorrectAnswer = (assessmentIndex) => {
    const assessment = assessments[assessmentIndex]
    const updated = {
      ...assessment,
      rubric: {
        ...assessment.rubric,
        correctAnswers: [
          ...(assessment.rubric.correctAnswers || []),
          { form: '', answer: '', explanation: '' }
        ]
      }
    }
    onChange(assessments.map((a, i) => i === assessmentIndex ? updated : a))
  }

  // Update correct answer
  const updateCorrectAnswer = (assessmentIndex, answerIndex, field, value) => {
    const assessment = assessments[assessmentIndex]
    const answers = [...(assessment.rubric.correctAnswers || [])]
    answers[answerIndex] = { ...answers[answerIndex], [field]: value }

    const updated = {
      ...assessment,
      rubric: { ...assessment.rubric, correctAnswers: answers }
    }
    onChange(assessments.map((a, i) => i === assessmentIndex ? updated : a))
  }

  // Remove correct answer
  const removeCorrectAnswer = (assessmentIndex, answerIndex) => {
    const assessment = assessments[assessmentIndex]
    const answers = (assessment.rubric.correctAnswers || []).filter((_, i) => i !== answerIndex)

    const updated = {
      ...assessment,
      rubric: { ...assessment.rubric, correctAnswers: answers }
    }
    onChange(assessments.map((a, i) => i === assessmentIndex ? updated : a))
  }

  // Get assessment type label
  const getTypeLabel = (type) => {
    if (type === 'dialogue') return '💬 Dialogue'
    if (type === 'written') return '✍️ Written'
    if (type === 'applied') return '🎯 Applied'
    return type
  }

  // Get difficulty badge color
  const getDifficultyColor = (difficulty) => {
    if (difficulty === 'basic') return '#4CAF50'
    if (difficulty === 'intermediate') return '#FF9800'
    if (difficulty === 'advanced') return '#F44336'
    return '#757575'
  }

  return (
    <div className="assessment-builder">
      <div className="assessment-builder-header">
        <h3>Assessments</h3>
        <p className="section-description">
          Create assessments that match your learning outcome. Different assessment types test different cognitive levels.
        </p>
      </div>

      {/* AI Generation */}
      {learningOutcome && (
        <div className="ai-generation-section">
          <div className="outcome-context">
            <strong>Learning Outcome:</strong> {learningOutcome}
          </div>
          <button
            onClick={onGenerateAssessments}
            disabled={isGenerating}
            className="generate-button"
          >
            {isGenerating ? '⏳ Generating...' : '✨ Generate Assessments with AI'}
          </button>
          <p className="help-text">
            AI will analyze the action verb in your outcome and suggest appropriate assessment types
          </p>
        </div>
      )}

      {/* Assessment Type Selector */}
      <div className="assessment-type-selector">
        <label>Add Assessment:</label>
        <div className="type-buttons">
          <button
            onClick={() => setSelectedType('dialogue')}
            className={`type-button ${selectedType === 'dialogue' ? 'selected' : ''}`}
          >
            💬 Dialogue
            <span className="type-hint">Socratic Q&A</span>
          </button>
          <button
            onClick={() => setSelectedType('written')}
            className={`type-button ${selectedType === 'written' ? 'selected' : ''}`}
          >
            ✍️ Written
            <span className="type-hint">Extended Response</span>
          </button>
          <button
            onClick={() => setSelectedType('applied')}
            className={`type-button ${selectedType === 'applied' ? 'selected' : ''}`}
          >
            🎯 Applied
            <span className="type-hint">Performance Task</span>
          </button>
        </div>
        <button onClick={addAssessment} className="add-assessment-button">
          + Add {getTypeLabel(selectedType)} Assessment
        </button>
      </div>

      {/* Assessment List */}
      <div className="assessments-list">
        {assessments.length === 0 && (
          <div className="no-assessments">
            <p>No assessments yet. Add your first assessment above.</p>
          </div>
        )}

        {assessments.map((assessment, index) => (
          <div key={index} className="assessment-card">
            <div className="assessment-header">
              <button
                onClick={() => toggleAssessment(index)}
                className="toggle-button"
              >
                {expandedAssessments.includes(index) ? '▼' : '▶'}
              </button>
              <span className="assessment-type-badge">
                {getTypeLabel(assessment.type)}
              </span>
              <span
                className="difficulty-badge"
                style={{ backgroundColor: getDifficultyColor(assessment.difficulty) }}
              >
                {assessment.difficulty}
              </span>
              <span className="assessment-title">
                {assessment.prompt ? assessment.prompt.substring(0, 50) + '...' : 'Untitled Assessment'}
              </span>
              <button
                onClick={() => removeAssessment(index)}
                className="remove-button"
              >
                ×
              </button>
            </div>

            {expandedAssessments.includes(index) && (
              <div className="assessment-details">
                {/* Common Fields */}
                <div className="form-group">
                  <label>Difficulty Level</label>
                  <select
                    value={assessment.difficulty}
                    onChange={(e) => updateAssessment(index, 'difficulty', e.target.value)}
                  >
                    <option value="basic">Basic</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Prompt/Question <span className="required">*</span></label>
                  <textarea
                    value={assessment.prompt}
                    onChange={(e) => updateAssessment(index, 'prompt', e.target.value)}
                    placeholder="Enter the assessment prompt or question..."
                    rows={4}
                  />
                </div>

                {/* Type-Specific Fields */}
                {assessment.type === 'dialogue' && (
                  <>
                    <div className="rubric-section">
                      <h4>Rubric (AI will use this to grade responses)</h4>
                      {['excellent', 'good', 'developing', 'insufficient'].map(level => (
                        <div key={level} className="rubric-level">
                          <label>{level.charAt(0).toUpperCase() + level.slice(1)} (≥{assessment.rubric[level].threshold * 100}%)</label>
                          <textarea
                            value={assessment.rubric[level].description}
                            onChange={(e) => updateRubricField(index, `rubric.${level}.description`, e.target.value)}
                            placeholder={`What makes a ${level} response?`}
                            rows={2}
                          />
                        </div>
                      ))}
                    </div>

                    <div className="form-group">
                      <label>Follow-up Question (optional)</label>
                      <textarea
                        value={assessment.followUp || ''}
                        onChange={(e) => updateAssessment(index, 'followUp', e.target.value)}
                        placeholder="Ask a deeper question if student answers well..."
                        rows={2}
                      />
                    </div>
                  </>
                )}

                {assessment.type === 'written' && (
                  <>
                    <div className="form-group">
                      <label>Word Count Range</label>
                      <div className="word-count-inputs">
                        <input
                          type="number"
                          value={assessment.wordCountRange?.min || 150}
                          onChange={(e) => updateRubricField(index, 'wordCountRange.min', parseInt(e.target.value))}
                          placeholder="Min"
                        />
                        <span>to</span>
                        <input
                          type="number"
                          value={assessment.wordCountRange?.max || 300}
                          onChange={(e) => updateRubricField(index, 'wordCountRange.max', parseInt(e.target.value))}
                          placeholder="Max"
                        />
                      </div>
                    </div>

                    <div className="form-group">
                      <label>Estimated Time</label>
                      <input
                        type="text"
                        value={assessment.estimatedTime || ''}
                        onChange={(e) => updateAssessment(index, 'estimatedTime', e.target.value)}
                        placeholder="e.g., 15-20 minutes"
                      />
                    </div>

                    <div className="rubric-section">
                      <h4>Multi-Dimensional Rubric</h4>
                      <p className="help-text">Define how this response will be evaluated across multiple dimensions</p>
                      {(assessment.rubric.dimensions || []).map((dim, dimIndex) => (
                        <div key={dimIndex} className="rubric-dimension">
                          <input
                            type="text"
                            value={dim.name}
                            onChange={(e) => {
                              const dims = [...assessment.rubric.dimensions]
                              dims[dimIndex] = { ...dims[dimIndex], name: e.target.value }
                              updateRubricField(index, 'rubric.dimensions', dims)
                            }}
                            placeholder="Dimension name (e.g., Clarity)"
                          />
                          <input
                            type="number"
                            step="0.1"
                            max="1"
                            min="0"
                            value={dim.weight}
                            onChange={(e) => {
                              const dims = [...assessment.rubric.dimensions]
                              dims[dimIndex] = { ...dims[dimIndex], weight: parseFloat(e.target.value) }
                              updateRubricField(index, 'rubric.dimensions', dims)
                            }}
                            placeholder="Weight"
                          />
                          <textarea
                            value={dim.description}
                            onChange={(e) => {
                              const dims = [...assessment.rubric.dimensions]
                              dims[dimIndex] = { ...dims[dimIndex], description: e.target.value }
                              updateRubricField(index, 'rubric.dimensions', dims)
                            }}
                            placeholder="What are you looking for in this dimension?"
                            rows={2}
                          />
                        </div>
                      ))}
                    </div>
                  </>
                )}

                {assessment.type === 'applied' && (
                  <>
                    <div className="form-group">
                      <label>Task Type</label>
                      <select
                        value={assessment.taskType || 'translation'}
                        onChange={(e) => updateAssessment(index, 'taskType', e.target.value)}
                      >
                        <option value="translation">Translation</option>
                        <option value="form_identification">Form Identification</option>
                        <option value="form_production">Form Production</option>
                        <option value="problem_solving">Problem Solving</option>
                        <option value="case_study">Case Study</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>Estimated Time</label>
                      <input
                        type="text"
                        value={assessment.estimatedTime || ''}
                        onChange={(e) => updateAssessment(index, 'estimatedTime', e.target.value)}
                        placeholder="e.g., 15-20 minutes"
                      />
                    </div>

                    <div className="rubric-section">
                      <h4>Rubric</h4>

                      <div className="form-group">
                        <label>Scoring Method</label>
                        <textarea
                          value={assessment.rubric.scoring || ''}
                          onChange={(e) => updateRubricField(index, 'rubric.scoring', e.target.value)}
                          placeholder="How is this task scored? (e.g., Each question worth 0.2 points, 5 questions = 1.0)"
                          rows={2}
                        />
                      </div>

                      <div className="form-group">
                        <label>Partial Credit Policy</label>
                        <textarea
                          value={assessment.rubric.partialCredit || ''}
                          onChange={(e) => updateRubricField(index, 'rubric.partialCredit', e.target.value)}
                          placeholder="How is partial credit awarded?"
                          rows={2}
                        />
                      </div>

                      <div className="correct-answers-section">
                        <h5>Correct Answers / Answer Key</h5>
                        {(assessment.rubric.correctAnswers || []).map((answer, answerIndex) => (
                          <div key={answerIndex} className="correct-answer-item">
                            <input
                              type="text"
                              value={answer.form}
                              onChange={(e) => updateCorrectAnswer(index, answerIndex, 'form', e.target.value)}
                              placeholder="Question/Form (e.g., Question 1)"
                            />
                            <input
                              type="text"
                              value={answer.answer}
                              onChange={(e) => updateCorrectAnswer(index, answerIndex, 'answer', e.target.value)}
                              placeholder="Correct answer"
                            />
                            <textarea
                              value={answer.explanation}
                              onChange={(e) => updateCorrectAnswer(index, answerIndex, 'explanation', e.target.value)}
                              placeholder="Explanation or key points"
                              rows={2}
                            />
                            <button
                              onClick={() => removeCorrectAnswer(index, answerIndex)}
                              className="remove-button"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                        <button
                          onClick={() => addCorrectAnswer(index)}
                          className="add-button"
                        >
                          + Add Answer Key Item
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Assessment Summary */}
      {assessments.length > 0 && (
        <div className="assessment-summary">
          <strong>Total Assessments:</strong> {assessments.length}
          ({assessments.filter(a => a.type === 'dialogue').length} Dialogue,
          {assessments.filter(a => a.type === 'written').length} Written,
          {assessments.filter(a => a.type === 'applied').length} Applied)
        </div>
      )}
    </div>
  )
}

export default AssessmentBuilder
