import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import LessonView from './content-types/LessonView'
import ParadigmTable from './content-types/ParadigmTable'
import SentenceDiagram from './content-types/SentenceDiagram'
import ExampleSet from './content-types/ExampleSet'
import MultipleChoice from './content-types/MultipleChoice'
import FillBlank from './content-types/FillBlank'
import DialogueQuestion from './content-types/DialogueQuestion'
import AssessmentResult from './content-types/AssessmentResult'
import DeclensionExplorer from './widgets/DeclensionExplorer'
import WordOrderManipulator from './widgets/WordOrderManipulator'
import ScenarioWidget from './widgets/ScenarioWidget'
import './ContentRenderer.css'

function ContentRenderer({ content, onResponse, onNext, isLoading, learnerId, conceptId }) {
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0)
  const [dots, setDots] = useState('')

  // Rotate through loading messages every 3 seconds
  useEffect(() => {
    if (!content) {
      const interval = setInterval(() => {
        setLoadingMessageIndex(prev => (prev + 1) % loadingMessages.length)
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [content])

  // Animate dots
  useEffect(() => {
    if (!content) {
      const interval = setInterval(() => {
        setDots(prev => prev.length >= 3 ? '' : prev + '.')
      }, 500)
      return () => clearInterval(interval)
    }
  }, [content])

  const loadingMessages = [
    { icon: '🎨', text: 'Crafting your personalized question' },
    { icon: '🏛️', text: 'Building a Roman scenario' },
    { icon: '📚', text: 'Selecting vocabulary from your interests' },
    { icon: '🎯', text: 'Adapting to your skill level' },
    { icon: '✨', text: 'Weaving in narrative context' },
    { icon: '🧠', text: 'Analyzing your learning patterns' }
  ]

  const renderContent = () => {
    if (!content) {
      return (
        <div className="content-placeholder" role="status" aria-live="polite">
          <div className="spinner"></div>
          <div className="loading-message">
            <span className="loading-icon">{loadingMessages[loadingMessageIndex].icon}</span>
            <p className="loading-text">
              {loadingMessages[loadingMessageIndex].text}
              <span className="loading-dots">{dots}</span>
            </p>
          </div>
          <p className="loading-subtext">This usually takes 5-10 seconds</p>
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

      case 'sentence-diagram':
        return (
          <SentenceDiagram
            title={content.title}
            sentence={content.sentence}
            words={content.words}
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
            languageConnection={content.languageConnection}
            nextContent={content._next_content}
            onContinue={onNext}
            learnerId={learnerId}
            conceptId={conceptId}
          />
        )

      case 'text':
        return (
          <div className="text-content">
            <div className="text-body">
              <ReactMarkdown>{content.html || content.text || ''}</ReactMarkdown>
            </div>
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

      case 'declension-explorer':
        return (
          <div>
            <DeclensionExplorer
              noun={content.noun}
              forms={content.forms}
              explanation={content.explanation}
              highlightCase={content.highlightCase}
            />
            <button onClick={onNext} className="continue-button">
              Continue
            </button>
          </div>
        )

      case 'word-order-manipulator':
        return (
          <div>
            <WordOrderManipulator
              sentence={content.sentence}
              words={content.words}
              explanation={content.explanation}
              correctOrders={content.correctOrders}
            />
            <button onClick={onNext} className="continue-button">
              Continue
            </button>
          </div>
        )

      case 'scenario':
        return (
          <ScenarioWidget
            scenario={{
              theme: content.theme,
              title: content.title,
              setting: content.setting,
              steps: content.steps
            }}
            onComplete={onNext}
          />
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
        <div className="debug-section">
          <strong>Mastery Score:</strong> {content.debug_context.mastery_score !== undefined ? `${Math.round(content.debug_context.mastery_score * 100)}%` : 'N/A'}
        </div>
        <div className="debug-section">
          <strong>Assessments Count:</strong> {content.debug_context.assessments_count !== undefined ? content.debug_context.assessments_count : 'N/A'}
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
