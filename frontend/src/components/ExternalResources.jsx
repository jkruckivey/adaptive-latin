import './ExternalResources.css'

function ExternalResources({ resources }) {
  if (!resources || resources.length === 0) {
    return null
  }

  const getResourceIcon = (type) => {
    switch (type) {
      case 'video':
        return '▶'
      case 'article':
        return '▪'
      case 'practice':
        return '▸'
      default:
        return '◆'
    }
  }

  const getResourceTypeLabel = (type) => {
    switch (type) {
      case 'video':
        return 'Watch'
      case 'article':
        return 'Read'
      case 'practice':
        return 'Practice'
      default:
        return 'View'
    }
  }

  return (
    <div className="external-resources">
      <div className="resources-header">
        <h3>Want to learn more?</h3>
        <p>These resources match your learning preferences and might help</p>
      </div>

      <div className="resources-list">
        {resources.map((resource, index) => (
          <a
            key={index}
            href={resource.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`resource-card resource-${resource.type}`}
          >
            {resource.thumbnail && (
              <div className="resource-thumbnail">
                <img src={resource.thumbnail} alt={resource.title} />
                {resource.duration && (
                  <span className="resource-duration">{resource.duration}</span>
                )}
              </div>
            )}

            <div className="resource-content">
              <div className="resource-header-row">
                <span className="resource-icon">{getResourceIcon(resource.type)}</span>
                <span className="resource-type">{getResourceTypeLabel(resource.type)}</span>
                <span className="resource-provider">{resource.provider}</span>
              </div>

              <h4 className="resource-title">{resource.title}</h4>
              <p className="resource-description">{resource.description}</p>

              <div className="resource-meta">
                {resource.duration && <span className="meta-item">⏱ {resource.duration}</span>}
                {resource.reading_time && <span className="meta-item">📖 {resource.reading_time}</span>}
                {resource.estimated_time && <span className="meta-item">⏱ {resource.estimated_time}</span>}
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}

export default ExternalResources
