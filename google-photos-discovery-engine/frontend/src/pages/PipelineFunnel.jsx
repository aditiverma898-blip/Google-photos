import React from 'react';
import './PipelineFunnel.css';
import statsData from '../data/stats.json';

export default function PipelineFunnel() {
  const { funnel, clusters } = statsData;

  return (
    <div className="funnel-container animate-fade-in">
      <div className="funnel-header">
        <span className="funnel-badge">Diagnostic Pass</span>
        <h1 className="funnel-title">Data Ingestion &amp; Pipeline Funnel</h1>
        <p className="funnel-subtitle">
          Auditing the full journey of approximately 12,000 raw scraped items across Play Store, YouTube, Reddit, 
          and Support Communities through the Gemini extraction and clustering layers.
        </p>
      </div>

      {/* Root Cause Callout */}
      <div className="funnel-diagnosis-alert">
        <h3>🔍 Diagnostic Findings: Where did the {funnel.total_ingested.toLocaleString()} items go?</h3>
        <p>
          <strong>1. Ingestion Succeeded:</strong> Exactly <strong>{funnel.total_ingested.toLocaleString()}</strong> raw feedback items exist on disk across batch files.<br />
          <strong>2. LLM Evaluation Pass:</strong> The background verification scripts have completely drained the queue, processing <strong>{funnel.evaluated_relevant.toLocaleString()}</strong> distinct, relevant search complaints.<br />
          <strong>3. Strict Relevance Filter:</strong> Of the {funnel.evaluated_relevant.toLocaleString()} items, <strong>{funnel.out_of_scope.toLocaleString()}</strong> were firmly out of scope for semantic search (Data Loss, Sync Defects, Locked Folders).<br />
          <strong>4. Clean Extraction &amp; Clustering:</strong> The remaining <strong>{funnel.in_scope.toLocaleString()}</strong> items were successfully parsed as Vague Memory Retrieval Failures and clustered into 5 product-actionable insights.
        </p>
      </div>

      {/* Horizontal Visual Flow */}
      <div className="funnel-flow-banner" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', padding: '2rem 1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', flexWrap: 'wrap' }}>
        <div className="funnel-flow-step" style={{ textAlign: 'center', padding: '1rem', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', minWidth: '160px' }}>
          <span className="flow-step-num" style={{ fontSize: '2rem', fontWeight: 'bold', display: 'block', color: 'var(--text-primary)' }}>{funnel.total_ingested.toLocaleString()}</span>
          <span className="flow-step-lbl" style={{ display: 'block', color: 'var(--text-secondary)' }}>Raw Ingested</span>
        </div>
        <span className="funnel-arrow" style={{ color: '#475569', fontSize: '1.5rem' }}>→</span>
        <div className="funnel-flow-step" style={{ textAlign: 'center', padding: '1rem', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', minWidth: '160px' }}>
          <span className="flow-step-num" style={{ fontSize: '2rem', fontWeight: 'bold', display: 'block', color: '#facc15' }}>{funnel.evaluated_relevant.toLocaleString()}</span>
          <span className="flow-step-lbl" style={{ display: 'block', color: 'var(--text-secondary)' }}>Evaluated</span>
        </div>
        <span className="funnel-arrow" style={{ color: '#475569', fontSize: '1.5rem' }}>→</span>
        <div className="funnel-flow-step" style={{ textAlign: 'center', padding: '1rem', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', minWidth: '160px', border: '1px dashed rgba(251, 146, 60, 0.5)' }}>
          <span className="flow-step-num" style={{ fontSize: '2rem', fontWeight: 'bold', display: 'block', color: '#fb923c' }}>{funnel.out_of_scope.toLocaleString()}</span>
          <span className="flow-step-lbl" style={{ display: 'block', color: 'var(--text-secondary)' }}>Out-of-Scope</span>
          <span style={{ fontSize: '0.75rem', color: '#fdba74' }}>Data Loss / Sync</span>
        </div>
        <span className="funnel-arrow" style={{ color: '#475569', fontSize: '1.5rem' }}>/</span>
        <div className="funnel-flow-step" style={{ textAlign: 'center', padding: '1rem', background: 'rgba(168, 85, 247, 0.1)', borderRadius: '8px', minWidth: '160px', border: '1px solid rgba(168, 85, 247, 0.4)' }}>
          <span className="flow-step-num" style={{ fontSize: '2rem', fontWeight: 'bold', display: 'block', color: '#c084fc' }}>{funnel.in_scope.toLocaleString()}</span>
          <span className="flow-step-lbl" style={{ display: 'block', color: 'var(--text-secondary)' }}>In-Scope</span>
          <span style={{ fontSize: '0.75rem', color: '#d8b4fe' }}>Vague Memory</span>
        </div>
      </div>

      <div className="funnel-grid" style={{ marginTop: '2rem' }}>
        <div className="funnel-card glass-panel" style={{ gridColumn: '1 / -1' }}>
          <h3>Verified Clusters Breakdown</h3>
          <table className="cluster-table" style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem', color: '#94a3b8' }}>ID</th>
                <th style={{ padding: '0.5rem', color: '#94a3b8' }}>Cluster Label</th>
                <th style={{ padding: '0.5rem', color: '#94a3b8' }}>Total Verified</th>
                <th style={{ padding: '0.5rem', color: '#94a3b8' }}>Primary Category</th>
              </tr>
            </thead>
            <tbody>
              {clusters.map(c => (
                <tr key={c.cluster_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '0.75rem 0.5rem' }}>{c.cluster_id}</td>
                  <td style={{ padding: '0.75rem 0.5rem' }}><strong>{c.label}</strong></td>
                  <td style={{ padding: '0.75rem 0.5rem', fontWeight: 'bold' }}>{c.record_count}</td>
                  <td style={{ padding: '0.75rem 0.5rem' }}>
                    {c.primary_category === 'vague_memory_retrieval' 
                      ? <span style={{ color: '#c084fc', background: 'rgba(192,132,252,0.1)', padding: '4px 8px', borderRadius: '4px', fontSize: '0.85em' }}>Vague Memory (In-Scope)</span> 
                      : <span style={{ color: '#fb923c', background: 'rgba(251,146,60,0.1)', padding: '4px 8px', borderRadius: '4px', fontSize: '0.85em' }}>Data Loss (Out-of-Scope)</span>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
