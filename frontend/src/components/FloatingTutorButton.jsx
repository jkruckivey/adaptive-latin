import { useState } from 'react'
import TutorChat from './TutorChat'
import './FloatingTutorButton.css'

/**
 * Floating button that provides always-accessible "Talk to Tutor" feature
 *
 * Appears in bottom-right corner on all pages
 * Opens a modal chat interface when clicked
 */
function FloatingTutorButton({ learnerId, conceptId }) {
  const [isChatOpen, setIsChatOpen] = useState(false)

  if (!learnerId || !conceptId) {
    return null // Don't show button if no learner/concept context
  }

  return (
    <>
      <button
        className="floating-tutor-button"
        onClick={() => setIsChatOpen(true)}
        aria-label="Talk to your Latin tutor"
        title="Ask your tutor for help"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {/* Speech bubble icon */}
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          {/* Question mark */}
          <path d="M9 9h.01M15 9h.01M12 13v.01" />
        </svg>
        <span className="button-text">Ask Tutor</span>
      </button>

      {isChatOpen && (
        <TutorChat
          learnerId={learnerId}
          conceptId={conceptId}
          onClose={() => setIsChatOpen(false)}
        />
      )}
    </>
  )
}

export default FloatingTutorButton
