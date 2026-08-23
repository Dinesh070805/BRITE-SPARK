import React, { useEffect, useState } from 'react';
import { getResidents } from '../services/api';

export default function ResidentsPage() {
  const [residents, setResidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [langFilter, setLangFilter] = useState('ALL');
  const [selectedRes, setSelectedRes] = useState(null);

  useEffect(() => {
    loadResidents();
  }, [langFilter]);

  const loadResidents = async () => {
    try {
      setLoading(true);
      const params = {};
      if (langFilter !== 'ALL') params.language = langFilter;
      const res = await getResidents(params);
      setResidents(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = residents.filter(r =>
    r.id.toLowerCase().includes(search.toLowerCase()) ||
    r.name.toLowerCase().includes(search.toLowerCase()) ||
    (r.mobile && r.mobile.includes(search)) ||
    (r.email && r.email.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div>
      <h1 className="page-title">Resident Profiles & Contact Health</h1>

      <div className="filter-row">
        <input
          type="text"
          className="input-control"
          placeholder="Search by ID, Name, Phone, Email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ minWidth: 280 }}
        />
        <select
          className="select-control"
          value={langFilter}
          onChange={(e) => setLangFilter(e.target.value)}
        >
          <option value="ALL">All Languages</option>
          <option value="en">English (en)</option>
          <option value="es">Spanish (es)</option>
          <option value="vi">Vietnamese (vi)</option>
          <option value="so">Somali (so)</option>
          <option value="ru">Russian (ru)</option>
          <option value="zh">Chinese (zh)</option>
        </select>
      </div>

      <div className="table-responsive">
        <table>
          <thead>
            <tr>
              <th>Resident ID</th>
              <th>Name</th>
              <th>Language</th>
              <th>Mobile</th>
              <th>Landline</th>
              <th>Email</th>
              <th>Opt-outs</th>
              <th>Last Verified</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colspan="9" style={{ textAlign: 'center', padding: '2rem' }}>Loading residents...</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colspan="9" style={{ textAlign: 'center', padding: '2rem' }}>No residents found.</td></tr>
            ) : (
              filtered.slice(0, 100).map(r => (
                <tr key={r.id}>
                  <td><strong>{r.id}</strong></td>
                  <td>{r.name}</td>
                  <td><span className="badge badge-delivered">{r.language.toUpperCase()}</span></td>
                  <td>{r.mobile || '—'}</td>
                  <td>{r.landline || '—'}</td>
                  <td>{r.email || '—'}</td>
                  <td>
                    {r.sms_optout && <span className="badge badge-blocked" style={{ marginRight: 4 }}>SMS</span>}
                    {r.voice_optout && <span className="badge badge-blocked" style={{ marginRight: 4 }}>Voice</span>}
                    {r.email_optout && <span className="badge badge-blocked">Email</span>}
                    {!r.sms_optout && !r.voice_optout && !r.email_optout && <span className="badge badge-reached">None</span>}
                  </td>
                  <td>{r.number_last_verified ? new Date(r.number_last_verified).toLocaleDateString() : '—'}</td>
                  <td>
                    <button className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.78rem' }} onClick={() => setSelectedRes(r)}>
                      View Profile
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {selectedRes && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card-panel" style={{ width: '90%', maxWidth: 520, position: 'relative' }}>
            <span style={{ position: 'absolute', right: '1.2rem', top: '1.2rem', cursor: 'pointer', fontSize: '1.2rem' }} onClick={() => setSelectedRes(null)}>&times;</span>
            <h3 style={{ fontFamily: 'Outfit', fontSize: '1.3rem', marginBottom: '1rem' }}>Resident Profile ({selectedRes.id})</h3>
            <p><strong>Full Name:</strong> {selectedRes.name}</p>
            <p><strong>Preferred Language:</strong> {selectedRes.language.toUpperCase()}</p>
            <p><strong>Mobile:</strong> {selectedRes.mobile || 'None'}</p>
            <p><strong>Landline:</strong> {selectedRes.landline || 'None'}</p>
            <p><strong>Email:</strong> {selectedRes.email || 'None'}</p>
            <p><strong>SMS Opt-out:</strong> {selectedRes.sms_optout ? 'YES' : 'NO'}</p>
            <p><strong>Voice Opt-out:</strong> {selectedRes.voice_optout ? 'YES' : 'NO'}</p>
            <p><strong>Email Opt-out:</strong> {selectedRes.email_optout ? 'YES' : 'NO'}</p>
            <p><strong>Last Verified:</strong> {selectedRes.number_last_verified ? new Date(selectedRes.number_last_verified).toLocaleDateString() : 'Unverified'}</p>
          </div>
        </div>
      )}
    </div>
  );
}
