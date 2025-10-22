import { useState } from 'react'
import './FillBlank.css'

function FillBlank({ sentence, blanks, onSubmit, isLoading }) {
  const [answers, setAnswers] = useState(Array(blanks.length).fill(''))

  const handleChange = (index, value) => {
    const newAnswers = [...answers]
    newAnswers[index] = value
    setAnswers(newAnswers)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (answers.every(a => a.trim()) && !isLoading) {
      onSubmit(answers)
    }
  }

  const renderSentence = () => {
    const parts = sentence.split('___')
    return parts.map((part, index) => (
      <span key={index}>
        {part}
        {index < parts.length - 1 && (
          <input
            type="text"
            value={answers[index]}
            onChange={(e) => handleChange(index, e.target.value)}
            className="fill-blank-input"
            placeholder="..."
            disabled={isLoading}
          />
        )}
      </span>
    ))
  }

  return (
    <div className="fill-blank">
      <h2 className="fill-blank-title">Fill in the blanks:</h2>

      <form onSubmit={handleSubmit} className="fill-blank-form">
        <div className="fill-blank-sentence">
          {renderSentence()}
        </div>

        {blanks.length > 0 && (
          <div className="fill-blank-hints">
            <div className="hints-label">Hints:</div>
            {blanks.map((hint, index) => (
              <div key={index} className="hint-item">
                Blank {index + 1}: {hint}
              </div>
            ))}
          </div>
        )}

        <button
          type="submit"
          className="submit-button"
          disabled={!answers.every(a => a.trim()) || isLoading}
        >
          {isLoading ? 'Checking...' : 'Submit Answers'}
        </button>
      </form>
    </div>
  )
}

export default FillBlank
