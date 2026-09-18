import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './EvidenceExplorer.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8000/api' 
    : 'https://google-photos.onrender.com/api');

export default function EvidenceExplorer() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedSource, setSelectedSource] = useState('All');
  const [selectedCluster, setSelectedCluster] = useState('All');
  const [selectedEmotion, setSelectedEmotion] = useState('All');
  const [page, setPage] = useState(1);
  const limit = 25;

  const fetchEvidence = async (p = 1) => {
    setLoading(true);
    try {
      const params = { page: p, limit };
      if (search.trim()) params.search = search.trim();
      if (selectedSource !== 'All') params.source = selectedSource;
      if (selectedCluster !== 'All') params.cluster_id = parseInt(selectedCluster, 10);
      if (selectedEmotion !== 'All') params.emotion = selectedEmotion;

      const res = await axios.get(`${API_BASE_URL}/evidence`, { params });
      setData(res.data);
      setPage(p);
    } catch (err) {
      console.error('Failed to load evidence:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvidence(1);
  }, [selectedSource, selectedCluster, selectedEmotion]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchEvidence(1);
  };

  const getSourceClass = (src) => {
    const s = String(src || '').toLowerCase();
    if (s.includes('play')) return 'play-store';
    if (s.includes('youtube')) return 'youtube';
    if (s.includes('reddit')) return 'reddit';
    if (s.includes('app_store') || s.includes('app store')) return 'app-store';
    if (s.includes('support') || s.includes('community') || s.includes('forum')) return 'community';
    return 'play-store';
  };

  const sourcesList = [
    { label: 'All Sources', value: 'All' },
    { label: 'Play Store', value: 'Play Store' },
    { label: 'YouTube Comments', value: 'YouTube Comment' },
    { label: 'Reddit', value: 'Reddit' },
    { label: 'App Store', value: 'App Store' },
    { label: 'Support Community', value: 'Google Support Community' }
  ];

  const clustersList = [
    { label: 'All Clusters', value: 'All' },
    { label: '#0: Missing Photos & Albums', value: '0' },
    { label: '#1: Broken Search Functionality', value: '1' },
    { label: '#2: Recent Media Misplacement', value: '2' },
    { label: '#3: UI & Search Redesign', value: '3' }
  ];

  return (
    <div className="evidence-container">
      <div className="evidence-header">
        <span className="evidence-badge">Full Dataset Traceability</span>
        <h1 className="evidence-title">Scraped Evidence Explorer</h1>
        <p className="evidence-subtitle">
          Search, filter, and inspect all <strong>{data ? data.total_corpus.toLocaleString() : '12,000+'}</strong> raw user feedback records 
          scraped across Google Play Store, YouTube Comments, Reddit, Apple App Store, and Google Support Community.
        </p>
      </div>

      {/* Macro Stats */}
      {data && (
        <div className="evidence-stats-grid">
          <div className="evidence-stat-card">
            <span className="stat-label">Total Scraped Evidence</span>
            <span className="stat-value">{data.total_corpus.toLocaleString()}</span>
          </div>
          <div className="evidence-stat-card">
            <span className="stat-label">Play Store Reviews</span>
            <span className="stat-value" style={{ color: '#34d399' }}>
              {(data.source_counts['Play Store'] || 0).toLocaleString()}
            </span>
          </div>
          <div className="evidence-stat-card">
            <span className="stat-label">YouTube Comments</span>
            <span className="stat-value" style={{ color: '#fb7185' }}>
              {(data.source_counts['YouTube Comment'] || 0).toLocaleString()}
            </span>
          </div>
          <div className="evidence-stat-card">
            <span className="stat-label">Reddit Posts</span>
            <span className="stat-value" style={{ color: '#fb923c' }}>
              {(data.source_counts['Reddit'] || 0).toLocaleString()}
            </span>
          </div>
          <div className="evidence-stat-card">
            <span className="stat-label">App Store &amp; Forum</span>
            <span className="stat-value" style={{ color: '#38bdf8' }}>
              {((data.source_counts['App Store'] || 0) + (data.source_counts['Google Support Community'] || 0)).toLocaleString()}
            </span>
          </div>
        </div>
      )}

      {/* Filters Toolbar */}
      <div className="evidence-toolbar">
        <form onSubmit={handleSearchSubmit} className="search-row">
          <input
            type="text"
            className="evidence-search-input"
            placeholder="Search verbatim quotes, failure points, faces, dates, or keywords (e.g. 'locked folder', 'face search', 'timeline')..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </form>

        <div className="filter-row">
          <div className="source-pills-group">
            {sourcesList.map(s => (
              <button
                key={s.value}
                type="button"
                className={`source-pill-btn ${selectedSource === s.value ? 'active' : ''}`}
                onClick={() => setSelectedSource(s.value)}
              >
                {s.label}
              </button>
            ))}
          </div>

          <div className="select-filters">
            <select 
              className="evidence-select"
              value={selectedCluster} 
              onChange={(e) => setSelectedCluster(e.target.value)}
            >
              {clustersList.map(c => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>

            <select 
              className="evidence-select"
              value={selectedEmotion} 
              onChange={(e) => setSelectedEmotion(e.target.value)}
            >
              <option value="All">All Emotional Signals</option>
              <option value="angry">Angry</option>
              <option value="frustrated">Frustrated</option>
              <option value="disappointed">Disappointed</option>
              <option value="neutral">Neutral</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results Header */}
      {data && (
        <div className="evidence-results-bar">
          <span>
            Showing <strong>{data.records.length}</strong> of <strong>{data.total.toLocaleString()}</strong> matching complaints
          </span>
          <span>
            Page {data.page} of {data.pages}
          </span>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem 0', color: '#94a3b8' }}>
          <div className="spinner"></div>
          <p style={{ marginTop: '0.75rem' }}>Loading evidence records...</p>
        </div>
      )}

      {/* Cards List */}
      {!loading && data && data.records.length > 0 && (
        <div className="evidence-list">
          {data.records.map(rec => (
            <div key={rec.id} className="evidence-card">
              <div className="card-top-meta">
                <div className="card-badges-left">
                  <span className={`src-pill ${getSourceClass(rec.source)}`}>
                    {rec.source || 'Play Store'}
                  </span>
                  <span className="cluster-pill-tag">
                    {rec.cluster_name}
                  </span>
                </div>
                <div className="card-tags-right">
                  {rec.photo_type && rec.photo_type !== 'other' && (
                    <span className="attr-tag">📷 {rec.photo_type}</span>
                  )}
                  {rec.emotional_signal && (
                    <span className="attr-tag">
                      {rec.emotional_signal === 'angry' ? '🔥 angry' :
                       rec.emotional_signal === 'frustrated' ? '⚡ frustrated' :
                       rec.emotional_signal === 'disappointed' ? '💧 disappointed' : '💬 neutral'}
                    </span>
                  )}
                  <span className="attr-tag" style={{ color: '#64748b' }}>
                    #{rec.id}
                  </span>
                </div>
              </div>

              <blockquote className="card-quote-text">
                "{rec.raw_text}"
              </blockquote>

              {rec.failure_point && (
                <div className="card-failure-box">
                  <span className="card-failure-label">Failure Point:</span>
                  <span>{rec.failure_point}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && data && data.records.length === 0 && (
        <div style={{ textAlign: 'center', padding: '4rem 0', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '16px' }}>
          <p style={{ fontSize: '1.1rem', color: '#94a3b8' }}>No scraped complaints matched your current search and filters.</p>
          <button 
            type="button" 
            className="pagination-btn"
            style={{ marginTop: '1rem' }}
            onClick={() => { setSearch(''); setSelectedSource('All'); setSelectedCluster('All'); setSelectedEmotion('All'); }}
          >
            Reset Filters
          </button>
        </div>
      )}

      {/* Pagination Controls */}
      {data && data.pages > 1 && (
        <div className="pagination-bar">
          <button
            type="button"
            className="pagination-btn"
            disabled={page <= 1}
            onClick={() => fetchEvidence(page - 1)}
          >
            ← Previous
          </button>
          <span className="page-indicator">
            Page {page} of {data.pages}
          </span>
          <button
            type="button"
            className="pagination-btn"
            disabled={page >= data.pages}
            onClick={() => fetchEvidence(page + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
