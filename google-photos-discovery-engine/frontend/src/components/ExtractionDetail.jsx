import React, { useState } from 'react';
import './ExtractionDetail.css';

export default function ExtractionDetail({ record }) {
  const [expanded, setExpanded] = useState(false);

  const getVal = (val) => val || <span className="not-extracted">Not extracted</span>;

  return (
    <div className="extraction-detail-container" onClick={(e) => e.stopPropagation()}>
      <button 
        className="expand-detail-btn" 
        onClick={(e) => { e.preventDefault(); setExpanded(!expanded); }}
      >
        {expanded ? "▼ Hide Extraction Detail" : "▶ View Extraction Detail"}
      </button>
      
      {expanded && (
        <div className="extraction-detail-panel glass-panel">
          <div className="ed-grid">
            <div className="ed-item">
              <span className="ed-label">Remembered Attributes</span>
              <span className="ed-value">{getVal(record.remembered_attributes)}</span>
            </div>
            <div className="ed-item">
              <span className="ed-label">Forgotten Attributes</span>
              <span className="ed-value">{getVal(record.forgotten_attributes)}</span>
            </div>
            <div className="ed-item">
              <span className="ed-label">Search Strategy</span>
              <span className="ed-value">{getVal(record.search_strategy)}</span>
            </div>
            <div className="ed-item">
              <span className="ed-label">Failure Point</span>
              <span className="ed-value">{getVal(record.failure_point)}</span>
            </div>
            <div className="ed-item">
              <span className="ed-label">Workaround</span>
              <span className="ed-value">{getVal(record.workaround)}</span>
            </div>
            <div className="ed-item">
              <span className="ed-label">Emotional Signal</span>
              <span className="ed-value">{getVal(record.emotional_signal)}</span>
            </div>
            <div className="ed-item">
              <span className="ed-label">Opportunity / Cluster</span>
              <span className="ed-value">Cluster #{record.cluster_id} {record.cluster_label ? `- ${record.cluster_label}` : ''}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
