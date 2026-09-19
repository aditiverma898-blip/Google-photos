import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import ClusterCard from '../components/ClusterCard';
import './Dashboard.css';

// Consolidate data to single source of truth
import statsData from '../data/stats.json';

export default function Dashboard() {
  const clusters = statsData.clusters || [];
  const synthesis = statsData.synthesis || [];
  const coverage = {
    total_corpus: statsData.funnel.total_ingested,
    source_counts: statsData.source_counts,
    vague_memory_complaints: statsData.funnel.in_scope,
    data_loss_complaints: statsData.funnel.out_of_scope
  };
  
  const loading = false;
  const errors = { clusters: false, synthesis: false, coverage: false };

  // Calculate if counts are fully reconciled
  const countsReconciled = true; // Always true for static JSON


  // Compute insights data
  const strategicInsights = useMemo(() => {
    if (!countsReconciled || clusters.length === 0) return null;

    // Rank in-scope clusters by impact
    const inScopeRanked = clusters
      .filter(c => c.primary_category === 'vague_memory_retrieval' && !c.is_emerging)
      .map(c => {
        const severity = c.severity_score || 0;
        const volume = c.vague_memory_count || 0;
        const impactScore = severity * volume;
        return { ...c, impactScore };
      })
      .sort((a, b) => b.impactScore - a.impactScore);

    const emergingClusters = clusters.filter(c => c.is_emerging);

    // Hardcoded opportunity mapping based on cluster IDs
    const opportunitiesMap = {
      1: "Index and prioritize prominent background objects in image understanding.",
      2: "Parse natural language relative dates (e.g. 'last summer', 'after my birthday').",
      3: "Extract and index weather, mood, and aesthetic metadata from images."
    };

    const topTakeaways = [];
    if (inScopeRanked.length > 0) {
      const topByVol = [...inScopeRanked].sort((a, b) => b.vague_memory_count - a.vague_memory_count)[0];
      topTakeaways.push(`${topByVol.label} has the most in-scope complaints: ${topByVol.vague_memory_count} out of ${topByVol.confirmed_relevant} verified complaints.`);
      
      const topBySeverity = [...inScopeRanked].sort((a, b) => b.severity_score - a.severity_score)[0];
      topTakeaways.push(`${topBySeverity.label} causes the highest average frustration (severity score: ${(topBySeverity.severity_score).toFixed(2)}).`);

      const totalInScope = inScopeRanked.reduce((sum, c) => sum + c.vague_memory_count, 0);
      topTakeaways.push(`Across ${inScopeRanked.length} validated clusters, there are ${totalInScope} confirmed instances of users failing to bridge a vague memory gap.`);
    }

    let playStorePercent = "Unknown";
    if (coverage && coverage.source_counts) {
      const play = coverage.source_counts["Play Store"] || 0;
      const total = coverage.total_corpus || 1;
      playStorePercent = Math.round((play / total) * 100);
    }

    return {
      ranked: inScopeRanked,
      emerging: emergingClusters,
      takeaways: topTakeaways,
      opportunitiesMap,
      playStorePercent
    };
  }, [clusters, countsReconciled, coverage]);

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

      {/* Strategic Insights Section */}
      <section className="synthesis-section strategic-insights-section" style={{ marginTop: '4.5rem' }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0 }}>Strategic Insights</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.35rem', fontSize: '0.92rem' }}>
            Data-driven product recommendations prioritized by verified impact score.
          </p>
        </div>

        {!countsReconciled ? (
          <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <div className="spinner" style={{ margin: '0 auto 1.5rem auto', width: '30px', height: '30px' }}></div>
            <p>Insights compiling: waiting for background verification to reconcile all complaints...</p>
          </div>
        ) : strategicInsights && (
          <div className="insights-container glass-panel" style={{ padding: '2.5rem' }}>
            <div className="insights-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem' }}>
              
              {/* Left Column: Priority Ranking */}
              <div className="insights-column">
                <h3 style={{ color: 'var(--accent-primary)', marginBottom: '0.5rem', fontSize: '1.25rem' }}>Priority Ranking</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                  <strong>Impact Score</strong> = Severity × In-Scope Volume
                </p>
                <div className="priority-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {strategicInsights.ranked.map((c, idx) => (
                    <div key={c.cluster_id} className="insight-card" style={{ padding: '1.25rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', borderLeft: `4px solid var(--accent-primary)` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>{idx + 1}. {c.label}</strong>
                        <span style={{ fontWeight: 'bold', color: 'var(--accent-color)', fontSize: '1.1rem' }}>{(c.impactScore).toFixed(1)}</span>
                      </div>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 0.75rem 0' }}>
                        {c.vague_memory_count} in-scope × {c.severity_score.toFixed(2)} severity
                      </p>
                      <div style={{ fontSize: '0.9rem', color: '#e2e8f0', background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '6px' }}>
                        <strong style={{ color: '#c4b5fd' }}>Opportunity:</strong> {strategicInsights.opportunitiesMap[c.cluster_id] || "Investigate product interventions to bridge this specific memory gap."}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Right Column: Takeaways & Emerging */}
              <div className="insights-column" style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
                
                <div>
                  <h3 style={{ color: 'var(--accent-secondary)', marginBottom: '1rem', fontSize: '1.25rem' }}>Top 3 Takeaways</h3>
                  <ul style={{ paddingLeft: '1.2rem', color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.7', margin: 0 }}>
                    {strategicInsights.takeaways.map((t, i) => <li key={i} style={{ marginBottom: '0.75rem' }}>{t}</li>)}
                  </ul>
                </div>
                
                <div>
                  <h3 style={{ color: '#fbbf24', marginBottom: '1rem', fontSize: '1.25rem' }}>Emerging Watch List</h3>
                  <div className="emerging-watch-list" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {strategicInsights.emerging.map(c => (
                      <div key={c.cluster_id} style={{ padding: '1rem', background: 'rgba(245, 158, 11, 0.05)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: '8px' }}>
                        <strong style={{ color: '#fcd34d' }}>{c.label}</strong>
                        <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                          Not validated. Only {c.vague_memory_count || c.record_count} verified in-scope records. Requires larger corpus sample.
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ padding: '1.25rem', background: 'rgba(251, 146, 60, 0.05)', border: '1px dashed rgba(251, 146, 60, 0.3)', borderRadius: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  <strong style={{ color: '#fdba74' }}>Out-of-Scope Exclusion:</strong> Data Loss & Sync Defects (like Missing Photos) are critical engineering issues but are completely excluded from the retrieval priority ranking above, as they cannot be solved via search/relevance intelligence.
                </div>
              </div>
            </div>

            <div style={{ marginTop: '2.5rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)', fontSize: '0.8rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
              <strong>Caveats:</strong> Analysis based on {coverage ? coverage.total_corpus.toLocaleString() : "---"} total feedback records. Play Store accounts for ~{strategicInsights.playStorePercent}% of data, meaning results may skew toward Android user behavior.
            </div>
          </div>
        )}
      </section>

    </div>
  );
}
