import React from 'react';
import { Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Dashboard from './pages/Dashboard';
import ClusterDetail from './pages/ClusterDetail';
import TestDrive from './pages/TestDrive';

function App() {
  return (
    <div className="container">
      <NavBar />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/cluster/:id" element={<ClusterDetail />} />
        <Route path="/test-drive" element={<TestDrive />} />
      </Routes>
    </div>
  );
}

export default App;
