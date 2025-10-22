import './ParadigmTable.css'

function ParadigmTable({ title, noun, forms, explanation, onContinue }) {
  return (
    <div className="paradigm-table-container">
      <h2 className="paradigm-title">{title}</h2>

      {noun && (
        <div className="paradigm-noun">
          <span className="noun-label">Declining:</span>
          <span className="noun-value">{noun}</span>
        </div>
      )}

      <div className="paradigm-table">
        <div className="paradigm-row paradigm-header">
          <div className="paradigm-cell">Case</div>
          <div className="paradigm-cell">Singular</div>
          <div className="paradigm-cell">Plural</div>
          <div className="paradigm-cell">Function</div>
        </div>

        {forms.map((form, index) => (
          <div key={index} className="paradigm-row">
            <div className="paradigm-cell case-name">{form.case}</div>
            <div className="paradigm-cell form-singular">{form.singular}</div>
            <div className="paradigm-cell form-plural">{form.plural}</div>
            <div className="paradigm-cell function-desc">{form.function}</div>
          </div>
        ))}
      </div>

      {explanation && (
        <div className="paradigm-explanation">
          <h3>Key Points:</h3>
          <p>{explanation}</p>
        </div>
      )}

      <div className="paradigm-footer">
        <button onClick={onContinue} className="continue-button">
          Continue →
        </button>
      </div>
    </div>
  )
}

export default ParadigmTable
