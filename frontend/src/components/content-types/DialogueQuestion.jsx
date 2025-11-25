import { useState } from 'react'
import './DialogueQuestion.css'

function DialogueQuestion({ question, context, onSubmit, isLoading }) {
  const [answer, setAnswer] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (answer.trim() && !isLoading) {
      onSubmit(answer.trim())
    }
  }

  const handleKeyDown = (e) => {
    // Submit on Ctrl+Enter or Cmd+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e)
    }
  }

  return (
    <div className="dialogue-question">
      <div className="dialogue-header">
        <div className="dialogue-icon">💬</div>
        <h2>Socratic Dialogue</h2>
        <p className="dialogue-subtitle">Let's explore this concept together through discussion</p>
      </div>

      <div className="dialogue-body">
        {/* Tutor's question */}
        <div className="tutor-message">
          <div className="message-avatar tutor-avatar">🏛️</div>
          <div className="message-bubble">
            {context && (
              <div className="message-context">
                <span className="context-label">Context:</span> {context}
              </div>
            )}
            <div className="message-content">
              {question}
            </div>
          </div>
        </div>

        {/* Response form */}
        <form onSubmit={handleSubmit} className="dialogue-form">
          <div className="input-wrapper">
            <div className="learner-indicator">
              <div className="message-avatar learner-avatar">👤</div>
              <span>Your response:</span>
            </div>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Share your thinking here... Explain your reasoning in your own words."
              className="dialogue-input"
              rows={5}
              disabled={isLoading}
              autoFocus
            />
            <div className="input-hint">
              <span className="hint-icon">💡</span>
              <span>There's no single right answer - I want to understand your thinking. Explain as clearly as you can.</span>
            </div>
          </div>

          <button
            type="submit"
            className="submit-button"
            disabled={!answer.trim() || isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Evaluating your response...
              </>
            ) : (
              <>
                <span className="send-icon">📤</span>
                Submit Response
              </>
            )}
          </button>

          <p className="keyboard-hint">Press Ctrl+Enter to submit</p>
        </form>
      </div>
    </div>
  )
}

export default DialogueQuestion
