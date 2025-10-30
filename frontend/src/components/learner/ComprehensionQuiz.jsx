import { useState } from 'react'
import './ComprehensionQuiz.css'

function ComprehensionQuiz({ questions, onComplete, materialTitle }) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [showFeedback, setShowFeedback] = useState(false)
  const [quizComplete, setQuizComplete] = useState(false)
  const [score, setScore] = useState(0)

  const currentQuestion = questions[currentQuestionIndex]

  const handleAnswer = (answer) => {
    setAnswers({
      ...answers,
      [currentQuestionIndex]: answer
    })
  }

  const checkAnswer = () => {
    const userAnswer = answers[currentQuestionIndex]
    const correctAnswer = currentQuestion.correctAnswer

    let isCorrect = false

    if (currentQuestion.type === 'multiple-choice') {
      isCorrect = userAnswer === correctAnswer
    } else if (currentQuestion.type === 'true-false') {
      isCorrect = userAnswer === correctAnswer
    } else if (currentQuestion.type === 'short-answer') {
      // For short answer, check if answer contains key keywords
      const keywords = correctAnswer.toLowerCase().split(/[,;]+/).map(k => k.trim())
      const userText = (userAnswer || '').toLowerCase()
      isCorrect = keywords.some(keyword => userText.includes(keyword))
    }

    return isCorrect
  }

  const handleNext = () => {
    setShowFeedback(false)

    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    } else {
      // Calculate final score
      let correctCount = 0
      questions.forEach((q, index) => {
        const userAnswer = answers[index]
        let isCorrect = false

        if (q.type === 'multiple-choice') {
          isCorrect = userAnswer === q.correctAnswer
        } else if (q.type === 'true-false') {
          isCorrect = userAnswer === q.correctAnswer
        } else if (q.type === 'short-answer') {
          const keywords = q.correctAnswer.toLowerCase().split(/[,;]+/).map(k => k.trim())
          const userText = (userAnswer || '').toLowerCase()
          isCorrect = keywords.some(keyword => userText.includes(keyword))
        }

        if (isCorrect) correctCount++
      })

      setScore(correctCount)
      setQuizComplete(true)
    }
  }

  const handleSubmitAnswer = () => {
    setShowFeedback(true)
  }

  const handleCompleteQuiz = () => {
    onComplete()
  }

  if (quizComplete) {
    const percentage = (score / questions.length) * 100
    const passed = percentage >= 70 // 70% passing grade

    return (
      <div className="quiz-complete">
        <div className={`score-display ${passed ? 'passed' : 'failed'}`}>
          <h3>{passed ? '✓ Quiz Passed!' : '✗ Quiz Not Passed'}</h3>
          <div className="score-value">
            {score} / {questions.length}
          </div>
          <div className="score-percentage">{percentage.toFixed(0)}%</div>
        </div>

        {passed ? (
          <div className="pass-message">
            <p>Great job! You've demonstrated understanding of the material.</p>
            <button onClick={handleCompleteQuiz} className="complete-button">
              Mark Material as Complete →
            </button>
          </div>
        ) : (
          <div className="fail-message">
            <p>Please review the material and try again. You need at least 70% to pass.</p>
            <button
              onClick={() => {
                setQuizComplete(false)
                setCurrentQuestionIndex(0)
                setAnswers({})
                setShowFeedback(false)
              }}
              className="retry-button"
            >
              Retry Quiz
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="comprehension-quiz">
      <div className="quiz-header">
        <h3>Comprehension Check</h3>
        <div className="question-counter">
          Question {currentQuestionIndex + 1} of {questions.length}
        </div>
      </div>

      <div className="question-container">
        <p className="question-text">{currentQuestion.question}</p>

        {/* Multiple Choice */}
        {currentQuestion.type === 'multiple-choice' && (
          <div className="options-list">
            {currentQuestion.options.map((option, index) => (
              <label key={index} className="option-label">
                <input
                  type="radio"
                  name="answer"
                  value={index}
                  checked={answers[currentQuestionIndex] === index}
                  onChange={() => handleAnswer(index)}
                  disabled={showFeedback}
                />
                <span className="option-text">{option}</span>
              </label>
            ))}
          </div>
        )}

        {/* True/False */}
        {currentQuestion.type === 'true-false' && (
          <div className="true-false-options">
            <label className="tf-option">
              <input
                type="radio"
                name="answer"
                value="true"
                checked={answers[currentQuestionIndex] === 'true'}
                onChange={() => handleAnswer('true')}
                disabled={showFeedback}
              />
              <span>True</span>
            </label>
            <label className="tf-option">
              <input
                type="radio"
                name="answer"
                value="false"
                checked={answers[currentQuestionIndex] === 'false'}
                onChange={() => handleAnswer('false')}
                disabled={showFeedback}
              />
              <span>False</span>
            </label>
          </div>
        )}

        {/* Short Answer */}
        {currentQuestion.type === 'short-answer' && (
          <textarea
            value={answers[currentQuestionIndex] || ''}
            onChange={(e) => handleAnswer(e.target.value)}
            placeholder="Type your answer here..."
            rows={4}
            className="short-answer-input"
            disabled={showFeedback}
          />
        )}

        {/* Feedback */}
        {showFeedback && (
          <div className={`feedback ${checkAnswer() ? 'correct' : 'incorrect'}`}>
            <div className="feedback-header">
              {checkAnswer() ? '✓ Correct!' : '✗ Incorrect'}
            </div>
            {currentQuestion.explanation && (
              <div className="feedback-explanation">
                {currentQuestion.explanation}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="quiz-actions">
        {!showFeedback ? (
          <button
            onClick={handleSubmitAnswer}
            disabled={answers[currentQuestionIndex] === undefined || answers[currentQuestionIndex] === ''}
            className="submit-answer-button"
          >
            Submit Answer
          </button>
        ) : (
          <button
            onClick={handleNext}
            className="next-question-button"
          >
            {currentQuestionIndex < questions.length - 1 ? 'Next Question →' : 'See Results'}
          </button>
        )}
      </div>
    </div>
  )
}

export default ComprehensionQuiz
