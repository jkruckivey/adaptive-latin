import { useState } from 'react'
import LessonView from './content-types/LessonView'
import ParadigmTable from './content-types/ParadigmTable'
import ExampleSet from './content-types/ExampleSet'
import MultipleChoice from './content-types/MultipleChoice'
import FillBlank from './content-types/FillBlank'
import DialogueQuestion from './content-types/DialogueQuestion'
import AssessmentResult from './content-types/AssessmentResult'
import './ContentRenderer.css'

function ContentRenderer({ content, onResponse, onNext, isLoading, learnerId, conceptId }) {
  const [userAnswer, setUserAnswer] = useState(null)

  const renderContent = () => {
    if (!content) {
      return (
        <div className="content-placeholder">
          <div className="spinner"></div>
          <p>Loading your personalized content...</p>
        </div>
      )
    }

    switch (content.type) {
      case 'lesson':
        return (
          <LessonView
            title={content.title}
            sections={content.sections}
            externalResources={content.external_resources}
            onContinue={onNext}
          />
        )

      case 'paradigm-table':
        return (
          <ParadigmTable
            title={content.title}
            noun={content.noun}
            forms={content.forms}
            explanation={content.explanation}
            onContinue={onNext}
          />
        )

      case 'example-set':
        return (
          <ExampleSet
            title={content.title}
            examples={content.examples}
            externalResources={content.external_resources}
            onContinue={onNext}
          />
        )

      case 'multiple-choice':
        return (
          <MultipleChoice
            scenario={content.scenario}
            question={content.question}
            options={content.options}
            onAnswer={(answer) => onResponse({ type: 'multiple-choice', answer })}
            isLoading={isLoading}
          />
        )

      case 'fill-blank':
        return (
          <FillBlank
            sentence={content.sentence}
            blanks={content.blanks}
            onSubmit={(answers) => onResponse({ type: 'fill-blank', answers })}
            isLoading={isLoading}
          />
        )

      case 'dialogue':
        return (
          <DialogueQuestion
            question={content.question}
            context={content.context}
            onSubmit={(answer) => onResponse({ type: 'dialogue', answer })}
            isLoading={isLoading}
          />
        )

      case 'assessment-result':
        return (
          <AssessmentResult
            score={content.score}
            feedback={content.feedback}
            correctAnswer={content.correctAnswer}
            calibration={content.calibration}
            onContinue={onNext}
            learnerId={learnerId}
            conceptId={conceptId}
          />
        )

      case 'text':
        return (
          <div className="text-content">
            <div className="text-body" dangerouslySetInnerHTML={{ __html: content.html }} />
            <button onClick={onNext} className="continue-button">
              Continue
            </button>
          </div>
        )

      case 'course-end':
        return (
          <div className="course-end-message">
            <div className="end-icon">🎓</div>
            <h2>Congratulations on Completing Available Content!</h2>
            <div className="end-description">
              <p><strong>You've mastered {content.completedConcepts || 1} concept{content.completedConcepts !== 1 ? 's' : ''}!</strong></p>
              <p>This course is currently under development. Additional concepts are being authored and will be available soon.</p>

              <div className="development-status">
                <h3>Development Status</h3>
                <ul>
                  <li>✅ Concept 001: First Declension & Present Tense of "Sum" (Complete)</li>
                  <li>🚧 Concepts 002-007: In Development</li>
                </ul>
              </div>

              <p>Your progress has been saved. When new concepts are added, you'll be able to continue your learning journey right where you left off.</p>

              <p className="review-prompt">In the meantime, you can:</p>
              <ul>
                <li>Review what you've learned by restarting the course</li>
                <li>Check the progress dashboard to see your mastery scores</li>
                <li>Use the AI tutor to ask questions about Latin grammar</li>
              </ul>
            </div>

            <button onClick={() => window.location.reload()} className="continue-button">
              Return to Dashboard
            </button>
          </div>
        )

      default:
        return (
          <div className="error-content">
            <p>Unknown content type: {content.type}</p>
            <button onClick={onNext} className="continue-button">
              Continue
            </button>
          </div>
        )
    }
  }

  // Show cumulative badge if applicable
  const cumulativeBadge = content?.is_cumulative && (
    <div className="cumulative-badge-container">
      <div className="cumulative-badge">
        <span className="badge-icon">🔗</span>
        <div className="badge-content">
          <strong>Cumulative Review</strong>
          <span className="badge-subtitle">
            Integrating: {content.cumulative_concepts?.join(', ') || 'multiple concepts'}
          </span>
        </div>
      </div>
    </div>
  )

  // Debug panel
  const debugPanel = content?.debug_context && (
    <details className="debug-panel">
      <summary className="debug-summary">🔍 Debug: AI Context (Click to expand)</summary>
      <div className="debug-content">
        <h4>Context Sent to AI</h4>
        <div className="debug-section">
          <strong>Stage:</strong> {content.debug_context.stage}
        </div>
        <div className="debug-section">
          <strong>Remediation Type:</strong> {content.debug_context.remediation_type || 'none'}
        </div>
        {content.debug_context.question_context_sent_to_ai ? (
          <div className="debug-section">
            <strong>Question Context:</strong>
            <pre className="debug-json">
              {JSON.stringify(content.debug_context.question_context_sent_to_ai, null, 2)}
            </pre>
          </div>
        ) : (
          <div className="debug-section">
            <strong>Question Context:</strong> <em>None (no question context sent)</em>
          </div>
        )}
      </div>
    </details>
  )

  return (
    <div className="content-renderer">
      {cumulativeBadge}
      {renderContent()}
      {debugPanel}
    </div>
  )
}

export default ContentRenderer
