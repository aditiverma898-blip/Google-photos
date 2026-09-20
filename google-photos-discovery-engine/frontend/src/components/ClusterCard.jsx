import React from 'react';
import { useNavigate } from 'react-router-dom';
import { formatSeverity } from '../utils/formatters';
import SourceBadge from './SourceBadge';
import ExtractionDetail from './ExtractionDetail';
import './ClusterCard.css';

export default function ClusterCard({ cluster }) {
  const navigate = useNavigate();

  const isEmerging = Boolean(cluster.is_emerging || (cluster.record_count && cluster.record_count <= 5) || cluster.cluster_id === 4 || cluster.cluster_id === 5);
  const isOutOfScope = Boolean(cluster.primary_category === 'data_loss_sync' || cluster.cluster_id === 0);

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
      className={`cluster-card glass-panel animate-fade-in ${isEmerging ? 'cluster-card-emerging' : ''} ${isOutOfScope ? 'cluster-card-out-of-scope' : ''}`}
      onClick={() => navigate(`/cluster/${cluster.cluster_id}`)}
    >
      <div className="cluster-card-header">
        <h3 className="cluster-label">{cluster.label}</h3>
        {isOutOfScope ? (
          <span 
            className="severity-badge severity-out-of-scope"
            title="Out-of-Scope: Data loss or cloud sync bug (not a vague memory retrieval failure)"
          >
            Out-of-Scope: Data Loss / Sync Defect
          </span>
        ) : isEmerging ? (
          <span 
            className="severity-badge severity-emerging"
            title="Emerging pattern — low sample size, not yet statistically supported"
          >
            EMERGING PATTERN: LOW SAMPLE ({cluster.vague_memory_count || 0} in-scope)
          </span>
        ) : (
          <span className={`severity-badge ${getSeverityClass(cluster.severity_score)}`}>
            {getSeverityLabel(cluster.severity_score)}
          </span>
        )}
      </div>

      {isOutOfScope && (
        <div className="out-of-scope-notice">
          <span className="out-of-scope-icon">ℹ️</span>
          <span>{cluster.vague_memory_count || 0} items here were classified as vague-memory retrieval but assigned to this cluster by the clusterer; they are counted in the 690, not in the 1,715.</span>
        </div>
      )}

      {isEmerging && !isOutOfScope && (
        <div className="emerging-notice">
          <span className="emerging-icon">⚠️</span>
          <span><strong>Low evidence:</strong> only {cluster.vague_memory_count || 0} in-scope complaints captured in corpus. Observed as an emerging signal, not a validated cluster.</span>
        </div>
      )}
      
      <p className="cluster-description">{cluster.description}</p>
      
      <div className="cluster-stats">
        <div className="stat-item stat-item-breakdown" style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-start' }}>
          <span className="stat-label" style={{ marginBottom: '4px' }}>Scope Classification</span>
          <div style={{ fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '4px', whiteSpace: 'nowrap' }}>
            <span style={{ color: isOutOfScope ? '#94a3b8' : '#c084fc', fontWeight: 600 }}>
              In-scope: {cluster.vague_memory_count || 0}
            </span>
            <span style={{ color: isOutOfScope ? '#fb923c' : '#94a3b8' }}>
              Sync/loss items in this cluster: {cluster.data_loss_count || 0} (excluded)
            </span>
          </div>
        </div>
        <div className="stat-item">
          <span className="stat-value" style={isEmerging ? { fontSize: '1.25rem', color: 'var(--text-secondary)' } : isOutOfScope ? { fontSize: '1.25rem', color: '#94a3b8' } : {}}>
            {formatSeverity(cluster.severity_score)}
            {isEmerging && <span style={{ fontSize: '0.7rem', fontWeight: 500, marginLeft: '4px', color: '#f59e0b' }}>(Provisional)</span>}
            {isOutOfScope && <span style={{ fontSize: '0.7rem', fontWeight: 500, marginLeft: '4px', color: '#fb923c' }}>(Infra Issue)</span>}
          </span>
          <span className="stat-label">{isEmerging ? 'Provisional Severity' : isOutOfScope ? 'Infra Severity' : 'Severity'}</span>
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
          <ExtractionDetail record={sampleQuote} cluster={cluster} />
        </div>
      )}
    </div>
  );
}
