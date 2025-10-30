// src/components/Dashboard.jsx
import { useContext } from 'react';
import { LearnerContext } from '../App';
import ContentRenderer from './ContentRenderer';
import ProgressDashboard from './ProgressDashboard';

function Dashboard() {
  const { learnerId, progress } = useContext(LearnerContext);

  // This is a simplified version of the main app view
  // In a real app, you would fetch and manage content here

  return (
    <div className="main-content">
      <div className="chat-column">
        <ContentRenderer content={{ type: 'lesson', title: 'Welcome!', paragraphs: ['Select a concept to begin.'] }} />
      </div>
      <div className="progress-column">
        <ProgressDashboard />
      </div>
    </div>
  );
}

export default Dashboard;
