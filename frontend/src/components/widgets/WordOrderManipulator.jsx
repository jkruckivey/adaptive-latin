import { useState } from 'react'
import './WordOrderManipulator.css'

function WordOrderManipulator({ sentence, words, explanation, correctOrders }) {
  const [currentOrder, setCurrentOrder] = useState([...words])
  const [draggedIndex, setDraggedIndex] = useState(null)
  const [feedback, setFeedback] = useState('')

  const handleDragStart = (index) => {
    setDraggedIndex(index)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleDrop = (dropIndex) => {
    if (draggedIndex === null) return

    const newOrder = [...currentOrder]
    const draggedWord = newOrder[draggedIndex]

    // Remove from old position
    newOrder.splice(draggedIndex, 1)

    // Insert at new position
    newOrder.splice(dropIndex, 0, draggedWord)

    setCurrentOrder(newOrder)
    setDraggedIndex(null)

    // Check if this order is valid
    checkOrder(newOrder)
  }

  const checkOrder = (order) => {
    const orderString = order.map(w => w.word).join(' ')

    if (correctOrders && correctOrders.length > 0) {
      const isCorrect = correctOrders.some(correct => {
        const correctString = correct.map(w => w.word || w).join(' ')
        return correctString === orderString
      })

      if (isCorrect) {
        const matchedOrder = correctOrders.find(correct => {
          const correctString = correct.map(w => w.word || w).join(' ')
          return correctString === orderString
        })

        // Get the emphasis/meaning from the matched order
        const emphasis = matchedOrder.find(w => w.emphasis)?.emphasis || 'neutral'
        setFeedback(`✓ Valid! This order emphasizes: ${emphasis}`)
      } else {
        setFeedback('Try a different arrangement - Latin word order is flexible!')
      }
    }
  }

  const reset = () => {
    setCurrentOrder([...words])
    setFeedback('')
  }

  const getWordClass = (word) => {
    const classes = ['word-tile']
    if (word.role) classes.push(`role-${word.role}`)
    return classes.join(' ')
  }

  return (
    <div className="word-order-manipulator">
      <div className="manipulator-header">
        <h3>Explore Word Order</h3>
        {explanation && <p className="manipulator-explanation">{explanation}</p>}
      </div>

      <div className="sentence-display">
        <div className="display-label">Current Sentence:</div>
        <div className="display-sentence">
          {currentOrder.map(w => w.word).join(' ')}
        </div>
        <div className="display-translation">
          "{sentence.translation}"
        </div>
      </div>

      <div className="word-tiles">
        {currentOrder.map((word, index) => (
          <div
            key={`${word.word}-${index}`}
            className={getWordClass(word)}
            draggable
            onDragStart={() => handleDragStart(index)}
            onDragOver={handleDragOver}
            onDrop={() => handleDrop(index)}
          >
            <div className="word-text">{word.word}</div>
            {word.role && <div className="word-role">{word.role}</div>}
            {word.case && <div className="word-case">{word.case}</div>}
          </div>
        ))}
      </div>

      {feedback && (
        <div className={`feedback-box ${feedback.startsWith('✓') ? 'success' : 'info'}`}>
          {feedback}
        </div>
      )}

      <div className="manipulator-controls">
        <button onClick={reset} className="reset-button">
          Reset to Original
        </button>
      </div>

      <div className="manipulator-hint">
        <strong>💡 Try this:</strong> Drag words to rearrange them. Latin word order is flexible because
        the case endings tell you each word's function. Try putting the most important word first -
        that's often where Romans put emphasis!
      </div>

      <div className="role-legend">
        <div className="legend-title">Word Functions:</div>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-color role-subject"></span>
            <span>Subject (nominative)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color role-verb"></span>
            <span>Verb</span>
          </div>
          <div className="legend-item">
            <span className="legend-color role-object"></span>
            <span>Object (accusative)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color role-indirect"></span>
            <span>Indirect Object (dative)</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default WordOrderManipulator
