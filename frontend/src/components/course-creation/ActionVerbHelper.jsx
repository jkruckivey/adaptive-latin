import { useState } from 'react'
import { bloomsTaxonomy, finksTaxonomy } from '../../utils/taxonomyData'
import './ActionVerbHelper.css'

function ActionVerbHelper({ taxonomy, onSelectVerb, onClose }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState(null)

  const taxonomyData = taxonomy === 'blooms' ? bloomsTaxonomy :
                        taxonomy === 'finks' ? finksTaxonomy : null

  if (!taxonomyData && taxonomy !== 'both') return null

  // Get categories based on selected taxonomy
  const getCategories = () => {
    if (taxonomy === 'both') {
      return [
        ...bloomsTaxonomy.levels.map(l => ({ ...l, taxonomy: 'blooms' })),
        ...finksTaxonomy.dimensions.map(d => ({ ...d, taxonomy: 'finks' }))
      ]
    }
    return taxonomy === 'blooms' ? bloomsTaxonomy.levels : finksTaxonomy.dimensions
  }

  const categories = getCategories()

  // Filter verbs based on search
  const filterVerbs = (verbs) => {
    if (!searchTerm) return verbs
    return verbs.filter(v => v.toLowerCase().includes(searchTerm.toLowerCase()))
  }

  const handleVerbClick = (verb) => {
    onSelectVerb(verb)
    onClose()
  }

  return (
    <div className="action-verb-helper">
      <div className="verb-helper-header">
        <h3>Select an Action Verb</h3>
        <button onClick={onClose} className="close-button">×</button>
      </div>

      <div className="verb-helper-search">
        <input
          type="text"
          placeholder="Search verbs..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      {taxonomy === 'blooms' && (
        <div className="taxonomy-note">
          <strong>📚 Bloom's Taxonomy</strong>
          <p>Hierarchical: Course-level outcomes typically use higher-order verbs (Analyze, Evaluate, Create). Module-level outcomes can use same or lower-order verbs.</p>
        </div>
      )}

      {taxonomy === 'finks' && (
        <div className="taxonomy-note">
          <strong>🌟 Fink's Taxonomy</strong>
          <p>Non-hierarchical: Choose verbs from different dimensions to create holistic learning outcomes.</p>
        </div>
      )}

      <div className="verb-categories">
        {categories.map(category => {
          const filteredVerbs = filterVerbs(category.verbs)
          if (filteredVerbs.length === 0) return null

          return (
            <div key={category.id} className="verb-category">
              <div
                className={`category-header ${selectedCategory === category.id ? 'expanded' : ''}`}
                onClick={() => setSelectedCategory(selectedCategory === category.id ? null : category.id)}
              >
                <h4>{category.name}</h4>
                <p className="category-description">{category.description}</p>
                {taxonomy === 'both' && (
                  <span className="taxonomy-badge">
                    {category.taxonomy === 'blooms' ? '📚 Bloom\'s' : '🌟 Fink\'s'}
                  </span>
                )}
              </div>

              {selectedCategory === category.id && (
                <div className="category-content">
                  <div className="verb-grid">
                    {filteredVerbs.map(verb => (
                      <button
                        key={verb}
                        onClick={() => handleVerbClick(verb)}
                        className="verb-button"
                      >
                        {verb}
                      </button>
                    ))}
                  </div>

                  {category.examples && category.examples.length > 0 && (
                    <div className="category-examples">
                      <strong>Examples:</strong>
                      <ul>
                        {category.examples.map((example, i) => (
                          <li key={i}>{example}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ActionVerbHelper
