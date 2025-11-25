import { useState, useRef, useEffect } from 'react'
import './DialogueQuestion.css'

function DialogueQuestion({ question, context, onSubmit, isLoading, onComplete }) {
  // Conversation history: array of { role: 'tutor'|'learner', content, type?: 'question'|'feedback' }
  const [messages, setMessages] = useState([])
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [exchangeCount, setExchangeCount] = useState(0)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const MAX_EXCHANGES = 3

  // Initialize with the first question
  useEffect(() => {
    if (question && messages.length === 0) {
      setMessages([{
        role: 'tutor',
        content: question,
        context: context,
        type: 'question'
      }])
    }
  }, [question, context])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input after tutor message
  useEffect(() => {
    if (!isEvaluating && !isComplete && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isEvaluating, isComplete, messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!currentAnswer.trim() || isEvaluating || isComplete) return

    const answer = currentAnswer.trim()

    // Add learner's response to conversation
    setMessages(prev => [...prev, {
      role: 'learner',
      content: answer,
      type: 'response'
    }])
    setCurrentAnswer('')
    setIsEvaluating(true)

    try {
      // Get the last tutor question for evaluation context
      const lastQuestion = messages.filter(m => m.role === 'tutor' && m.type === 'question').pop()

      // Call backend for evaluation - this returns feedback + optional follow-up
      const result = await onSubmit(answer, {
        questionContext: lastQuestion?.content,
        exchangeCount: exchangeCount,
        conversationHistory: messages
      })

      const newExchangeCount = exchangeCount + 1
      setExchangeCount(newExchangeCount)

      // Add tutor's feedback
      setMessages(prev => [...prev, {
        role: 'tutor',
        content: result.feedback,
        type: 'feedback',
        score: result.score,
        isCorrect: result.isCorrect
      }])

      // Check if we should continue or complete
      if (newExchangeCount >= MAX_EXCHANGES || result.dialogueComplete) {
        // Dialogue complete - show final message and allow moving on
        setIsComplete(true)
        setTimeout(() => {
          setMessages(prev => [...prev, {
            role: 'tutor',
            content: result.isCorrect
              ? "Great discussion! You've shown solid understanding. Let's move on."
              : "Good effort working through this. Let's continue and build on what we've covered.",
            type: 'closing'
          }])
        }, 500)
      } else if (result.followUpQuestion) {
        // Add follow-up question after a brief pause
        setTimeout(() => {
          setMessages(prev => [...prev, {
            role: 'tutor',
            content: result.followUpQuestion,
            type: 'question'
          }])
        }, 800)
      }
    } catch (error) {
      console.error('Dialogue evaluation error:', error)
      setMessages(prev => [...prev, {
        role: 'tutor',
        content: "I had trouble processing that. Let's try again - could you rephrase your answer?",
        type: 'feedback'
      }])
    } finally {
      setIsEvaluating(false)
    }
  }

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e)
    }
  }

  const handleContinue = () => {
    if (onComplete) {
      onComplete({
        exchangeCount,
        messages,
        finalScore: messages.filter(m => m.score !== undefined).reduce((sum, m) => sum + (m.score || 0), 0) / Math.max(1, exchangeCount)
      })
    }
  }

  return (
    <div className="dialogue-question conversational">
      <div className="dialogue-header">
        <div className="dialogue-icon">💬</div>
        <h2>Socratic Dialogue</h2>
        <p className="dialogue-subtitle">Let's explore this through back-and-forth discussion</p>
        <div className="exchange-indicator">
          Exchange {Math.min(exchangeCount + 1, MAX_EXCHANGES)} of {MAX_EXCHANGES}
        </div>
      </div>

      <div className="dialogue-conversation">
        {/* Context banner (shown once at top) */}
        {context && (
          <div className="context-banner">
            <span className="context-label">📚 Context:</span> {context}
          </div>
        )}

        {/* Conversation messages */}
        <div className="messages-container">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}-message ${msg.type || ''}`}>
              <div className="message-avatar">
                {msg.role === 'tutor' ? '🏛️' : '👤'}
              </div>
              <div className={`message-bubble ${msg.type === 'feedback' ? (msg.isCorrect ? 'positive' : 'constructive') : ''}`}>
                {msg.type === 'feedback' && (
                  <div className="feedback-indicator">
                    {msg.isCorrect ? '✓' : '→'}
                  </div>
                )}
                <div className="message-content">{msg.content}</div>
              </div>
            </div>
          ))}

          {/* Typing indicator when evaluating */}
          {isEvaluating && (
            <div className="message tutor-message">
              <div className="message-avatar">🏛️</div>
              <div className="message-bubble typing">
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input area - hidden when complete */}
        {!isComplete ? (
          <form onSubmit={handleSubmit} className="dialogue-input-area">
            <div className="input-row">
              <div className="input-avatar">👤</div>
              <textarea
                ref={inputRef}
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={exchangeCount === 0
                  ? "Share your thinking..."
                  : "Continue the discussion..."}
                className="dialogue-input compact"
                rows={2}
                disabled={isEvaluating || isLoading}
              />
              <button
                type="submit"
                className="send-button"
                disabled={!currentAnswer.trim() || isEvaluating || isLoading}
                aria-label="Send response"
              >
                {isEvaluating ? (
                  <span className="spinner small"></span>
                ) : (
                  <span className="send-icon">➤</span>
                )}
              </button>
            </div>
            <p className="keyboard-hint">Ctrl+Enter to send</p>
          </form>
        ) : (
          <div className="dialogue-complete">
            <button onClick={handleContinue} className="continue-button">
              Continue Learning
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default DialogueQuestion
