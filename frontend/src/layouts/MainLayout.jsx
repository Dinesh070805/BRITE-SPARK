import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { runReminderEngine } from '../services/api';

export default function MainLayout() {
  const [isRunning, setIsRunning] = useState(false);
  const navigate = useNavigate();

  const handleRunEngine = async () => {
    try {
      setIsRunning(true);
      const res = await runReminderEngine();
      alert(`⚡ Reminder Engine Run Completed!\nProcessed: ${res.data.summary.appointments_processed} appointments.`);
      window.location.reload();
    } catch (err) {
      alert("Failed to run reminder engine: " + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">📡</div>
          <div className="sidebar-title">
            <h2>Calder County</h2>
            <p>Reminder System</p>
          </div>
        </div>

        <nav className="sidebar-menu">
          <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span>📊</span> Dashboard
          </NavLink>
          <NavLink to="/appointments" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span>📅</span> Appointments
          </NavLink>
          <NavLink to="/residents" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span>👥</span> Residents
          </NavLink>
          <NavLink to="/reminders" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span>🔔</span> Reminders
          </NavLink>
          <NavLink to="/analytics" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span>📈</span> Analytics
          </NavLink>
          <NavLink to="/audit-logs" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span>📋</span> Audit Logs
          </NavLink>
          <NavLink to="/policies" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span>⚙️</span> Policies & Rules
          </NavLink>
        </nav>
      </aside>

      {/* Main Wrapper */}
      <div className="main-wrapper">
        <header className="top-header">
          <div className="header-status">
            <div className="pulse-dot"></div>
            POLICY ENGINE ONLINE
          </div>
          <div>
            <button className="btn btn-primary" onClick={handleRunEngine} disabled={isRunning}>
              {isRunning ? '⚡ Executing...' : '⚡ Run Reminder Engine'}
            </button>
          </div>
        </header>

        <main className="page-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
