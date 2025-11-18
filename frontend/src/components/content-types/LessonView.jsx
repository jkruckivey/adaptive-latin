import './LessonView.css'
import ExternalResources from '../ExternalResources'

function LessonView({ title, sections, externalResources, onContinue }) {
  return (
    <div className="lesson-view">
      <div className="lesson-header">
        <h1 className="lesson-title">{title}</h1>
      </div>

      <div className="lesson-content">
        {sections.map((section, index) => (
          <div key={index} className="lesson-section">
            {section.heading && <h2 className="section-heading">{section.heading}</h2>}

            {section.paragraphs && section.paragraphs.map((para, i) => (
              <p key={i} className="section-paragraph">{para}</p>
            ))}

            {section.bullets && (
              <ul className="section-bullets">
                {section.bullets.map((bullet, i) => (
                  <li key={i}>{bullet}</li>
                ))}
              </ul>
            )}

            {section.example && (
              <div className="section-example">
                <div className="example-label">Example:</div>
                <div className="example-content">{section.example}</div>
              </div>
            )}

            {section.callout && (
              <div className={`section-callout ${section.callout.type || 'info'}`}>
                <div className="callout-icon">
                </div>
                <div className="callout-content">{section.callout.text}</div>
              </div>
            )}
          </div>
        ))}
      </div>

      {externalResources && <ExternalResources resources={externalResources} />}

      <div className="lesson-footer">
        <button onClick={onContinue} className="continue-button">
          Continue →
        </button>
      </div>
    </div>
  )
}

export default LessonView
