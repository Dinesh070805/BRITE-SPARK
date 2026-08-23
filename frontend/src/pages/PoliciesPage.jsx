import React, { useEffect, useState } from 'react';
import { getPolicies, updatePolicies } from '../services/api';

export default function PoliciesPage() {
  const [policy, setPolicy] = useState({
    quiet_hours_start: 20,
    quiet_hours_end: 8,
    max_attempts: 3,
    channel_priority: 'SMS,Voice,Email'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadPolicy();
  }, []);

  const loadPolicy = async () => {
    try {
      setLoading(true);
      const res = await getPolicies();
      setPolicy(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      await updatePolicies(policy);
      alert("Policy configuration saved to SQLite database successfully!");
    } catch (err) {
      alert("Failed to save policy: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="page-title">Loading Policies...</div>;

  return (
    <div>
      <h1 className="page-title">Policy & Configuration Settings</h1>

      <div className="card-panel" style={{ maxWidth: 600 }}>
        <form onSubmit={handleSave}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 600, marginBottom: '0.4rem' }}>
              Quiet Hours Start Time (Hour 0-23):
            </label>
            <input
              type="number"
              min="0"
              max="23"
              className="input-control"
              style={{ width: '100%' }}
              value={policy.quiet_hours_start}
              onChange={(e) => setPolicy({ ...policy, quiet_hours_start: parseInt(e.target.value) || 0 })}
            />
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Default: 20 (8:00 PM)</span>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 600, marginBottom: '0.4rem' }}>
              Quiet Hours End Time (Hour 0-23):
            </label>
            <input
              type="number"
              min="0"
              max="23"
              className="input-control"
              style={{ width: '100%' }}
              value={policy.quiet_hours_end}
              onChange={(e) => setPolicy({ ...policy, quiet_hours_end: parseInt(e.target.value) || 0 })}
            />
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Default: 8 (8:00 AM)</span>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 600, marginBottom: '0.4rem' }}>
              Maximum Attempts Per Appointment:
            </label>
            <input
              type="number"
              min="1"
              max="10"
              className="input-control"
              style={{ width: '100%' }}
              value={policy.max_attempts}
              onChange={(e) => setPolicy({ ...policy, max_attempts: parseInt(e.target.value) || 1 })}
            />
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Default: 3</span>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 600, marginBottom: '0.4rem' }}>
              Channel Priority Order (Comma Separated):
            </label>
            <input
              type="text"
              className="input-control"
              style={{ width: '100%' }}
              value={policy.channel_priority}
              onChange={(e) => setPolicy({ ...policy, channel_priority: e.target.value })}
            />
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Default: SMS,Voice,Email</span>
          </div>

          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save Policy Config'}
          </button>
        </form>
      </div>
    </div>
  );
}
