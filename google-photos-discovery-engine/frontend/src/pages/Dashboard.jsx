import React, { useState, useEffect } from 'react';
import axios from 'axios';
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
              <div className="coverage-header">
                <h3>Source Coverage</h3>
                <span className="coverage-total">{coverage.total_corpus} complaints across {Object.keys(coverage.source_counts || {}).length} sources</span>
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
        <h2>Failure Clusters</h2>
        {errors.clusters ? (
          <div className="error-state glass-panel" style={{ color: 'var(--text-secondary)', padding: '2rem', textAlign: 'center' }}>Failed to load clusters data.</div>
        ) : (
          <div className="grid grid-cols-3">
            {clusters.map(cluster => (
              <ClusterCard key={cluster.cluster_id} cluster={cluster} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
