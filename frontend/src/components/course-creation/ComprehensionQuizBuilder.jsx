import { useState } from 'react'
import './ComprehensionQuizBuilder.css'

function ComprehensionQuizBuilder({ questions, onChange }) {
  const addQuestion = () => {
    onChange([
      ...questions,
      {
        question: '',
        type: 'multiple-choice',
        options: ['', '', '', ''],
        correctAnswer: 0,
        explanation: ''
      }
    ])
  }

  const updateQuestion = (index, field, value) => {
    const updated = [...questions]
    updated[index] = { ...updated[index], [field]: value }
    onChange(updated)
  }

  const updateOption = (questionIndex, optionIndex, value) => {
    const updated = [...questions]
    updated[questionIndex].options[optionIndex] = value
    onChange(updated)
  }

  const removeQuestion = (index) => {
    onChange(questions.filter((_, i) => i !== index))
  }

  const addOption = (questionIndex) => {
    const updated = [...questions]
    updated[questionIndex].options.push('')
    onChange(updated)
  }

  const removeOption = (questionIndex, optionIndex) => {
    const updated = [...questions]
    updated[questionIndex].options = updated[questionIndex].options.filter((_, i) => i !== optionIndex)
    // Adjust correct answer if needed
    if (updated[questionIndex].correctAnswer >= updated[questionIndex].options.length) {
      updated[questionIndex].correctAnswer = Math.max(0, updated[questionIndex].options.length - 1)
    }
    onChange(updated)
  }

  return (
    <div className="comprehension-quiz-builder">
      <div className="quiz-header">
        <h4>Comprehension Questions</h4>
        <p className="quiz-description">
          Students must answer these questions correctly to verify they've engaged with the material
        </p>
      </div>

      {questions.map((question, qIndex) => (
        <div key={qIndex} className="question-builder">
          <div className="question-header">
            <h5>Question {qIndex + 1}</h5>
            <button
              onClick={() => removeQuestion(qIndex)}
              className="remove-question-btn"
              title="Remove question"
            >
              Remove
            </button>
          </div>

          <div className="form-group">
            <label>Question Text *</label>
            <textarea
              value={question.question}
              onChange={(e) => updateQuestion(qIndex, 'question', e.target.value)}
              placeholder="What is the main issue facing the company in this case?"
              rows={2}
              className="question-input"
            />
          </div>

          <div className="form-group">
            <label>Question Type</label>
            <select
              value={question.type}
              onChange={(e) => updateQuestion(qIndex, 'type', e.target.value)}
              className="type-select"
            >
              <option value="multiple-choice">Multiple Choice</option>
              <option value="true-false">True/False</option>
              <option value="short-answer">Short Answer</option>
            </select>
          </div>

          {question.type === 'multiple-choice' && (
            <div className="form-group">
              <label>Answer Options *</label>
              {question.options.map((option, oIndex) => (
                <div key={oIndex} className="option-row">
                  <input
                    type="radio"
                    name={`correct-${qIndex}`}
                    checked={question.correctAnswer === oIndex}
                    onChange={() => updateQuestion(qIndex, 'correctAnswer', oIndex)}
                    className="correct-radio"
                    title="Mark as correct answer"
                  />
                  <input
                    type="text"
                    value={option}
                    onChange={(e) => updateOption(qIndex, oIndex, e.target.value)}
                    placeholder={`Option ${oIndex + 1}`}
                    className="option-input"
                  />
                  {question.options.length > 2 && (
                    <button
                      onClick={() => removeOption(qIndex, oIndex)}
                      className="remove-option-btn"
                      title="Remove option"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              {question.options.length < 6 && (
                <button
                  onClick={() => addOption(qIndex)}
                  className="add-option-btn"
                >
                  + Add Option
                </button>
              )}
              <div className="hint">Select the radio button next to the correct answer</div>
            </div>
          )}

          {question.type === 'true-false' && (
            <div className="form-group">
              <label>Correct Answer *</label>
              <div className="true-false-options">
                <label className="radio-label">
                  <input
                    type="radio"
                    name={`tf-${qIndex}`}
                    checked={question.correctAnswer === 'true'}
                    onChange={() => updateQuestion(qIndex, 'correctAnswer', 'true')}
                  />
                  <span>True</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name={`tf-${qIndex}`}
                    checked={question.correctAnswer === 'false'}
                    onChange={() => updateQuestion(qIndex, 'correctAnswer', 'false')}
                  />
                  <span>False</span>
                </label>
              </div>
            </div>
          )}

          {question.type === 'short-answer' && (
            <div className="form-group">
              <label>Expected Answer / Keywords</label>
              <textarea
                value={question.correctAnswer || ''}
                onChange={(e) => updateQuestion(qIndex, 'correctAnswer', e.target.value)}
                placeholder="Key points or keywords that should appear in the student's answer"
                rows={2}
                className="question-input"
              />
              <div className="hint">
                For short answer questions, the system will look for these keywords in student responses
              </div>
            </div>
          )}

          <div className="form-group">
            <label>Explanation (optional)</label>
            <textarea
              value={question.explanation || ''}
              onChange={(e) => updateQuestion(qIndex, 'explanation', e.target.value)}
              placeholder="Provide feedback or explanation after the student answers"
              rows={2}
              className="explanation-input"
            />
          </div>
        </div>
      ))}

      <button onClick={addQuestion} className="add-question-btn">
        + Add Question
      </button>

      {questions.length === 0 && (
        <div className="empty-state">
          <p>No comprehension questions yet. Add at least one question to verify student engagement.</p>
        </div>
      )}

      {questions.length > 0 && questions.length < 2 && (
        <div className="warning-message">
          Tip: We recommend 2-5 comprehension questions for required materials
        </div>
      )}
    </div>
  )
}

export default ComprehensionQuizBuilder
