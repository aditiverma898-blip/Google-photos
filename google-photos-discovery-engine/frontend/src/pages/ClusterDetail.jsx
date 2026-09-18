import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import SourceBadge from '../components/SourceBadge';
import './ClusterDetail.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://google-photos.onrender.com/api';

export default function ClusterDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecords = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/clusters/${id}/records`);
        const recs = response.data.records || [];
        setRecords(recs);

        // Audit missing sources in this cluster
        const missing = recs.filter(r => !r.source || r.source.toLowerCase() === 'unknown');
        if (missing.length > 0) {
          console.warn(
            `[Photos Discovery Engine] ⚠️ Cluster #${id} Audit: ${missing.length} / ${recs.length} complaints have MISSING source platforms! ` +
            `Record IDs requiring backfill:`, missing.map(m => m.id)
          );
        } else {
          console.log(`[Photos Discovery Engine] ✓ Cluster #${id} Audit: All ${recs.length} complaints have verified source tags.`);
        }
      } catch (error) {
        console.error('Error fetching cluster records:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchRecords();
  }, [id]);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="cluster-detail animate-fade-in">
      <button className="back-button" onClick={() => navigate(-1)}>
        &larr; Back to Dashboard
      </button>

      <header className="detail-header">
        <h2>Cluster <span className="text-gradient">#{id}</span> Analysis</h2>
        <p>Found {records.length} historical user complaints exhibiting this failure pattern.</p>
      </header>
      
      <div className="records-grid">
        {records.map(record => (
          <div key={record.id} className="record-card glass-panel">
            <div className="record-meta">
              <SourceBadge 
                source={record.source} 
                sourcePlatform={record.source_platform}
                recordId={record.id}
                rawText={record.raw_text} 
              />
              <span className={`emotion-tag ${record.emotional_signal}`}>
                {record.emotional_signal}
              </span>
            </div>
            
            <p className="record-text">"{record.raw_text}"</p>
            
            <div className="record-attributes">
              <div className="attr-group">
                <span className="attr-label">Tried to Search</span>
                <span className="attr-value">{record.search_strategy}</span>
              </div>
              <div className="attr-group">
                <span className="attr-label">Failed Because</span>
                <span className="attr-value">{record.failure_point}</span>
              </div>
              
              {record.workaround && (
                <div className="attr-group full-width">
                  <span className="attr-label">Workaround</span>
                  <span className="attr-value">{record.workaround}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
