import React, { useEffect, useState } from 'react';
import { getAppointments, getAppointmentById } from '../services/api';

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  useEffect(() => {
    loadAppointments();
  }, [statusFilter]);

  const loadAppointments = async () => {
    try {
      setLoading(true);
      const params = {};
      if (statusFilter !== 'ALL') params.status = statusFilter;
      const res = await getAppointments(params);
      setAppointments(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = appointments.filter(a =>
    a.id.toLowerCase().includes(search.toLowerCase()) ||
    a.resident_id.toLowerCase().includes(search.toLowerCase()) ||
    a.location.toLowerCase().includes(search.toLowerCase()) ||
    a.service_type.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <h1 className="page-title">Appointments Directory</h1>

      <div className="filter-row">
        <input
          type="text"
          className="input-control"
          placeholder="Search by ID, Resident, Location..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ minWidth: 280 }}
        />
        <select
          className="select-control"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="ALL">All Statuses</option>
          <option value="Booked">Booked</option>
        </select>
      </div>

      <div className="table-responsive">
        <table>
          <thead>
            <tr>
              <th>Appointment ID</th>
              <th>Resident ID</th>
              <th>Scheduled Time</th>
              <th>Location</th>
              <th>Service Type</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colspan="7" style={{ textAlign: 'center', padding: '2rem' }}>Loading appointments...</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colspan="7" style={{ textAlign: 'center', padding: '2rem' }}>No appointments found.</td></tr>
            ) : (
              filtered.slice(0, 100).map(a => (
                <tr key={a.id}>
                  <td><strong>{a.id}</strong></td>
                  <td>{a.resident_id}</td>
                  <td>{new Date(a.scheduled_at).toLocaleString()}</td>
                  <td>{a.location}</td>
                  <td>{a.service_type}</td>
                  <td><span className="badge badge-delivered">{a.status}</span></td>
                  <td>
                    <button className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.78rem' }} onClick={() => setSelectedApp(a)}>
                      Details
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {selectedApp && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card-panel" style={{ width: '90%', maxWidth: 500, position: 'relative' }}>
            <span style={{ position: 'absolute', right: '1.2rem', top: '1.2rem', cursor: 'pointer', fontSize: '1.2rem' }} onClick={() => setSelectedApp(null)}>&times;</span>
            <h3 style={{ fontFamily: 'Outfit', fontSize: '1.3rem', marginBottom: '1rem' }}>Appointment Details</h3>
            <p><strong>Appointment ID:</strong> {selectedApp.id}</p>
            <p><strong>Resident ID:</strong> {selectedApp.resident_id}</p>
            <p><strong>Scheduled Time:</strong> {new Date(selectedApp.scheduled_at).toLocaleString()}</p>
            <p><strong>Location:</strong> {selectedApp.location}</p>
            <p><strong>Service Type:</strong> {selectedApp.service_type}</p>
            <p><strong>Status:</strong> {selectedApp.status}</p>
          </div>
        </div>
      )}
    </div>
  );
}
