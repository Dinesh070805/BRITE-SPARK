import React, { useEffect, useState } from 'react';
import { getMetrics } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#10b981', '#38bdf8', '#f59e0b', '#f43f5e', '#a855f7'];

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      const res = await getMetrics();
      setMetrics(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !metrics) {
    return <div className="page-title">Loading Analytics...</div>;
  }

  const funnelData = [
    { stage: 'Appointments', count: metrics.appointments },
    { stage: 'Attempts', count: metrics.reminders_attempted },
    { stage: 'Reached (Human)', count: metrics.residents_reached }
  ];

  const channelStatsData = [
    { channel: 'SMS', Delivered: metrics.channel_stats.sms.delivered, Failed: metrics.channel_stats.sms.failed },
    { channel: 'Voice', HumanReached: metrics.channel_stats.voice.human, Voicemail: metrics.channel_stats.voice.voicemail, Failed: metrics.channel_stats.voice.failed },
    { channel: 'Email', Delivered: metrics.channel_stats.email.delivered, Failed: metrics.channel_stats.email.failed }
  ];

  return (
    <div>
      <h1 className="page-title">Advanced Operational Analytics</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card-panel">
          <h3 style={{ fontFamily: 'Outfit', fontSize: '1.1rem', marginBottom: '1rem' }}>Conversion Funnel</h3>
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={funnelData} layout="vertical">
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis dataKey="stage" type="category" stroke="#94a3b8" />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)' }} />
                <Bar dataKey="count" fill="#38bdf8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card-panel">
          <h3 style={{ fontFamily: 'Outfit', fontSize: '1.1rem', marginBottom: '1rem' }}>Voice Channel Breakdown</h3>
          <div style={{ padding: '1rem' }}>
            <p><strong>Human Answered (Confirmed Reach):</strong> <span style={{ color: 'var(--accent-emerald)', fontWeight: 'bold' }}>{metrics.channel_stats.voice.human}</span></p>
            <p><strong>Voicemail Left:</strong> {metrics.channel_stats.voice.voicemail}</p>
            <p><strong>No Answer / Busy / Failed:</strong> {metrics.channel_stats.voice.failed}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
