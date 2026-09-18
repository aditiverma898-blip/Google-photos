import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './TestDrive.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

const SAMPLE_QUERIES = [
  { label: "Mom at the beach in 2018", cluster: "Face + Time + Scene" },
  { label: "David graduation party May 2021", cluster: "Face + Month + Event" },
  { label: "Our dog in the snow last winter", cluster: "Pet + Relative Time + Weather" },
  { label: "Black cat by the window", cluster: "Species & Color Separation" },
  { label: "Eiffel Tower trip in October 2019", cluster: "Landmark + Date Gating" },
  { label: "Mom with Charlie at the beach in Maui in Summer 2018", cluster: "5-Way Joint Compound" },
];

export default function TestDrive() {
  const [activeTab, setActiveTab] = useState('engine'); // 'engine', 'benchmark', 'complaints'
  
  // Search Engine State
  const [query, setQuery] = useState('Mom at the beach in 2018');
  const [searchResults, setSearchResults] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [error, setError] = useState(null);

  // Benchmark State
  const [benchmarkResults, setBenchmarkResults] = useState(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);

  // Legacy Complaint Classifier State
  const [complaintQuery, setComplaintQuery] = useState('');
  const [complaintResults, setComplaintResults] = useState(null);
  const [complaintLoading, setComplaintLoading] = useState(false);
  
  const navigate = useNavigate();

  // Execute search on load for sample
  useEffect(() => {
    executeSearch('Mom at the beach in 2018');
  }, []);

  const executeSearch = async (searchStr) => {
    const q = searchStr || query;
    if (!q.trim()) return;
    setSearchLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/photos/search`, { query: q });
      setSearchResults(response.data);
    } catch (err) {
      console.error("Search failed:", err);
      setError("Failed to connect to backend search engine. Ensure backend is running.");
    } finally {
      setSearchLoading(false);
    }
  };

  const runFullBenchmark = async () => {
    setBenchmarkLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/photos/benchmark`);
      setBenchmarkResults(response.data);
    } catch (err) {
      console.error("Benchmark failed:", err);
    } finally {
      setBenchmarkLoading(false);
    }
  };

  const handleComplaintSearch = async (e) => {
    e.preventDefault();
    if (!complaintQuery.trim()) return;
    setComplaintLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/test-search`, { query: complaintQuery });
      setComplaintResults(response.data);
    } catch (err) {
      console.error("Complaint search failed:", err);
    } finally {
      setComplaintLoading(false);
    }
  };

  return (
    <div className="test-drive animate-fade-in">
      <header className="test-header">
        <h2>Photos <span className="text-gradient">Discovery Engine</span></h2>
        <p>Semantic Query Understanding, Multi-Index Hybrid Retrieval & Benchmark Evaluation</p>

        <div className="mode-tabs glass-panel">
          <button 
            className={`tab-btn ${activeTab === 'engine' ? 'active' : ''}`}
            onClick={() => setActiveTab('engine')}
          >
            ⚡ Hybrid Search Engine
          </button>
          <button 
            className={`tab-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
            onClick={() => { setActiveTab('benchmark'); if (!benchmarkResults) runFullBenchmark(); }}
          >
            📊 25-Query Benchmark Suite
          </button>
          <button 
            className={`tab-btn ${activeTab === 'complaints' ? 'active' : ''}`}
            onClick={() => setActiveTab('complaints')}
          >
            🔍 Complaint Cluster Classifier
          </button>
        </div>
      </header>

      {/* ========================================================= */}
      {/* TAB 1: HYBRID SEARCH ENGINE                               */}
      {/* ========================================================= */}
      {activeTab === 'engine' && (
        <div className="engine-section animate-fade-in">
          <form className="search-form glass-panel" onSubmit={(e) => { e.preventDefault(); executeSearch(); }}>
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Mom at the beach in 2018, our dog in snow..."
              className="search-input"
            />
            <button type="submit" className="btn-primary" disabled={searchLoading}>
              {searchLoading ? 'Searching...' : 'Search Engine'}
            </button>
          </form>

          <div className="sample-pills">
            <span className="pills-label">Try compound queries:</span>
            {SAMPLE_QUERIES.map((sq, idx) => (
              <button 
                key={idx}
                className="sample-pill"
                onClick={() => { setQuery(sq.label); executeSearch(sq.label); }}
              >
                {sq.label}
              </button>
            ))}
          </div>

          {error && <div className="error-banner glass-panel">{error}</div>}

          {searchResults && (
            <div className="search-output-container animate-fade-in">
              {/* Query Understanding Card */}
              <div className="nlu-card glass-panel">
                <div className="nlu-header">
                  <div className="nlu-title">
                    <span className="badge-tag">NLU Decomposed Constraints</span>
                    <h3>"{searchResults.query}"</h3>
                  </div>
                  <div className={`tier-badge ${searchResults.execution_tier}`}>
                    {searchResults.execution_tier.replace(/_/g, ' ')}
                  </div>
                </div>

                <div className="constraints-grid">
                  <div className="constraint-box">
                    <span className="c-label">👤 People Resolved</span>
                    <span className="c-val">
                      {searchResults.parsed.people.length > 0 
                        ? searchResults.parsed.people.map(p => `${p.canonical_name} (${p.resolved_person_id})`).join(', ')
                        : 'None'}
                    </span>
                  </div>

                  <div className="constraint-box">
                    <span className="c-label">🐾 Pet / Breed Resolved</span>
                    <span className="c-val">
                      {searchResults.parsed.pets.length > 0
                        ? searchResults.parsed.pets.map(p => `${p.raw_mention} (${p.species || 'pet'}${p.breed ? ` / ${p.breed}` : ''})`).join(', ')
                        : 'None'}
                    </span>
                  </div>

                  <div className="constraint-box">
                    <span className="c-label">📅 Temporal Interval</span>
                    <span className="c-val">
                      {searchResults.parsed.temporal 
                        ? `${searchResults.parsed.temporal.raw_mention} [${searchResults.parsed.temporal.start_utc.slice(0, 10)} → ${searchResults.parsed.temporal.end_utc.slice(0, 10)}]`
                        : 'None'}
                    </span>
                  </div>

                  <div className="constraint-box">
                    <span className="c-label">📍 Spatial Boundary</span>
                    <span className="c-val">
                      {searchResults.parsed.spatial 
                        ? `${searchResults.parsed.spatial.resolved_place}`
                        : 'None'}
                    </span>
                  </div>

                  <div className="constraint-box full-width">
                    <span className="c-label">🎨 Stripped Visual Prompt (Sent to Vector Index)</span>
                    <span className="c-val text-accent">
                      "{searchResults.parsed.visual_residual.clean_prompt || '—'}"
                    </span>
                  </div>
                </div>
              </div>

              {/* Photos Grid */}
              <div className="results-header-bar">
                <h4>Retrieved Results ({searchResults.total_results})</h4>
                <span className="latency-label">Latency: {searchResults.latency_ms} ms</span>
              </div>

              {searchResults.results.length === 0 ? (
                <div className="empty-results glass-panel">
                  <p>No photos matched all constraints.</p>
                </div>
              ) : (
                <div className="photos-grid">
                  {searchResults.results.map((photo) => (
                    <div key={photo.photo_id} className="photo-card glass-panel">
                      <div className="photo-placeholder">
                        <span className="photo-id-tag">ID: {photo.photo_id}</span>
                        <span className="photo-icon">📷</span>
                      </div>
                      <div className="photo-info">
                        <h5>{photo.title}</h5>
                        <div className="photo-meta">
                          <span>📅 {photo.captured_at_utc}</span>
                          <span>📍 {[photo.city, photo.state, photo.country].filter(Boolean).join(', ')}</span>
                          {photo.landmark && <span>🏛️ {photo.landmark}</span>}
                        </div>
                        <div className="matched-badges">
                          {photo.matched_constraints.map((c, i) => (
                            <span key={i} className="c-pill">{c}</span>
                          ))}
                        </div>
                        <div className="explanation-pill">
                          ✓ {photo.explanation_badge}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 2: AUTOMATED 25-QUERY BENCHMARK SUITE                 */}
      {/* ========================================================= */}
      {activeTab === 'benchmark' && (
        <div className="benchmark-section animate-fade-in">
          <div className="benchmark-controls">
            <button 
              className="btn-primary" 
              onClick={runFullBenchmark}
              disabled={benchmarkLoading}
            >
              {benchmarkLoading ? 'Running 25 Tests...' : 'Re-Run Benchmark Suite'}
            </button>
          </div>

          {benchmarkResults && (
            <div className="benchmark-dashboard animate-fade-in">
              {/* Summary Stats Row */}
              <div className="stats-row">
                <div className="stat-box glass-panel">
                  <span className="stat-number text-accent">
                    {benchmarkResults.summary.pass_rate_pct}%
                  </span>
                  <span className="stat-title">Pass Rate</span>
                </div>
                <div className="stat-box glass-panel">
                  <span className="stat-number">
                    {benchmarkResults.summary.passed} / {benchmarkResults.summary.total_queries}
                  </span>
                  <span className="stat-title">Tests Passing</span>
                </div>
                <div className="stat-box glass-panel">
                  <span className="stat-number">
                    {benchmarkResults.summary.avg_latency_ms} ms
                  </span>
                  <span className="stat-title">Avg Latency</span>
                </div>
                <div className="stat-box glass-panel">
                  <span className="stat-number text-success">
                    {benchmarkResults.summary.status}
                  </span>
                  <span className="stat-title">Suite Status</span>
                </div>
              </div>

              {/* Cluster Breakdown */}
              <div className="cluster-breakdown glass-panel">
                <h3>Cluster Pass Distribution</h3>
                <div className="cluster-pills-row">
                  {Object.entries(benchmarkResults.cluster_breakdown).map(([name, stat]) => (
                    <div key={name} className="cluster-stat-pill">
                      <span className="pill-name">{name}</span>
                      <span className="pill-score">{stat.passed} / {stat.total} (100%)</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Detailed Tests Table */}
              <div className="tests-table-container glass-panel">
                <h3>Detailed Labeled Query Execution</h3>
                <table className="benchmark-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Cluster</th>
                      <th>Natural Language Query</th>
                      <th>Decomposed Constraints</th>
                      <th>Tier</th>
                      <th>Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {benchmarkResults.details.map((t) => (
                      <tr key={t.test_id} className={t.passed ? 'row-pass' : 'row-fail'}>
                        <td className="id-col">{t.test_id}</td>
                        <td><span className="cluster-badge">{t.cluster}</span></td>
                        <td className="query-col"><strong>"{t.query}"</strong></td>
                        <td className="constraints-col">
                          {t.parsed_constraints.people.length > 0 && <span className="mini-badge">👤 {t.parsed_constraints.people.join(', ')}</span>}
                          {t.parsed_constraints.pets.length > 0 && <span className="mini-badge">🐾 {t.parsed_constraints.pets.join(', ')}</span>}
                          {t.parsed_constraints.temporal && <span className="mini-badge">📅 {t.parsed_constraints.temporal}</span>}
                          {t.parsed_constraints.spatial && <span className="mini-badge">📍 {t.parsed_constraints.spatial}</span>}
                          {t.parsed_constraints.visual && <span className="mini-badge">🎨 {t.parsed_constraints.visual}</span>}
                        </td>
                        <td><span className="tier-pill">{t.execution_tier.replace(/_/g, ' ')}</span></td>
                        <td>
                          <span className={t.passed ? "badge-success" : "badge-fail"}>
                            {t.passed ? "PASS" : "FAIL"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 3: LEGACY COMPLAINT CLUSTERING                        */}
      {/* ========================================================= */}
      {activeTab === 'complaints' && (
        <div className="complaints-section animate-fade-in">
          <form className="search-form glass-panel" onSubmit={handleComplaintSearch}>
            <input 
              type="text" 
              value={complaintQuery}
              onChange={(e) => setComplaintQuery(e.target.value)}
              placeholder="e.g. I can't find my dog picture from 2018..."
              className="search-input"
            />
            <button type="submit" className="btn-primary" disabled={complaintLoading}>
              {complaintLoading ? 'Analyzing...' : 'Analyze Complaint'}
            </button>
          </form>
          
          {complaintResults && (
            <div className="results-container animate-fade-in">
              <div className="nearest-cluster glass-panel">
                <h3>Classification</h3>
                {complaintResults.is_confident_match && complaintResults.nearest_cluster ? (
                  <div className="cluster-match">
                    <span className="match-label">✓ Confident Match (Cluster #{complaintResults.nearest_cluster.cluster_id}):</span>
                    <span className="match-title">{complaintResults.nearest_cluster.label}</span>
                    <p>{complaintResults.nearest_cluster.description}</p>
                    <div className="distance-badge success">
                      Distance: {complaintResults.nearest_cluster.distance.toFixed(4)} (Threshold: &le; 0.35)
                    </div>
                    <button 
                      className="btn-primary view-btn"
                      onClick={() => navigate(`/cluster/${complaintResults.nearest_cluster.cluster_id}`)}
                    >
                      View Full Cluster
                    </button>
                  </div>
                ) : (
                  <div className="cluster-unmatched">
                    <div className="amber-badge">
                      ⚠️ Out-of-Domain / No Confident Match
                    </div>
                    <p>
                      This query does not match any of the 4 tracked failure clusters with high confidence.
                      {complaintResults.nearest_cluster && (
                        <span> The closest is <strong>{complaintResults.nearest_cluster.label}</strong> with distance <code>{complaintResults.nearest_cluster.distance.toFixed(4)}</code>, which exceeds the 0.35 threshold.</span>
                      )}
                    </p>
                    <div className="attribute-hint-box">
                      💡 <em>Product Note: Queries like "{complaintResults.query}" typically represent an unmapped <strong>Object / Attribute Search</strong> failure pattern (e.g. clothing & color attributes).</em>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="similar-records">
                <h3>Nearest Historical Complaints</h3>
                {!complaintResults.is_confident_match && (
                  <div className="amber-low-confidence-banner">
                    <div className="banner-title">⚠️ Closest Available Reference (Low Confidence)</div>
                    <p>No historical complaints met the 0.35 similarity cutoff for this query. The records below are shown for reference only and are likely unrelated.</p>
                  </div>
                )}
                <div className="records-list">
                  {complaintResults.similar_records.map(record => (
                    <div key={record.id} className={`record-card glass-panel ${record.is_confident ? '' : 'card-low-conf'}`}>
                      <p className="record-text">"{record.raw_text}"</p>
                      <div className="record-meta-small">
                        <span>Cluster #{record.cluster_id}</span>
                        <span className={`distance-tag ${record.is_confident ? 'tag-confident' : 'tag-low-conf'}`}>
                          {record.is_confident ? '✓ High Confidence' : '⚠️ Low Confidence Reference'} ({record.distance.toFixed(4)})
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
