import React from 'react';
import '../index.css'; // Ensure styles are available

const SkeletonLoader = ({ type = 'text', lines = 3 }) => {
    const renderLines = () => {
        return Array.from({ length: lines }).map((_, index) => (
            <div key={index} className="skeleton-line" style={{ width: `${Math.random() * 40 + 60}%` }}></div>
        ));
    };

    if (type === 'card') {
        return (
            <div className="skeleton-card">
                <div className="skeleton-header"></div>
                <div className="skeleton-body">
                    {renderLines()}
                </div>
            </div>
        );
    }

    if (type === 'question') {
        return (
            <div className="skeleton-question">
                <div className="skeleton-scenario"></div>
                <div className="skeleton-text"></div>
                <div className="skeleton-options">
                    <div className="skeleton-option"></div>
                    <div className="skeleton-option"></div>
                    <div className="skeleton-option"></div>
                    <div className="skeleton-option"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="skeleton-text-block">
            {renderLines()}
        </div>
    );
};

export default SkeletonLoader;
