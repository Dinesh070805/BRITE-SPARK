import React, { useEffect, useState } from 'react';
import { getReminders, retryReminder } from '../services/api';

export default function RemindersPage() {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [channelFilter, setChannelFilter] = useState('ALL');

  useEffect(() => {
    loadReminders();
  }, [statusFilter, channelFilter]);

  const loadReminders = async () => {
    try {
      setLoading(true);
      const params = {};
      if (statusFilter !== 'ALL') params.status = statusFilter;
      if (channelFilter !== 'ALL') params.channel = channelFilter;
      const res = await getReminders(params);
      setReminders(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async (id) => {
    try {
      await retryReminder(id);
      alert(`Reminder #${id} retried successfully.`);
      loadReminders();
    } catch (err) {
      alert("Failed to retry reminder: " + err.message);
    }
  };

  return (
    <div>
      <h1 className="page-title">Reminders Engine Monitoring</h1>

      <div className="filter-row">
        <select
          className="select-control"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="ALL">All Statuses</option>
          <option value="Reached">Reached (Confirmed Human)</option>
          <option value="Delivered">Delivered</option>
          <option value="Pending">Pending</option>
          <option value="Failed">Failed</option>
          <option value="Deferred">Deferred</option>
          <option value="Blocked">Blocked</option>
        </select>

        <select
          className="select-control"
          value={channelFilter}
          onChange={(e) => setChannelFilter(e.target.value)}
        >
          <option value="ALL">All Channels</option>
          <option value="sms">SMS</option>
          <option value="voice">Voice</option>
          <option value="email">Email</option>
        </select>
      </div>

      <div className="table-responsive">
        <table>
          <thead>
            <tr>
              <th>Reminder ID</th>
              <th>Appt ID</th>
              <th>Resident ID</th>
              <th>Scheduled Time</th>
              <th>Channel</th>
              <th>Status</th>
              <th>Human Reached?</th>
              <th>Attempts</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colspan="9" style={{ textAlign: 'center', padding: '2rem' }}>Loading reminders...</td></tr>
            ) : reminders.length === 0 ? (
              <tr><td colspan="9" style={{ textAlign: 'center', padding: '2rem' }}>No reminders found. Run reminder engine first.</td></tr>
            ) : (
              reminders.slice(0, 100).map(r => {
                let badgeClass = 'badge-delivered';
                if (r.reached) badgeClass = 'badge-reached';
                else if (r.status === 'Failed') badgeClass = 'badge-failed';
                else if (r.status === 'Blocked' || r.status === 'Deferred') badgeClass = 'badge-blocked';
                else if (r.status === 'Pending') badgeClass = 'badge-pending';

                return (
                  <tr key={r.id}>
                    <td><strong>#{r.id}</strong></td>
                    <td>{r.appointment_id}</td>
                    <td>{r.resident_id}</td>
                    <td>{new Date(r.scheduled_at).toLocaleString()}</td>
                    <td><span className="badge badge-delivered">{r.channel.toUpperCase()}</span></td>
                    <td><span className={`badge ${badgeClass}`}>{r.status.toUpperCase()}</span></td>
                    <td>{r.reached ? <strong style={{ color: 'var(--accent-emerald)' }}>YES 🎯</strong> : 'NO'}</td>
                    <td>{r.attempt_count}</td>
                    <td>
                      <button className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.78rem' }} onClick={() => handleRetry(r.id)}>
                        Retry
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
