import { useState } from 'react'
import './DialogueQuestion.css'

function DialogueQuestion({ question, context, onSubmit, isLoading }) {
  const [answer, setAnswer] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (answer.trim() && !isLoading) {
      onSubmit(answer)
    }
  }

  return (
    <div className="dialogue-question">
      {context && (
        <div className="dialogue-context">
          <div className="context-label">Context:</div>
          <div className="context-text">{context}</div>
        </div>
      )}

      <div className="dialogue-prompt">
        <h2>{question}</h2>
      </div>

      <form onSubmit={handleSubmit} className="dialogue-form">
        <textarea
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Type your answer here..."
          className="dialogue-input"
          rows={4}
          disabled={isLoading}
        />

        <button
          type="submit"
          className="submit-button"
          disabled={!answer.trim() || isLoading}
        >
          {isLoading ? 'Evaluating...' : 'Submit Answer'}
        </button>
      </form>
    </div>
  )
}

export default DialogueQuestion
