import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './NavBar.css';

export default function NavBar() {
  const location = useLocation();

  return (
    <nav className="navbar glass-panel">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          <span className="text-gradient">Photos Discovery Engine</span>
        </Link>
        <div className="navbar-links">
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            Dashboard
          </Link>
          <Link 
            to="/test-drive" 
            className={`nav-link ${location.pathname === '/test-drive' ? 'active' : ''}`}
          >
            Test Drive
          </Link>
        </div>
      </div>
    </nav>
  );
}
