import { useState } from 'react'
import LessonView from './content-types/LessonView'
import ParadigmTable from './content-types/ParadigmTable'
import ExampleSet from './content-types/ExampleSet'
import MultipleChoice from './content-types/MultipleChoice'
import FillBlank from './content-types/FillBlank'
import DialogueQuestion from './content-types/DialogueQuestion'
import AssessmentResult from './content-types/AssessmentResult'
import './ContentRenderer.css'

function ContentRenderer({ content, onResponse, onNext, isLoading }) {
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

  return (
    <div className="content-renderer">
      {renderContent()}
    </div>
  )
}

export default ContentRenderer
