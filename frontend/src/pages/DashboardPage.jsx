import React, { useEffect, useState } from 'react';
import { getDashboard } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#38bdf8', '#a855f7', '#10b981', '#f59e0b', '#f43f5e'];

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const res = await getDashboard();
      setData(res.data);
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data) {
    return <div className="page-title">Loading Dashboard Analytics...</div>;
  }

  const channelChartData = [
    { name: 'SMS', Attempts: data.channel_stats.sms.attempts, Delivered: data.channel_stats.sms.delivered },
    { name: 'Voice', Attempts: data.channel_stats.voice.attempts, Reached: data.channel_stats.voice.human },
    { name: 'Email', Attempts: data.channel_stats.email.attempts, Delivered: data.channel_stats.email.delivered }
  ];

  const languagePieData = Object.entries(data.language_stats || {}).map(([lang, count]) => ({
    name: lang.toUpperCase(),
    value: count
  }));

  return (
    <div>
      <h1 className="page-title">Executive Operations Dashboard</h1>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Confirmed Reach Rate</div>
          <div className="kpi-val" style={{ color: 'var(--accent-emerald)' }}>{data.reach_rate}%</div>
          <div className="kpi-sub">{data.residents_reached} residents reached</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Carrier Delivery Rate</div>
          <div className="kpi-val" style={{ color: 'var(--accent-cyan)' }}>{data.delivery_rate}%</div>
          <div className="kpi-sub">{data.reminders_attempted} total dispatches</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Total Appointments</div>
          <div className="kpi-val">{data.appointments}</div>
          <div className="kpi-sub">{data.residents} registered residents</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Policy Blocks & Safety</div>
          <div className="kpi-val" style={{ color: 'var(--accent-amber)' }}>
            {data.blocked + data.deferred + data.duplicates_prevented}
          </div>
          <div className="kpi-sub">{data.blocked} opt-outs | {data.duplicates_prevented} duplicates</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card-panel">
          <h3 style={{ fontFamily: 'Outfit', fontSize: '1.1rem', marginBottom: '1rem' }}>Reminders by Channel</h3>
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={channelChartData}>
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)' }} />
                <Bar dataKey="Attempts" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Delivered" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card-panel">
          <h3 style={{ fontFamily: 'Outfit', fontSize: '1.1rem', marginBottom: '1rem' }}>Language Distribution</h3>
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={languagePieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                  {languagePieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
