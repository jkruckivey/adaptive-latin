import { useState } from 'react'
import { bloomsTaxonomy, finksTaxonomy } from '../../utils/taxonomyData'
import './TaxonomySelector.css'

function TaxonomySelector({ selectedTaxonomy, onSelect }) {
  const [showDetails, setShowDetails] = useState(false)

  return (
    <div className="taxonomy-selector">
      <div className="taxonomy-header">
        <h4>Select Learning Outcome Framework</h4>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="info-toggle"
        >
          {showDetails ? 'Hide Details' : 'Show Details'}
        </button>
      </div>

      <div className="taxonomy-options">
        <label className={`taxonomy-option ${selectedTaxonomy === 'blooms' ? 'selected' : ''}`}>
          <input
            type="radio"
            name="taxonomy"
            value="blooms"
            checked={selectedTaxonomy === 'blooms'}
            onChange={(e) => onSelect(e.target.value)}
          />
          <div className="option-content">
            <div className="option-title">{bloomsTaxonomy.name}</div>
            <div className="option-description">{bloomsTaxonomy.description}</div>
            {selectedTaxonomy === 'blooms' && showDetails && (
              <div className="taxonomy-details">
                <p className="detail-note">
                  <strong>Hierarchical:</strong> Progresses from lower-order (Remember) to higher-order thinking (Create)
                </p>
                <div className="levels-list">
                  {bloomsTaxonomy.levels.map(level => (
                    <div key={level.id} className="level-item">
                      <strong>{level.name}:</strong> {level.description}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </label>

        <label className={`taxonomy-option ${selectedTaxonomy === 'finks' ? 'selected' : ''}`}>
          <input
            type="radio"
            name="taxonomy"
            value="finks"
            checked={selectedTaxonomy === 'finks'}
            onChange={(e) => onSelect(e.target.value)}
          />
          <div className="option-content">
            <div className="option-title">{finksTaxonomy.name}</div>
            <div className="option-description">{finksTaxonomy.description}</div>
            {selectedTaxonomy === 'finks' && showDetails && (
              <div className="taxonomy-details">
                <p className="detail-note">
                  <strong>Non-Hierarchical:</strong> Six interactive dimensions that work together for holistic learning
                </p>
                <div className="levels-list">
                  {finksTaxonomy.dimensions.map(dim => (
                    <div key={dim.id} className="level-item">
                      <strong>{dim.name}:</strong> {dim.description}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </label>

        <label className={`taxonomy-option ${selectedTaxonomy === 'both' ? 'selected' : ''}`}>
          <input
            type="radio"
            name="taxonomy"
            value="both"
            checked={selectedTaxonomy === 'both'}
            onChange={(e) => onSelect(e.target.value)}
          />
          <div className="option-content">
            <div className="option-title">Both Frameworks</div>
            <div className="option-description">Use verbs from both taxonomies for comprehensive outcomes</div>
          </div>
        </label>
      </div>
    </div>
  )
}

export default TaxonomySelector
