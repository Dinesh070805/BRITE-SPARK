import React, { useEffect, useState } from 'react';
import { getAuditLogs } from '../services/api';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadAuditLogs();
  }, [actionFilter]);

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      const params = {};
      if (actionFilter !== 'ALL') params.action = actionFilter;
      const res = await getAuditLogs(params);
      setLogs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = logs.filter(l =>
    (l.resident_id && l.resident_id.toLowerCase().includes(search.toLowerCase())) ||
    (l.appointment_id && l.appointment_id.toLowerCase().includes(search.toLowerCase())) ||
    (l.reason && l.reason.toLowerCase().includes(search.toLowerCase())) ||
    (l.details && l.details.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div>
      <h1 className="page-title">Decision Audit Logs</h1>

      <div className="filter-row">
        <input
          type="text"
          className="input-control"
          placeholder="Search by Resident, Appointment, Reason..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ minWidth: 280 }}
        />
        <select
          className="select-control"
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
        >
          <option value="ALL">All Actions</option>
          <option value="REACHED">REACHED</option>
          <option value="ATTEMPTED">ATTEMPTED</option>
          <option value="DEFERRED">DEFERRED</option>
          <option value="BLOCKED">BLOCKED</option>
          <option value="STOPPED">STOPPED</option>
          <option value="DUPLICATE_PREVENTED">DUPLICATE_PREVENTED</option>
        </select>
      </div>

      <div className="table-responsive">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>Resident ID</th>
              <th>Appt ID</th>
              <th>Channel</th>
              <th>Status</th>
              <th>Reason</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colspan="8" style={{ textAlign: 'center', padding: '2rem' }}>Loading audit logs...</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colspan="8" style={{ textAlign: 'center', padding: '2rem' }}>No audit logs found.</td></tr>
            ) : (
              filtered.slice(0, 100).map(l => (
                <tr key={l.id}>
                  <td>{new Date(l.timestamp).toLocaleString()}</td>
                  <td><span className="badge badge-delivered">{l.action}</span></td>
                  <td>{l.resident_id || '—'}</td>
                  <td>{l.appointment_id || '—'}</td>
                  <td>{l.channel ? l.channel.toUpperCase() : '—'}</td>
                  <td><span className="badge badge-pending">{l.status}</span></td>
                  <td>{l.reason}</td>
                  <td>{l.details}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
