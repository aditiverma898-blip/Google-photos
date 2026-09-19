import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import ClusterCard from '../components/ClusterCard';
import './Dashboard.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://google-photos.onrender.com/api';

export default function Dashboard() {
  const [clusters, setClusters] = useState([]);
  const [synthesis, setSynthesis] = useState([]);
  const [coverage, setCoverage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({ clusters: false, synthesis: false, coverage: false });

  useEffect(() => {
    if (!import.meta.env.VITE_API_URL) {
      console.warn("VITE_API_URL is not set in the environment. Falling back to production URL, which may cause CORS or 500 errors if the production server is unstable.");
    }

    const fetchData = async () => {
      try {
        const results = await Promise.allSettled([
          axios.get(`${API_BASE_URL}/clusters`),
          axios.get(`${API_BASE_URL}/synthesis`),
          axios.get(`${API_BASE_URL}/coverage`)
        ]);
        
        const [clustersRes, synthesisRes, coverageRes] = results;
        const newErrors = { clusters: false, synthesis: false, coverage: false };
        
        if (clustersRes.status === 'fulfilled') {
          const cl = clustersRes.value.data.clusters || [];
          setClusters(cl);
          
          // Audit missing sources across all cluster sample quotes
          let totalQuotes = 0;
          let missingQuotes = 0;
          const missingIds = [];
          cl.forEach(c => {
            if (c.representative_quotes) {
              c.representative_quotes.forEach(q => {
                totalQuotes++;
                const src = typeof q === 'object' ? q.source : null;
                if (!src || src.toLowerCase() === 'unknown') {
                  missingQuotes++;
                  if (typeof q === 'object' && q.id) missingIds.push(q.id);
                }
              });
            }
          });
          if (missingQuotes > 0) {
            console.warn(
              `[Photos Discovery Engine] ⚠️ Dashboard Audit: ${missingQuotes} / ${totalQuotes} cluster sample complaints have MISSING source platforms! ` +
              `IDs requiring backfill:`, missingIds
            );
          } else {
            console.log(`[Photos Discovery Engine] ✓ Dashboard Audit: All ${totalQuotes} cluster sample complaints have verified source tags.`);
          }
        } else {
          console.error('Failed to load clusters:', clustersRes.reason);
          newErrors.clusters = true;
        }

        if (synthesisRes.status === 'fulfilled') {
          setSynthesis(synthesisRes.value.data.synthesis || []);
        } else {
          console.error('Failed to load synthesis:', synthesisRes.reason);
          newErrors.synthesis = true;
        }

        if (coverageRes.status === 'fulfilled') {
          setCoverage(coverageRes.value.data);
        } else {
          console.error('Failed to load coverage:', coverageRes.reason);
          newErrors.coverage = true;
        }

        setErrors(newErrors);
      } catch (error) {
        console.error('Unexpected error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Analyzing millions of parameters...</p>
      </div>
    );
  }

  const inScopeClusters = clusters.filter(
    c => c.primary_category === 'vague_memory_retrieval' || (c.cluster_id !== 0 && c.primary_category !== 'data_loss_sync')
  );
  const outOfScopeClusters = clusters.filter(
    c => c.primary_category === 'data_loss_sync' || c.cluster_id === 0
  );

  return (
    <div className="dashboard animate-fade-in">
      <header className="dashboard-header">
        <h1>Vague Retrieval <span className="text-gradient">Insights</span></h1>
        <p>AI-synthesized analysis of user search failures in Google Photos</p>
      </header>
      
      {(synthesis.length > 0 || errors.synthesis) && (
        <section className="synthesis-section">
          <h2>Strategic Insights</h2>
          {errors.synthesis ? (
            <div className="error-state glass-panel" style={{ color: 'var(--text-secondary)', padding: '2rem', textAlign: 'center' }}>Failed to load synthesis data.</div>
          ) : (
            <div className="synthesis-grid">
              {synthesis.map((qa, index) => (
                <div key={qa.question_id || index} className="qa-card glass-panel">
                  <h4>{qa.question || qa.question_text}</h4>
                  <p>{qa.answer || qa.answer_text}</p>
                  
                  {qa.evidence && qa.evidence.verbatim_quotes && (
                    <div className="evidence-quotes">
                      {qa.evidence.verbatim_quotes.map((quote, i) => (
                        <blockquote key={i}>"{quote}"</blockquote>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {((coverage && coverage.total_corpus > 0) || errors.coverage) && (
        <section className="coverage-section">
          {errors.coverage ? (
            <div className="error-state glass-panel" style={{ color: 'var(--text-secondary)', padding: '2rem', textAlign: 'center' }}>Failed to load source coverage data.</div>
          ) : (
            <div className="coverage-bar glass-panel">
              <div className="coverage-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.5rem' }}>
                <div style={{ display: 'flex', gap: '2.5rem', flexWrap: 'wrap' }}>
                  <div>
                    <h3 style={{ fontSize: '0.95rem', marginBottom: '0.2rem', color: 'var(--text-secondary)' }}>Raw Items Ingested</h3>
                    <div style={{ fontSize: '1.35rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                      {coverage.total_corpus.toLocaleString()} <span style={{ fontSize: '0.85rem', fontWeight: 'normal', color: 'var(--text-secondary)' }}>across {Object.keys(coverage.source_counts || {}).length} sources</span>
                    </div>
                  </div>
                  <div>
                    <h3 style={{ fontSize: '0.95rem', marginBottom: '0.2rem', color: 'var(--accent-color, #c4b5fd)' }}>In-Scope Retrieval Complaints</h3>
                    <div style={{ fontSize: '1.35rem', fontWeight: 'bold', color: '#c084fc' }}>
                      {(coverage.vague_memory_complaints || 0).toLocaleString()} <span style={{ fontSize: '0.8rem', fontWeight: 'normal', color: 'var(--text-secondary)' }}>vague memory</span>
                    </div>
                  </div>
                  <div>
                    <h3 style={{ fontSize: '0.95rem', marginBottom: '0.2rem', color: '#fb923c' }}>Out-of-Scope Bugs</h3>
                    <div style={{ fontSize: '1.35rem', fontWeight: 'bold', color: '#fdba74' }}>
                      {(coverage.data_loss_complaints || 0).toLocaleString()} <span style={{ fontSize: '0.8rem', fontWeight: 'normal', color: 'var(--text-secondary)' }}>data loss / sync</span>
                    </div>
                  </div>
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', maxWidth: '270px', textAlign: 'right', marginTop: '0.2rem' }}>
                  💡 Classified via batched LLM pass into vague memory retrieval vs data loss/sync bugs — <Link to="/funnel" style={{ color: 'var(--accent-color, #c4b5fd)', textDecoration: 'underline' }}>see funnel.</Link>
                </div>
              </div>
              <div className="coverage-stats">
                {Object.entries(coverage.source_counts || {})
                  .sort((a, b) => b[1] - a[1])
                  .map(([source, count]) => (
                  <div key={source} className="coverage-stat-item">
                    <span className="source-name">{source}:</span>
                    <span className="source-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      <section className="clusters-section">
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <h2 style={{ margin: 0 }}>Vague Memory Retrieval Failures</h2>
            <span style={{ 
              background: 'rgba(168, 85, 247, 0.2)', 
              color: '#c084fc', 
              border: '1px solid rgba(168, 85, 247, 0.4)', 
              borderRadius: '999px', 
              fontSize: '0.72rem', 
              fontWeight: 700, 
              padding: '0.2rem 0.6rem',
              letterSpacing: '0.5px'
            }}>
              PRIMARY FOCUS • IN-SCOPE
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.35rem', fontSize: '0.92rem' }}>
            User memory vs retrieval gap: users recall partial cues (background objects, relative dates, visual aesthetics, events) but Google Photos search fails to bridge the gap.
          </p>
        </div>

        {errors.clusters ? (
          <div className="error-state glass-panel" style={{ color: 'var(--text-secondary)', padding: '2rem', textAlign: 'center' }}>Failed to load clusters data.</div>
        ) : (
          <div className="grid grid-cols-3">
            {inScopeClusters.map(cluster => (
              <ClusterCard key={cluster.cluster_id} cluster={cluster} />
            ))}
          </div>
        )}
      </section>

      {outOfScopeClusters.length > 0 && (
        <section className="clusters-section" style={{ marginTop: '3.5rem' }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
              <h2 style={{ margin: 0, color: '#fdba74' }}>Data Loss & Sync Defects</h2>
              <span style={{ 
                background: 'rgba(251, 146, 60, 0.15)', 
                color: '#fdba74', 
                border: '1px solid rgba(251, 146, 60, 0.35)', 
                borderRadius: '999px', 
                fontSize: '0.72rem', 
                fontWeight: 700, 
                padding: '0.2rem 0.6rem',
                letterSpacing: '0.5px'
              }}>
                OUT-OF-SCOPE CONTEXT • ENGINEERING DEFECTS
              </span>
            </div>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.35rem', fontSize: '0.92rem' }}>
              Complaints where content was deleted, lost, or misplaced due to cloud sync failures, locked folder bugs, or device backup corruption. Retained for complete transparency across the verified corpus.
            </p>
          </div>

          <div className="grid grid-cols-3">
            {outOfScopeClusters.map(cluster => (
              <ClusterCard key={cluster.cluster_id} cluster={cluster} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
