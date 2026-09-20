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
      
      {id === '0' && (
        <div style={{
          margin: '0.5rem 0 1.5rem 0',
          padding: '0.85rem 1.25rem',
          background: 'rgba(251, 146, 60, 0.1)',
          border: '1px solid rgba(251, 146, 60, 0.4)',
          borderRadius: '8px',
          color: '#fdba74',
          fontSize: '0.9rem',
          lineHeight: '1.5'
        }}>
          ℹ️ <strong>Out-of-Scope Context (Data Loss & Sync Defect):</strong> This cluster captures engineering data loss, backup failures, and device sync bugs where media was missing due to platform defects rather than user vague-memory retrieval gaps. Retained for corpus completeness.
        </div>
      )}

      {records.length <= 5 && id !== '0' && (
        <div style={{
          margin: '0.5rem 0 1.5rem 0',
          padding: '0.85rem 1.25rem',
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px dashed rgba(245, 158, 11, 0.5)',
          borderRadius: '8px',
          color: '#fcd34d',
          fontSize: '0.9rem',
          lineHeight: '1.5'
        }}>
          ⚠️ <strong>Emerging pattern — low sample:</strong> This pattern currently contains only {records.length} sample complaints in the database. It is tracked as an observational hypothesis rather than a statistically validated cluster.
        </div>
      )}

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
