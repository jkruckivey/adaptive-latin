import { useState } from 'react'
import './DiscussionPrompt.css'

function DiscussionPrompt({ prompt, onComplete, materialTitle }) {
  const [response, setResponse] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const minLength = 100 // Minimum 100 characters
  const isValid = response.trim().length >= minLength

  const handleSubmit = () => {
    if (isValid) {
      setSubmitted(true)
      // In a real app, you'd send this to the backend
      // For now, we just mark as complete after a brief delay
      setTimeout(() => {
        onComplete()
      }, 1500)
    }
  }

  if (submitted) {
    return (
      <div className="discussion-submitted">
        <div className="success-icon">✓</div>
        <h3>Response Submitted!</h3>
        <p>Thank you for your thoughtful response.</p>
        <div className="submitted-response">
          <h4>Your Response:</h4>
          <p>{response}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="discussion-prompt">
      <div className="prompt-header">
        <h3>Discussion Prompt</h3>
        <p className="prompt-instruction">
          Please respond to the following prompt based on the material you reviewed:
        </p>
      </div>

      <div className="prompt-box">
        <p className="prompt-text">{prompt}</p>
      </div>

      <div className="response-section">
        <label htmlFor="response">Your Response</label>
        <textarea
          id="response"
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          placeholder="Share your thoughts, analysis, and insights here..."
          rows={10}
          className="response-textarea"
        />
        <div className="char-counter">
          <span className={response.length >= minLength ? 'valid' : 'invalid'}>
            {response.length}
          </span>
          {' / '}
          {minLength} characters minimum
        </div>
      </div>

      <div className="prompt-actions">
        <button
          onClick={handleSubmit}
          disabled={!isValid}
          className="submit-response-button"
        >
          Submit Response
        </button>
      </div>

      <div className="prompt-hints">
        <p><strong>Tips for a good response:</strong></p>
        <ul>
          <li>Reference specific details from the material</li>
          <li>Explain your reasoning and thought process</li>
          <li>Connect to broader concepts or real-world examples</li>
          <li>Be thorough and thoughtful</li>
        </ul>
      </div>
    </div>
  )
}

export default DiscussionPrompt
