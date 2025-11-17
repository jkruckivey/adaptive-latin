import './ParadigmTable.css'

function ParadigmTable({
  title,
  noun,
  nounLabel = 'Item',
  forms,
  headers = { col1: 'Type', col2: 'Form 1', col3: 'Form 2', col4: 'Function' },
  explanation,
  onContinue
}) {
  return (
    <div className="paradigm-table-container">
      <h2 className="paradigm-title">{title}</h2>

      {noun && (
        <div className="paradigm-noun">
          <span className="noun-label">{nounLabel}:</span>
          <span className="noun-value">{noun}</span>
        </div>
      )}

      <div className="paradigm-table">
        <div className="paradigm-row paradigm-header">
          <div className="paradigm-cell">{headers.col1}</div>
          <div className="paradigm-cell">{headers.col2}</div>
          <div className="paradigm-cell">{headers.col3}</div>
          <div className="paradigm-cell">{headers.col4}</div>
        </div>

        {forms.map((form, index) => (
          <div key={index} className="paradigm-row">
            <div className="paradigm-cell case-name">{form.case || form.type}</div>
            <div className="paradigm-cell form-singular">{form.singular || form.form1}</div>
            <div className="paradigm-cell form-plural">{form.plural || form.form2}</div>
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
