import { useState } from 'react'
import './DeclensionExplorer.css'

function DeclensionExplorer({ noun, forms, explanation, highlightCase }) {
  const [selectedCase, setSelectedCase] = useState(highlightCase || 'nominative')
  const [selectedNumber, setSelectedNumber] = useState('singular')

  const cases = ['nominative', 'genitive', 'dative', 'accusative', 'ablative']
  const numbers = ['singular', 'plural']

  const getForm = (caseType, number) => {
    const key = `${caseType}_${number}`
    return forms[key] || '—'
  }

  const getCaseFunction = (caseType) => {
    const functions = {
      nominative: 'Subject of the verb',
      genitive: 'Possession (of/\'s)',
      dative: 'Indirect object (to/for)',
      accusative: 'Direct object',
      ablative: 'Means, manner, place (by/with/from)'
    }
    return functions[caseType] || ''
  }

  const currentForm = getForm(selectedCase, selectedNumber)
  const currentFunction = getCaseFunction(selectedCase)

  return (
    <div className="declension-explorer">
      <div className="explorer-header">
        <h3>Explore: {noun}</h3>
        {explanation && <p className="explorer-explanation">{explanation}</p>}
      </div>

      <div className="explorer-controls">
        <div className="control-group">
          <label>Case:</label>
          <div className="button-group">
            {cases.map(c => (
              <button
                key={c}
                className={`case-button ${selectedCase === c ? 'active' : ''} ${highlightCase === c ? 'highlight' : ''}`}
                onClick={() => setSelectedCase(c)}
              >
                {c.charAt(0).toUpperCase() + c.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="control-group">
          <label>Number:</label>
          <div className="button-group">
            {numbers.map(n => (
              <button
                key={n}
                className={`number-button ${selectedNumber === n ? 'active' : ''}`}
                onClick={() => setSelectedNumber(n)}
              >
                {n.charAt(0).toUpperCase() + n.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="explorer-display">
        <div className="form-display">
          <div className="form-label">Form:</div>
          <div className="form-value">{currentForm}</div>
        </div>
        <div className="function-display">
          <div className="function-label">Function:</div>
          <div className="function-value">{currentFunction}</div>
        </div>
      </div>

      <div className="explorer-table">
        <table>
          <thead>
            <tr>
              <th>Case</th>
              <th>Singular</th>
              <th>Plural</th>
              <th>Function</th>
            </tr>
          </thead>
          <tbody>
            {cases.map(c => (
              <tr
                key={c}
                className={selectedCase === c ? 'selected-row' : ''}
                onClick={() => setSelectedCase(c)}
              >
                <td className="case-name">{c.charAt(0).toUpperCase() + c.slice(1)}</td>
                <td className={selectedCase === c && selectedNumber === 'singular' ? 'selected-cell' : ''}>
                  {getForm(c, 'singular')}
                </td>
                <td className={selectedCase === c && selectedNumber === 'plural' ? 'selected-cell' : ''}>
                  {getForm(c, 'plural')}
                </td>
                <td className="case-function">{getCaseFunction(c)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="explorer-hint">
        💡 Click a case or number to explore how the form changes and what it means
      </div>
    </div>
  )
}

export default DeclensionExplorer
