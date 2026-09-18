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

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [clustersRes, synthesisRes, coverageRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/clusters`),
          axios.get(`${API_BASE_URL}/synthesis`),
          axios.get(`${API_BASE_URL}/coverage`).catch(() => ({ data: { total_corpus: 0, source_counts: {} } }))
        ]);
        
        const cl = clustersRes.data.clusters || [];
        setClusters(cl);
        setSynthesis(synthesisRes.data.synthesis || []);
        setCoverage(coverageRes.data);

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
      } catch (error) {
        console.error('Error fetching data:', error);
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
      
      {synthesis.length > 0 && (
        <section className="synthesis-section">
          <h2>Strategic Insights</h2>
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
        </section>
      )}

      {coverage && coverage.total_corpus > 0 && (
        <section className="coverage-section">
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
        </section>
      )}

      <section className="clusters-section">
        <h2>Failure Clusters</h2>
        <div className="grid grid-cols-3">
          {clusters.map(cluster => (
            <ClusterCard key={cluster.cluster_id} cluster={cluster} />
          ))}
        </div>
      </section>
    </div>
  );
}
