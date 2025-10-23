import { useState, useEffect, useRef } from 'react'
import './RomanChat.css'

const API_BASE_URL = 'http://127.0.0.1:8000'

/**
 * Chat interface for "Talk to a Roman" scenario-based conversations
 *
 * Features:
 * - Displays character info and setting
 * - Immersive Latin practice with translations
 * - Shows character personality and context
 * - Counts toward progress after 6+ exchanges
 */
function RomanChat({ learnerId, conceptId, scenarioId, onClose }) {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [scenario, setScenario] = useState(null)
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
      const response = await fetch(`${API_BASE_URL}/conversations/roman`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          learner_id: learnerId,
          concept_id: conceptId,
          scenario_id: scenarioId
        })
      })

      const data = await response.json()

      if (data.success) {
        setConversationId(data.conversation_id)
        setMessages(data.conversation_history)
        setScenario(data.scenario)
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
      const response = await fetch(`${API_BASE_URL}/conversations/roman`, {
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
    return content.split('\n').map((line, i) => {
      // Highlight text within square brackets [Translation: ...]
      if (line.includes('[Translation:')) {
        return (
          <p key={i} className="translation">
            {line}
          </p>
        )
      }
      // Highlight text within parentheses (setting context)
      if (line.startsWith('(') && line.endsWith(')')) {
        return (
          <p key={i} className="context-note">
            {line}
          </p>
        )
      }
      return <p key={i}>{line}</p>
    })
  }

  if (!scenario) {
    return null
  }

  return (
    <div className="roman-chat-container">
      <div className="roman-chat-header">
        <div className="character-info">
          <div className="character-avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <div className="character-details">
            <h3>{scenario.character_name}</h3>
            <p className="character-role">{scenario.character_role}</p>
            <p className="setting">{scenario.setting}</p>
          </div>
        </div>
        <button className="close-button-roman" onClick={onClose} aria-label="Close conversation">
          ×
        </button>
      </div>

      <div className="roman-chat-messages">
        {messages.map((message, index) => (
          <div key={index} className={`roman-message ${message.role}`}>
            {message.role === 'assistant' && (
              <div className="character-name">{scenario.character_name}:</div>
            )}
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
          <div className="roman-message assistant">
            <div className="character-name">{scenario.character_name}:</div>
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

      <form onSubmit={handleSubmit} className="roman-chat-input">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type in Latin or English..."
          className="chat-input-roman"
          disabled={isLoading || !conversationId}
        />
        <button
          type="submit"
          className="send-button-roman"
          disabled={isLoading || !inputValue.trim() || !conversationId}
        >
          Send
        </button>
      </form>

      {messages.length >= 6 && (
        <div className="progress-badge">
          Conversation complete! Counts toward mastery.
        </div>
      )}
    </div>
  )
}

export default RomanChat
