#!/usr/bin/env python3
"""
Localhost Web Dashboard Server for Reminder That Reaches.
Runs on http://localhost:8000 using Python standard library.
"""
import http.server
import socketserver
import json
import os
import urllib.parse
from datetime import datetime

from reminder.loader import load_contacts, load_appointments
from reminder.policy import ContactPolicy
from reminder.language import LanguageSelector
from reminder.dedup import DeduplicationService
from reminder.dispatcher import ReminderDispatcher
from reminder.planner import ReminderPlanner
from reminder.metrics import MetricsCollector

PORT = 8000

def get_dashboard_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calder County — Reminder Engine Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #070913;
            --bg-card: rgba(15, 23, 42, 0.65);
            --border-card: rgba(255, 255, 255, 0.08);
            --border-card-hover: rgba(56, 189, 248, 0.3);
            --accent-cyan: #38bdf8;
            --accent-emerald: #10b981;
            --accent-purple: #a855f7;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --glass-glow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-dark);
            background-image: 
                radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.12) 0px, transparent 50%),
                radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.08) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem;
        }

        .container { max-width: 1440px; margin: 0 auto; }

        /* Top Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding: 1.25rem 1.75rem;
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-card);
            border-radius: 20px;
            box-shadow: var(--glass-glow);
        }

        .brand-section { display: flex; align-items: center; gap: 1rem; }
        .logo-icon {
            width: 44px; height: 44px;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.4rem; box-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
        }
        .brand-title h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 1.5rem; font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(to right, #ffffff, #cbd5e1);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .brand-title p { font-size: 0.85rem; color: var(--text-muted); }

        .system-status {
            display: inline-flex; align-items: center; gap: 0.5rem;
            padding: 0.35rem 0.85rem; border-radius: 20px;
            background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);
            color: var(--accent-emerald); font-size: 0.8rem; font-weight: 600;
        }
        .pulse-dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: var(--accent-emerald);
            box-shadow: 0 0 10px var(--accent-emerald);
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }

        .btn-group { display: flex; gap: 0.8rem; }
        .btn {
            display: inline-flex; align-items: center; gap: 0.5rem;
            padding: 0.7rem 1.4rem; border-radius: 12px;
            font-family: 'Outfit', sans-serif; font-size: 0.9rem; font-weight: 600;
            border: none; cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .btn-primary {
            background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
            color: white; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5); }
        .btn-secondary {
            background: rgba(255, 255, 255, 0.05); color: var(--text-main);
            border: 1px solid var(--border-card);
        }
        .btn-secondary:hover { background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.2); }

        /* KPI Cards Grid */
        .kpi-grid {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; margin-bottom: 2rem;
        }
        @media (max-width: 1100px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 600px) { .kpi-grid { grid-template-columns: 1fr; } }

        .kpi-card {
            background: var(--bg-card); backdrop-filter: blur(16px);
            border: 1px solid var(--border-card); border-radius: 20px;
            padding: 1.5rem; position: relative; overflow: hidden;
            transition: all 0.3s ease; box-shadow: var(--glass-glow);
        }
        .kpi-card:hover {
            border-color: var(--border-card-hover); transform: translateY(-3px);
        }
        .kpi-header { display: flex; justify-content: space-between; align-items: center; }
        .kpi-label { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }
        .kpi-icon { font-size: 1.2rem; opacity: 0.8; }
        .kpi-val { font-family: 'Outfit', sans-serif; font-size: 2.4rem; font-weight: 800; margin: 0.6rem 0; letter-spacing: -0.02em; }
        
        .progress-bar-bg { width: 100%; height: 6px; background: rgba(255, 255, 255, 0.1); border-radius: 10px; overflow: hidden; margin-top: 0.8rem; }
        .progress-bar-fill { height: 100%; border-radius: 10px; transition: width 1s ease-in-out; }

        /* Tab Navigation */
        .tabs-nav {
            display: flex; gap: 0.5rem; margin-bottom: 1.5rem;
            background: rgba(15, 23, 42, 0.5); padding: 0.4rem;
            border-radius: 14px; border: 1px solid var(--border-card);
            width: fit-content;
        }
        .tab-btn {
            padding: 0.65rem 1.25rem; border-radius: 10px; font-size: 0.88rem; font-weight: 600;
            color: var(--text-muted); background: transparent; border: none; cursor: pointer;
            transition: all 0.2s ease;
        }
        .tab-btn.active {
            background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan);
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        /* Content Panels */
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .panels-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem; }
        @media (max-width: 900px) { .panels-grid { grid-template-columns: 1fr; } }

        .panel-card {
            background: var(--bg-card); backdrop-filter: blur(16px);
            border: 1px solid var(--border-card); border-radius: 20px;
            padding: 1.75rem; box-shadow: var(--glass-glow);
        }
        .panel-title { font-family: 'Outfit', sans-serif; font-size: 1.2rem; font-weight: 700; margin-bottom: 1.25rem; display: flex; align-items: center; justify-content: space-between; }

        .stat-row {
            display: flex; justify-content: space-between; align-items: center;
            padding: 0.9rem 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        .stat-row:last-child { border-bottom: none; }

        .badge-pill {
            display: inline-flex; align-items: center; gap: 0.35rem;
            padding: 0.3rem 0.7rem; border-radius: 8px; font-size: 0.78rem; font-weight: 700;
            letter-spacing: 0.02em;
        }
        .badge-sms { background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan); border: 1px solid rgba(56, 189, 248, 0.25); }
        .badge-voice { background: rgba(168, 85, 247, 0.15); color: var(--accent-purple); border: 1px solid rgba(168, 85, 247, 0.25); }
        .badge-email { background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald); border: 1px solid rgba(16, 185, 129, 0.25); }

        /* Search & Filters */
        .filter-bar {
            display: flex; gap: 1rem; margin-bottom: 1.2rem; flex-wrap: wrap; align-items: center; justify-content: space-between;
        }
        .search-box {
            position: relative; flex: 1; min-width: 280px;
        }
        .search-box input {
            width: 100%; padding: 0.7rem 1rem 0.7rem 2.4rem; border-radius: 12px;
            background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border-card);
            color: var(--text-main); font-size: 0.88rem; outline: none; transition: border-color 0.2s;
        }
        .search-box input:focus { border-color: var(--accent-cyan); }
        .search-icon { position: absolute; left: 0.85rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); font-size: 0.9rem; }

        .filter-select {
            padding: 0.7rem 1rem; border-radius: 12px;
            background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border-card);
            color: var(--text-main); font-size: 0.88rem; outline: none; cursor: pointer;
        }

        /* Table */
        .table-responsive { overflow-x: auto; max-height: 520px; border-radius: 14px; border: 1px solid rgba(255, 255, 255, 0.05); }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem; }
        th {
            background: rgba(15, 23, 42, 0.95); color: var(--text-muted);
            padding: 0.9rem 1.1rem; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em;
            position: sticky; top: 0; z-index: 10; border-bottom: 1px solid var(--border-card);
        }
        td { padding: 0.85rem 1.1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.04); }
        tr:hover td { background: rgba(56, 189, 248, 0.04); }

        .tag-status {
            padding: 0.25rem 0.65rem; border-radius: 6px; font-size: 0.75rem; font-weight: 700; display: inline-block;
        }
        .tag-reached { background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald); }
        .tag-delivered { background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan); }
        .tag-failed { background: rgba(244, 63, 94, 0.15); color: var(--accent-rose); }
        .tag-blocked { background: rgba(245, 158, 11, 0.15); color: var(--accent-amber); }

        /* Modal */
        .modal-overlay {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(8px);
            display: none; align-items: center; justify-content: center; z-index: 1000;
        }
        .modal-card {
            background: #0f172a; border: 1px solid var(--border-card);
            border-radius: 20px; max-width: 600px; width: 90%; padding: 2rem;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6); position: relative;
        }
        .modal-close { position: absolute; right: 1.5rem; top: 1.5rem; font-size: 1.2rem; cursor: pointer; color: var(--text-muted); }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div class="brand-section">
                <div class="logo-icon">📡</div>
                <div class="brand-title">
                    <h1>Reminder Engine</h1>
                    <p>Calder County Policy-Driven Appointment Communications</p>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 1.5rem;">
                <div class="system-status">
                    <div class="pulse-dot"></div>
                    POLICY ENGINE ONLINE
                </div>
                <div class="btn-group">
                    <button class="btn btn-secondary" onclick="fetchMetrics()">🔄 Refresh Data</button>
                    <button class="btn btn-primary" onclick="runEngine()">⚡ Run Engine</button>
                </div>
            </div>
        </header>

        <!-- KPI Hero Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-label">Confirmed Human Reach</span>
                    <span class="kpi-icon" style="color: var(--accent-emerald);">🎯</span>
                </div>
                <div class="kpi-val" id="reach-val" style="color: var(--accent-emerald);">0%</div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" id="reach-bar" style="width: 0%; background: var(--accent-emerald);"></div>
                </div>
                <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.6rem;" id="reach-sub">Loading...</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-label">Carrier Delivery Rate</span>
                    <span class="kpi-icon" style="color: var(--accent-cyan);">📲</span>
                </div>
                <div class="kpi-val" id="delivery-val" style="color: var(--accent-cyan);">0%</div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" id="delivery-bar" style="width: 0%; background: var(--accent-cyan);"></div>
                </div>
                <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.6rem;" id="delivery-sub">Loading...</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-label">Appointments Processed</span>
                    <span class="kpi-icon" style="color: var(--accent-purple);">📅</span>
                </div>
                <div class="kpi-val" id="app-val" style="color: var(--text-main);">0</div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: 100%; background: var(--accent-purple);"></div>
                </div>
                <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.6rem;" id="resident-sub">Loading...</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-header">
                    <span class="kpi-label">Policy Blocks & Safety</span>
                    <span class="kpi-icon" style="color: var(--accent-amber);">🛡️</span>
                </div>
                <div class="kpi-val" id="safety-val" style="color: var(--accent-amber);">0</div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: 100%; background: var(--accent-amber);"></div>
                </div>
                <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.6rem;" id="safety-sub">Loading...</div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="tabs-nav">
            <button class="tab-btn active" onclick="switchTab('overview')">📊 Overview & Performance</button>
            <button class="tab-btn" onclick="switchTab('audit')">📋 Interactive Audit Log Explorer</button>
            <button class="tab-btn" onclick="switchTab('policy')">🛡️ Contact Policy Rules</button>
        </div>

        <!-- TAB 1: Overview -->
        <div id="tab-overview" class="tab-content active">
            <div class="panels-grid">
                <div class="panel-card">
                    <div class="panel-title">
                        <span>Channel Performance</span>
                        <span style="font-size: 0.8rem; font-weight: 500; color: var(--text-muted);">Bounded Fallback: SMS ➔ Voice ➔ Email</span>
                    </div>
                    <div id="channel-content">Loading...</div>
                </div>

                <div class="panel-card">
                    <div class="panel-title">
                        <span>Language Distribution</span>
                        <span style="font-size: 0.8rem; font-weight: 500; color: var(--text-muted);">Multilingual Templates</span>
                    </div>
                    <div id="language-content">Loading...</div>
                </div>
            </div>
        </div>

        <!-- TAB 2: Audit Explorer -->
        <div id="tab-audit" class="tab-content">
            <div class="panel-card">
                <div class="filter-bar">
                    <div class="search-box">
                        <span class="search-icon">🔍</span>
                        <input type="text" id="search-input" placeholder="Search Resident ID, Appt ID, Location, Contact..." oninput="filterAuditTable()">
                    </div>
                    <div style="display: flex; gap: 0.8rem;">
                        <select id="channel-filter" class="filter-select" onchange="filterAuditTable()">
                            <option value="ALL">All Channels</option>
                            <option value="sms">SMS</option>
                            <option value="voice">Voice</option>
                            <option value="email">Email</option>
                        </select>
                        <select id="status-filter" class="filter-select" onchange="filterAuditTable()">
                            <option value="ALL">All Statuses</option>
                            <option value="reached">Reached (Human)</option>
                            <option value="delivered">Delivered</option>
                            <option value="failed">Failed</option>
                            <option value="blocked">Blocked (Policy)</option>
                        </select>
                    </div>
                </div>

                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Appointment ID</th>
                                <th>Resident ID</th>
                                <th>Channel</th>
                                <th>Contact Point</th>
                                <th>Language</th>
                                <th>Status</th>
                                <th>Outcome / Detail</th>
                                <th>Attempt #</th>
                            </tr>
                        </thead>
                        <tbody id="audit-tbody">
                            <tr><td colspan="8" style="text-align: center; padding: 2rem;">Loading audit records...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 3: Policy Rules -->
        <div id="tab-policy" class="tab-content">
            <div class="panel-card">
                <div class="panel-title">Centralized Policy Rules & Safety Standards</div>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; margin-top: 1rem;">
                    <div style="background: rgba(15, 23, 42, 0.8); padding: 1.25rem; border-radius: 14px; border: 1px solid var(--border-card);">
                        <h4 style="color: var(--accent-cyan); margin-bottom: 0.5rem;">🌙 Quiet Hours Enforcer</h4>
                        <p style="font-size: 0.88rem; color: var(--text-muted);">Quiet hours run from 20:00 to 08:00 local time. Reminders scheduled during quiet hours are deferred to 08:00 AM the following morning.</p>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.8); padding: 1.25rem; border-radius: 14px; border: 1px solid var(--border-card);">
                        <h4 style="color: var(--accent-amber); margin-bottom: 0.5rem;">📵 Landline SMS Protection</h4>
                        <p style="font-size: 0.88rem; color: var(--text-muted);">Numbers in the 555-2xx landline carrier block listed under mobile fields are intercepted by ContactPolicy and prevented from receiving SMS.</p>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.8); padding: 1.25rem; border-radius: 14px; border: 1px solid var(--border-card);">
                        <h4 style="color: var(--accent-emerald); margin-bottom: 0.5rem;">🎯 Confirmed Human Reach</h4>
                        <p style="font-size: 0.88rem; color: var(--text-muted);">SMS delivery and email delivery count as delivery evidence. Only Voice calls answered by a human count as Confirmed Human Reach.</p>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.8); padding: 1.25rem; border-radius: 14px; border: 1px solid var(--border-card);">
                        <h4 style="color: var(--accent-purple); margin-bottom: 0.5rem;">🔄 Shared Contact Deduplication</h4>
                        <p style="font-size: 0.88rem; color: var(--text-muted);">Normalizes phone numbers to digits-only and emails to lowercased strings. Prevents sending duplicate messages to the same contact point.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal for Detailed Entry -->
    <div class="modal-overlay" id="detail-modal" onclick="closeModal(event)">
        <div class="modal-card">
            <span class="modal-close" onclick="closeModalDirect()">&times;</span>
            <h3 style="font-family: 'Outfit', sans-serif; font-size: 1.4rem; margin-bottom: 1rem;" id="modal-title">Appointment Detail</h3>
            <div id="modal-body" style="font-size: 0.9rem; color: var(--text-muted);"></div>
        </div>
    </div>

    <script>
        let auditRecords = [];

        function switchTab(tabName) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById('tab-' + tabName).classList.add('active');
        }

        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();
                renderMetrics(data);
                fetchAudit();
            } catch (err) {
                console.error("Error fetching metrics:", err);
            }
        }

        async function fetchAudit() {
            try {
                const res = await fetch('/api/audit');
                auditRecords = await res.json();
                renderAuditTable(auditRecords);
            } catch (err) {
                console.error("Error fetching audit:", err);
            }
        }

        async function runEngine() {
            try {
                const res = await fetch('/api/run', { method: 'POST' });
                const data = await res.json();
                renderMetrics(data);
                fetchAudit();
                alert("⚡ Reminder Engine Execution Completed!");
            } catch (err) {
                alert("Execution error: " + err);
            }
        }

        function renderMetrics(data) {
            if (!data || !data.summary) return;
            const s = data.summary;
            const r = data.rates;
            const c = data.channels;
            const l = data.languages;

            // Reach Card
            document.getElementById('reach-val').innerText = r.reach_rate_percent + '%';
            document.getElementById('reach-bar').style.width = r.reach_rate_percent + '%';
            document.getElementById('reach-sub').innerText = `${s.residents_reached} of ${s.residents_requiring_reminders} residents reached`;

            // Delivery Card
            document.getElementById('delivery-val').innerText = r.delivery_rate_percent + '%';
            document.getElementById('delivery-bar').style.width = r.delivery_rate_percent + '%';
            document.getElementById('delivery-sub').innerText = `${s.reminder_attempts} total dispatches`;

            // Appt Card
            document.getElementById('app-val').innerText = s.appointments_processed;
            document.getElementById('resident-sub').innerText = `${s.residents_processed} total registered residents`;

            // Safety Card
            const blockedTotal = s.optout_blocked + s.no_eligible_contact + s.duplicate_attempts_prevented;
            document.getElementById('safety-val').innerText = blockedTotal;
            document.getElementById('safety-sub').innerText = `${s.optout_blocked} opt-outs | ${s.no_eligible_contact} no contact info`;

            // Channel Content
            let channelHtml = `
                <div class="stat-row">
                    <div><span class="badge-pill badge-sms">SMS</span> <strong>${c.sms.attempts} Total Attempts</strong></div>
                    <div>${c.sms.delivered} Delivered | ${c.sms.failures} Failures</div>
                </div>
                <div class="stat-row">
                    <div><span class="badge-pill badge-voice">VOICE</span> <strong>${c.voice.attempts} Total Calls</strong></div>
                    <div><strong style="color: var(--accent-emerald);">${c.voice.human_answered} Human Answered</strong> | ${c.voice.voicemail} Voicemail</div>
                </div>
                <div class="stat-row">
                    <div><span class="badge-pill badge-email">EMAIL</span> <strong>${c.email.attempts} Total Dispatches</strong></div>
                    <div>${c.email.delivered} Delivered | ${c.email.failures} Bounces</div>
                </div>
            `;
            document.getElementById('channel-content').innerHTML = channelHtml;

            // Language Content
            let langHtml = '';
            for (const [lang, count] of Object.entries(l.counts_per_language)) {
                langHtml += `
                    <div class="stat-row">
                        <div><strong>${lang.toUpperCase()} Template</strong></div>
                        <div><strong>${count}</strong> reminders rendered</div>
                    </div>
                `;
            }
            langHtml += `<div class="stat-row"><div><strong>English Fallbacks:</strong></div><div>${l.english_fallbacks}</div></div>`;
            document.getElementById('language-content').innerHTML = langHtml;
        }

        function renderAuditTable(records) {
            const tbody = document.getElementById('audit-tbody');
            if (!records || records.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 2rem;">No records found. Click Run Engine.</td></tr>';
                return;
            }

            let html = '';
            records.forEach(r => {
                let tagClass = 'tag-delivered';
                if (r.reached) tagClass = 'tag-reached';
                else if (r.status === 'failed') tagClass = 'tag-failed';
                else if (r.status === 'blocked') tagClass = 'tag-blocked';

                html += `
                    <tr onclick="openRecordModal('${r.appointment_id}', '${r.resident_id}', '${r.channel}', '${r.contact}', '${r.status}', '${r.outcome}', '${r.reason}')" style="cursor: pointer;">
                        <td><strong>${r.appointment_id}</strong></td>
                        <td>${r.resident_id}</td>
                        <td><span class="badge-pill badge-${r.channel}">${r.channel.toUpperCase()}</span></td>
                        <td>${r.contact}</td>
                        <td>${r.language.toUpperCase()}</td>
                        <td><span class="tag-status ${tagClass}">${r.status.toUpperCase()}</span></td>
                        <td>${r.outcome || r.reason}</td>
                        <td>${r.attempt_number}</td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;
        }

        function filterAuditTable() {
            const query = document.getElementById('search-input').value.toLowerCase();
            const channel = document.getElementById('channel-filter').value;
            const status = document.getElementById('status-filter').value;

            const filtered = auditRecords.filter(r => {
                const matchQuery = !query || 
                    r.appointment_id.toLowerCase().includes(query) ||
                    r.resident_id.toLowerCase().includes(query) ||
                    r.contact.toLowerCase().includes(query) ||
                    r.reason.toLowerCase().includes(query);

                const matchChannel = channel === 'ALL' || r.channel === channel;
                const matchStatus = status === 'ALL' || 
                    (status === 'reached' && r.reached) ||
                    (status === 'delivered' && r.status === 'delivered' && !r.reached) ||
                    (status === 'failed' && r.status === 'failed') ||
                    (status === 'blocked' && r.status === 'blocked');

                return matchQuery && matchChannel && matchStatus;
            });

            renderAuditTable(filtered);
        }

        function openRecordModal(appId, resId, ch, contact, status, outcome, reason) {
            document.getElementById('modal-title').innerText = `Appointment ${appId} Audit Details`;
            document.getElementById('modal-body').innerHTML = `
                <p style="margin-bottom: 0.5rem;"><strong>Resident ID:</strong> ${resId}</p>
                <p style="margin-bottom: 0.5rem;"><strong>Channel Used:</strong> ${ch.toUpperCase()}</p>
                <p style="margin-bottom: 0.5rem;"><strong>Contact Destination:</strong> ${contact}</p>
                <p style="margin-bottom: 0.5rem;"><strong>Status:</strong> ${status.toUpperCase()}</p>
                <p style="margin-bottom: 0.5rem;"><strong>Outcome Detail:</strong> ${outcome}</p>
                <p style="margin-bottom: 0.5rem;"><strong>Policy Reason:</strong> ${reason}</p>
            `;
            document.getElementById('detail-modal').style.display = 'flex';
        }

        function closeModal(e) {
            if (e.target.id === 'detail-modal') closeModalDirect();
        }
        function closeModalDirect() {
            document.getElementById('detail-modal').style.display = 'none';
        }

        // Run initial load
        fetchMetrics();
    </script>
</body>
</html>
"""

class DashboardRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        url_path = urllib.parse.urlparse(self.path).path
        
        if url_path == "/" or url_path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(get_dashboard_html().encode("utf-8"))

        elif url_path == "/api/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            contacts = load_contacts("data/contacts.csv")
            appointments = load_appointments("data/appointments.csv")
            policy = ContactPolicy()
            lang_selector = LanguageSelector()
            dedup_service = DeduplicationService()
            dispatcher = ReminderDispatcher(policy, lang_selector, dedup_service)
            planner = ReminderPlanner(policy)

            for app in appointments:
                res = contacts.get(app.resident_id)
                if res:
                    planned_time, _ = planner.plan_reminder_time(app)
                    dispatcher.dispatch_reminder(app, res, planned_time)

            collector = MetricsCollector()
            collector.add_audit_records(dispatcher.audit_records)
            metrics = collector.compute_metrics(len(appointments), len(contacts), lang_selector.fallback_count)
            self.wfile.write(json.dumps(metrics).encode("utf-8"))

        elif url_path == "/api/audit":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            if os.path.exists("audit_log.json"):
                with open("audit_log.json", "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(b"[]")

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url_path = urllib.parse.urlparse(self.path).path
        if url_path == "/api/run":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            contacts = load_contacts("data/contacts.csv")
            appointments = load_appointments("data/appointments.csv")
            policy = ContactPolicy()
            lang_selector = LanguageSelector()
            dedup_service = DeduplicationService()
            dispatcher = ReminderDispatcher(policy, lang_selector, dedup_service)
            planner = ReminderPlanner(policy)

            for app in appointments:
                res = contacts.get(app.resident_id)
                if res:
                    planned_time, _ = planner.plan_reminder_time(app)
                    dispatcher.dispatch_reminder(app, res, planned_time)

            collector = MetricsCollector()
            collector.add_audit_records(dispatcher.audit_records)
            collector.write_audit_log_csv("audit_log.csv")
            collector.write_audit_log_json("audit_log.json")
            metrics = collector.compute_metrics(len(appointments), len(contacts), lang_selector.fallback_count)
            self.wfile.write(json.dumps(metrics).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def start_server():
    print(f"Starting Calder County Dashboard on http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), DashboardRequestHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()
