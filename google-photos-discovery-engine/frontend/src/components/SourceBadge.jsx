import React, { useEffect } from 'react';
import './SourceBadge.css';

export function getCanonicalSource(rawSource) {
  if (!rawSource) return null;
  const s = String(rawSource).trim().toLowerCase();
  if (s === '' || s === 'unknown' || s === 'null' || s === 'none') {
    return null;
  }
  if (s.includes('reddit')) return 'Reddit';
  if (s.includes('play') || s === 'google_play' || s === 'play_store') return 'Play Store';
  if (s.includes('app_store') || s.includes('appstore') || s.includes('ios')) return 'App Store';
  if (s.includes('youtube')) return 'YouTube Comment';
  if (s.includes('help') || s.includes('forum') || s.includes('support')) return 'Google Support Community';
  if (s.includes('twitter') || s === 'x') return 'Twitter/X';
  return String(rawSource).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export default function SourceBadge({ source, sourcePlatform, recordId, rawText, className = '' }) {
  const canonical = getCanonicalSource(source || sourcePlatform);

  useEffect(() => {
    if (!canonical) {
      console.warn(
        `[Photos Discovery Engine] ⚠️ Complaint ${recordId ? `#${recordId}` : ''} has a MISSING source value in the dataset! ` +
        `Raw text snippet: "${(rawText || '').substring(0, 60)}...". Backfill required.`
      );
    }
  }, [canonical, recordId, rawText]);

  if (!canonical) {
    return (
      <span 
        className={`source-badge source-badge-missing ${className}`} 
        title={`Missing source platform for complaint ${recordId ? `#${recordId}` : ''} - requires backfill`}
      >
        ⚠️ Missing Source
      </span>
    );
  }

  let colorClass = 'source-badge-play-store';
  if (canonical === 'Reddit') colorClass = 'source-badge-reddit';
  else if (canonical === 'YouTube Comment') colorClass = 'source-badge-youtube';
  else if (canonical === 'Google Support Community') colorClass = 'source-badge-support';
  else if (canonical === 'App Store') colorClass = 'source-badge-app-store';
  else if (canonical === 'Twitter/X') colorClass = 'source-badge-twitter';

  return (
    <span className={`source-badge ${colorClass} ${className}`}>
      <span className="source-badge-dot"></span>
      {canonical}
    </span>
  );
}
