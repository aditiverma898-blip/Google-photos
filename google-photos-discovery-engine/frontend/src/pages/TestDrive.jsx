import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import SourceBadge from '../components/SourceBadge';
import ExtractionDetail from '../components/ExtractionDetail';
import './TestDrive.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://google-photos.onrender.com/api';

const SAMPLE_COMPLAINT_QUERIES = [
  { label: "Can't find old dog pictures from 2018", desc: "Broken Search" },
  { label: "Cloud backup photos disappeared after update", desc: "Missing Cloud Albums" },
  { label: "Face grouping stopped working and mixed up people", desc: "Face Tagging" },
  { label: "Searching for 'Car Engine' gives random photos", desc: "Object & Text" },
  { label: "Timeline sorts by upload date instead of capture date", desc: "Date Indexing" },
];

export default function TestDrive() {
  const [complaintQuery, setComplaintQuery] = useState('');
  const [complaintResults, setComplaintResults] = useState(null);
  const [complaintLoading, setComplaintLoading] = useState(false);
  
  const navigate = useNavigate();

  const handleComplaintSearch = async (e, customQuery) => {
    if (e) e.preventDefault();
    const q = customQuery !== undefined ? customQuery : complaintQuery;
    if (!q || !q.trim()) return;
    setComplaintQuery(q);
    setComplaintLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/test-search`, { query: q });
      const data = response.data;
      setComplaintResults(data);

      if (data && data.similar_records) {
        const missing = data.similar_records.filter(r => !r.source || r.source.toLowerCase() === 'unknown');
        if (missing.length > 0) {
          console.warn(
            `[Photos Discovery Engine] ⚠️ Search Audit: ${missing.length} / ${data.similar_records.length} nearest complaints have MISSING source values! ` +
            `Record IDs requiring backfill:`, missing.map(m => m.id)
          );
        } else {
          console.log(`[Photos Discovery Engine] ✓ Search Audit: All ${data.similar_records.length} nearest complaints have verified source tags.`);
        }
      }
    } catch (err) {
      console.error("Complaint search failed:", err);
    } finally {
      setComplaintLoading(false);
    }
  };

  return (
    <div className="test-drive animate-fade-in">
      <header className="test-header">
        <h2>Complaint <span className="text-gradient">Classifier</span></h2>
        <p>Test the complaint clustering model with natural language failures</p>
      </header>

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
        
        <div className="sample-pills" style={{ marginTop: '1rem', marginBottom: '1.5rem' }}>
          <span className="pills-label">💡 Try these sample questions:</span>
          {SAMPLE_COMPLAINT_QUERIES.map((sq, idx) => (
            <button 
              key={idx}
              type="button"
              className="sample-pill"
              onClick={() => {
                setComplaintQuery(sq.label);
                handleComplaintSearch(null, sq.label);
              }}
            >
              {sq.label}
            </button>
          ))}
        </div>

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
                    <div className="record-card-top-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem', gap: '0.5rem' }}>
                      <span className="cluster-tag-badge" style={{ fontSize: '0.75rem', fontWeight: '600', color: '#c4b5fd' }}>
                        Cluster #{record.cluster_id}
                      </span>
                      <SourceBadge 
                        source={record.source} 
                        sourcePlatform={record.source_platform}
                        recordId={record.id}
                        rawText={record.raw_text} 
                      />
                    </div>
                    <p className="record-text">"{record.raw_text}"</p>
                    <ExtractionDetail record={record} />
                    <div className="record-meta-small">
                      <span className={`distance-tag ${record.is_confident ? 'tag-confident' : 'tag-low-conf'}`}>
                        {record.is_confident ? '✓ High Confidence' : '⚠️ Low Confidence Reference'} ({record.distance ? record.distance.toFixed(4) : 'N/A'})
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
