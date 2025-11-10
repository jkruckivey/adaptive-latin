import React from 'react';
import './LandingPage.css';

function LandingPage({ onStartLearning, onCreateCourse }) {
  return (
    <div className="landing-page">
      <div className="landing-container">
        <h1 className="landing-title">Adaptive Learning Platform</h1>
        <p className="landing-subtitle">Choose an option to continue</p>

        <div className="landing-actions">
          <button
            className="landing-button"
            onClick={onStartLearning}
          >
            Start Learning
          </button>

          <button
            className="landing-button secondary"
            onClick={onCreateCourse}
          >
            Create a Course
          </button>
        </div>
      </div>
    </div>
  );
}

export default LandingPage;
