import { useState, useEffect, useRef } from 'react'
import { api } from '../api'
import ConfidenceRating from './ConfidenceRating'
import './ChatInterface.css'

function ChatInterface({ learnerId, onProgressUpdate }) {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showConfidenceRating, setShowConfidenceRating] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Send initial greeting
  useEffect(() => {
    if (learnerId && messages.length === 0) {
      handleSendMessage('Hello! I\'m ready to learn Latin.')
    }
  }, [learnerId])

  const handleSendMessage = async (message) => {
    if (!message.trim() || isLoading) return

    const userMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await api.sendMessage(learnerId, message)

      if (response.success) {
        const assistantMessage = {
          role: 'assistant',
          content: response.message,
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, assistantMessage])

        // Update progress if provided
        if (response.confidence !== null && response.confidence !== undefined) {
          onProgressUpdate?.()
        }
      } else {
        const errorMessage = {
          role: 'error',
          content: response.error || 'Sorry, something went wrong. Please try again.',
          timestamp: new Date().toISOString()
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      console.error('Send message error:', error)
      const errorMessage = {
        role: 'error',
        content: 'Connection error. Please check your internet connection.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    handleSendMessage(inputValue)
  }

  const handleConfidenceSubmit = (confidenceLevel) => {
    setShowConfidenceRating(false)
    handleSendMessage(`My confidence level is: ${confidenceLevel}/5`)
  }

  return (
    <div className="chat-interface">
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="message-content">
              {message.content.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
            <div className="message-time">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant loading">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {showConfidenceRating ? (
        <ConfidenceRating onSubmit={handleConfidenceSubmit} />
      ) : (
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message..."
            className="chat-input"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="send-button"
            disabled={isLoading || !inputValue.trim()}
          >
            Send
          </button>
        </form>
      )}
    </div>
  )
}

export default ChatInterface
