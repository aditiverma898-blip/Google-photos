import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ClusterCard from '../components/ClusterCard';
import './Dashboard.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://google-photos.onrender.com/api';

export default function Dashboard() {
  const [clusters, setClusters] = useState([]);
  const [synthesis, setSynthesis] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [clustersRes, synthesisRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/clusters`),
          axios.get(`${API_BASE_URL}/synthesis`)
        ]);
        
        setClusters(clustersRes.data.clusters || []);
        setSynthesis(synthesisRes.data.synthesis || []);
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
