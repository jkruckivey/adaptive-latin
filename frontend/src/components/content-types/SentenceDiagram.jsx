import './SentenceDiagram.css'

function SentenceDiagram({ title, sentence, words, explanation, onContinue }) {
  // Map case names to color classes matching ParadigmTable
  const getCaseClass = (caseType) => {
    if (!caseType) return 'case-default'
    const caseLower = caseType.toLowerCase()
    if (caseLower.includes('nominative')) return 'case-nominative'
    if (caseLower.includes('genitive')) return 'case-genitive'
    if (caseLower.includes('dative')) return 'case-dative'
    if (caseLower.includes('accusative')) return 'case-accusative'
    if (caseLower.includes('ablative')) return 'case-ablative'
    return 'case-default'
  }

  return (
    <div className="sentence-diagram-container">
      <h2 className="diagram-title">{title}</h2>

      {/* Full sentence display */}
      {sentence && (
        <div className="full-sentence">
          <span className="sentence-label">Sentence:</span>
          <span className="sentence-text">{sentence}</span>
        </div>
      )}

      {/* Word breakdown diagram */}
      <div className="diagram-words">
        {words.map((word, index) => {
          const caseClass = getCaseClass(word.case)

          return (
            <div key={index} className="diagram-word-group">
              {/* Connection arrow (if not first word) */}
              {index > 0 && (
                <div className="connection-arrow">
                  <span className="arrow-symbol">→</span>
                </div>
              )}

              {/* Word card */}
              <div className={`diagram-word ${caseClass}`}>
                {/* Latin word */}
                <div className="word-latin">{word.latin}</div>

                {/* English translation */}
                <div className="word-english">"{word.english}"</div>

                {/* Grammatical info */}
                <div className="word-grammar">
                  <div className="grammar-item">
                    <span className="grammar-label">Case:</span>
                    <span className="grammar-value">{word.case}</span>
                  </div>
                  <div className="grammar-item">
                    <span className="grammar-label">Role:</span>
                    <span className="grammar-value">{word.role}</span>
                  </div>
                </div>

                {/* Case indicator dot */}
                <div className="case-indicator-wrapper">
                  <span className="case-indicator"></span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Explanation section */}
      {explanation && (
        <div className="diagram-explanation">
          <h3>How It Works:</h3>
          <p>{explanation}</p>
        </div>
      )}

      {/* Continue button */}
      <div className="diagram-footer">
        <button onClick={onContinue} className="continue-button">
          Continue →
        </button>
      </div>
    </div>
  )
}

export default SentenceDiagram
