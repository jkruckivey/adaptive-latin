import './ExampleSet.css'
import ExternalResources from '../ExternalResources'

function ExampleSet({ title, examples, externalResources, onContinue }) {
  return (
    <div className="example-set">
      <h2 className="examples-title">{title}</h2>

      <div className="examples-list">
        {examples.map((example, index) => (
          <div key={index} className="example-card">
            <div className="example-number">{index + 1}</div>
            <div className="example-body">
              <div className="example-latin">{example.latin}</div>
              <div className="example-translation">{example.translation}</div>
              {example.notes && (
                <div className="example-notes">
                  <span className="notes-label">Note:</span> {example.notes}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {externalResources && <ExternalResources resources={externalResources} />}

      <div className="examples-footer">
        <button onClick={onContinue} className="continue-button">
          Continue →
        </button>
      </div>
    </div>
  )
}

export default ExampleSet
