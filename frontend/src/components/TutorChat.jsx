import { useState, useEffect, useRef } from 'react'
import './TutorChat.css'

const API_BASE_URL = 'http://127.0.0.1:8000'

/**
 * Modal chat interface for "Talk to Tutor" conversations
 *
 * Features:
 * - Starts new conversation or continues existing one
 * - Displays Socratic responses from tutor
 * - Saves conversation history
 * - Counts toward progress after 6+ exchanges
 */
function TutorChat({ learnerId, conceptId, onClose }) {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Start conversation on mount
  useEffect(() => {
    startConversation()
  }, [])

  const startConversation = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/conversations/tutor`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learner_id: learnerId,
          concept_id: conceptId
        })
      })

      const data = await response.json()

      if (data.success) {
        setConversationId(data.conversation_id)
        setMessages(data.conversation_history)
      } else {
        setError(data.error || 'Failed to start conversation')
      }
    } catch (err) {
      console.error('Start conversation error:', err)
      setError('Connection error. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const sendMessage = async (message) => {
    if (!message.trim() || isLoading || !conversationId) return

    // Add user message optimistically
    const userMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/conversations/tutor`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learner_id: learnerId,
          concept_id: conceptId,
          conversation_id: conversationId,
          message: message
        })
      })

      const data = await response.json()

      if (data.success) {
        // Update with server response (includes both user and assistant messages)
        setMessages(data.conversation_history)
      } else {
        setError(data.error || 'Failed to send message')
        // Remove optimistic user message on error
        setMessages(prev => prev.slice(0, -1))
      }
    } catch (err) {
      console.error('Send message error:', err)
      setError('Connection error. Please try again.')
      // Remove optimistic user message on error
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(inputValue)
  }

  const formatMessage = (content) => {
    // Split by newlines and render as paragraphs
    return content.split('\n').map((line, i) => (
      <p key={i}>{line}</p>
    ))
  }

  return (
    <div className="tutor-chat-overlay" onClick={onClose}>
      <div className="tutor-chat-modal" onClick={(e) => e.stopPropagation()}>
        <div className="tutor-chat-header">
          <div className="header-content">
            <div className="tutor-avatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 14l9-5-9-5-9 5 9 5z" />
                <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
              </svg>
            </div>
            <div className="header-text">
              <h2>Latin Tutor</h2>
              <p>Ask questions about {conceptId}</p>
            </div>
          </div>
          <button className="close-button" onClick={onClose} aria-label="Close chat">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="tutor-chat-messages">
          {messages.map((message, index) => (
            <div key={index} className={`tutor-message ${message.role}`}>
              <div className="message-bubble">
                {formatMessage(message.content)}
              </div>
              <div className="message-timestamp">
                {new Date(message.timestamp).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="tutor-message assistant">
              <div className="message-bubble loading">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="tutor-chat-input">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask your tutor a question..."
            className="chat-input"
            disabled={isLoading || !conversationId}
          />
          <button
            type="submit"
            className="send-button"
            disabled={isLoading || !inputValue.trim() || !conversationId}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>

        {messages.length >= 6 && (
          <div className="progress-notification">
            This conversation counts toward your mastery progress!
          </div>
        )}
      </div>
    </div>
  )
}

export default TutorChat
