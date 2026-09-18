import React from 'react';
import { useNavigate } from 'react-router-dom';
import { formatSeverity } from '../utils/formatters';
import SourceBadge from './SourceBadge';
import ExtractionDetail from './ExtractionDetail';
import './ClusterCard.css';

export default function ClusterCard({ cluster }) {
  const navigate = useNavigate();

  const getSeverityClass = (score) => {
    if (score > 0.55) return 'severity-high';
    if (score > 0.48) return 'severity-medium';
    return 'severity-low';
  };

  const getSeverityLabel = (score) => {
    if (score > 0.55) return 'High Churn Risk';
    if (score > 0.48) return 'Medium Frustration';
    return 'Nuisance';
  };

  const sampleQuote = cluster.representative_quotes && cluster.representative_quotes.length > 0
    ? (typeof cluster.representative_quotes[0] === 'object'
        ? cluster.representative_quotes[0]
        : { text: cluster.representative_quotes[0], source: null })
    : null;

  return (
    <div 
      className="cluster-card glass-panel animate-fade-in"
      onClick={() => navigate(`/cluster/${cluster.cluster_id}`)}
    >
      <div className="cluster-card-header">
        <h3 className="cluster-label">{cluster.label}</h3>
        <span className={`severity-badge ${getSeverityClass(cluster.severity_score)}`}>
          {getSeverityLabel(cluster.severity_score)}
        </span>
      </div>
      
      <p className="cluster-description">{cluster.description}</p>
      
      <div className="cluster-stats">
        <div className="stat-item stat-item-breakdown" style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-start' }}>
          <span className="stat-label" style={{ marginBottom: '4px' }}>Complaints Verification</span>
          <div style={{ display: 'flex', gap: '8px', fontSize: '13px' }}>
            <span style={{ color: '#4ade80' }} title="Confirmed Relevant">✓ {cluster.confirmed_relevant || 0}</span>
            <span style={{ color: '#f87171' }} title="Confirmed Irrelevant">✗ {cluster.confirmed_irrelevant || 0}</span>
            <span style={{ color: '#9ca3af' }} title="Unverified">? {cluster.unverified || 0}</span>
          </div>
        </div>
        <div className="stat-item">
          <span className="stat-value">{formatSeverity(cluster.severity_score)}</span>
          <span className="stat-label">Severity</span>
        </div>
      </div>
      
      <div className="cluster-tags">
        {cluster.top_failure_points.slice(0, 3).map((fp, i) => (
          <span key={i} className="cluster-tag">{fp}</span>
        ))}
      </div>

      {sampleQuote && (
        <div className="cluster-quote-preview">
          <div className="quote-preview-header">
            <span className="quote-label">Sample Complaint</span>
            <SourceBadge 
              source={sampleQuote.source} 
              recordId={sampleQuote.id}
              rawText={sampleQuote.text} 
            />
          </div>
          <p className="quote-preview-text">
            "{sampleQuote.text}"
          </p>
          <ExtractionDetail record={sampleQuote} />
        </div>
      )}
    </div>
  );
}
