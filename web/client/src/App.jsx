import React, { useEffect, useState, useRef } from 'react'
import './styles.css'

/* ── Status Badge (USWDS tag style) ── */
function StatusBadge({ status }) {
  const s = (status || 'UNKNOWN').toUpperCase()
  const cls = s === 'PASS' ? 'pass' : s === 'FAIL' ? 'fail' : s === 'NOT ASSESSED' ? 'warn' : 'unknown'
  return <span className={`status-badge ${cls}`}>{s}</span>
}

/* ── Control Card ── */
function ControlCard({ controlId, data }) {
  const [open, setOpen] = useState(false)
  const status = (data.status || 'UNKNOWN').toUpperCase()
  const findings = data.findings || []
  const recs = data.recommendations || []
  const narrative = data.nova_narrative

  return (
    <div className="control-card" onClick={() => setOpen(o => !o)}>
      <div className="control-card-header">
        <span className="control-id">{controlId}</span>
        <StatusBadge status={status} />
        {narrative && <span className="nova-badge">Nova AI</span>}
        <span className="chevron">{open ? '▲' : '▼'}</span>
      </div>
      {open && (
        <div className="control-card-body">
          {findings.length > 0 && (
            <div className="detail-section">
              <h4>Findings</h4>
              <ul>{findings.map((f, i) => <li key={i}>{f}</li>)}</ul>
            </div>
          )}
          {recs.length > 0 && (
            <div className="detail-section">
              <h4>Recommendations</h4>
              <ul>{recs.map((r, i) => <li key={i}>{r}</li>)}</ul>
            </div>
          )}
          {narrative && (
            <div className="nova-narrative">
              <span className="nova-label">Nova AI Narrative</span>
              <p>{narrative}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Family Section ── */
function FamilySection({ familyId, data }) {
  const controls = data.controls || {}
  const total = Object.keys(controls).length
  const passed = Object.values(controls).filter(c => (c.status || '').toUpperCase() === 'PASS').length

  return (
    <div className="family-section">
      <div className="family-header">
        <span className="family-id">{familyId}</span>
        <span className="family-stats">
          <span className="pass-count">{passed} Pass</span>
          {' · '}
          <span className="fail-count">{total - passed} Fail</span>
          {' · '}
          <span>{total} Total</span>
        </span>
      </div>
      <div className="control-list">
        {Object.entries(controls).map(([cid, cdata]) => (
          <ControlCard key={cid} controlId={cid} data={cdata} />
        ))}
      </div>
    </div>
  )
}

/* ── POA&M Table ── */
function PoamTable({ items }) {
  if (!items || items.length === 0) return <p className="empty-panel">No POA&amp;M items.</p>
  const riskClass = lvl => {
    const l = (lvl || '').toUpperCase()
    return l === 'HIGH' ? 'risk-high' : l === 'MODERATE' ? 'risk-moderate' : 'risk-low'
  }
  return (
    <div className="poam-table-wrap">
      <table className="poam-table">
        <thead>
          <tr>
            <th>Item ID</th><th>Control</th><th>Risk Level</th><th>Weakness Description</th>
          </tr>
        </thead>
        <tbody>
          {items.map(item => (
            <tr key={item.item_id}>
              <td className="mono">{item.item_id}</td>
              <td className="mono">{item.control_id}</td>
              <td><span className={riskClass(item.risk_level)}>{item.risk_level}</span></td>
              <td className="weakness-cell">{item.weakness}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════════════════
   Main Application
   ═══════════════════════════════════════════════════════════════════════════ */
export default function App() {
  const [tab, setTab] = useState('run')
  const [files, setFiles] = useState([])
  const [running, setRunning] = useState(false)
  const [runDone, setRunDone] = useState(false)
  const [log, setLog] = useState('')
  const [applySuggestions, setApplySuggestions] = useState(false)
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.9)
  const [contextFile, setContextFile] = useState(null)
  const [report, setReport] = useState(null)
  const [poam, setPoam] = useState(null)
  const [infraSource, setInfraSource] = useState('live')
  const [infraFile, setInfraFile] = useState(null)
  const [configS3Bucket, setConfigS3Bucket] = useState('')
  const [configS3Prefix, setConfigS3Prefix] = useState('')
  const [cfnStacks, setCfnStacks] = useState('')
  const [awsProfile, setAwsProfile] = useState('')
  const [awsRegion, setAwsRegion] = useState('us-east-1')
  const [awsAccessKeyId, setAwsAccessKeyId] = useState('')
  const [awsSecretAccessKey, setAwsSecretAccessKey] = useState('')
  const [showSecret, setShowSecret] = useState(false)
  const [credsSaved, setCredsSaved] = useState(false)
  const logRef = useRef(null)

  /* ── Load saved credentials from localStorage on mount ── */
  useEffect(() => {
    try {
      const saved = localStorage.getItem('bobbie_aws_creds')
      if (saved) {
        const c = JSON.parse(saved)
        if (c.awsProfile !== undefined) setAwsProfile(c.awsProfile)
        if (c.awsRegion !== undefined) setAwsRegion(c.awsRegion)
        if (c.awsAccessKeyId !== undefined) setAwsAccessKeyId(c.awsAccessKeyId)
        if (c.awsSecretAccessKey !== undefined) setAwsSecretAccessKey(c.awsSecretAccessKey)
        setCredsSaved(true)
      }
    } catch {}
  }, [])

  function saveCredentials() {
    try {
      localStorage.setItem('bobbie_aws_creds', JSON.stringify({
        awsProfile, awsRegion, awsAccessKeyId, awsSecretAccessKey
      }))
      setCredsSaved(true)
    } catch {}
  }

  function clearCredentials() {
    try { localStorage.removeItem('bobbie_aws_creds') } catch {}
    setAwsProfile('')
    setAwsRegion('us-east-1')
    setAwsAccessKeyId('')
    setAwsSecretAccessKey('')
    setCredsSaved(false)
  }

  /* ── Data fetching ── */
  async function fetchAll() {
    try {
      const [af, rp, pm] = await Promise.all([
        fetch('/api/artifacts').then(r => r.json()),
        fetch('/api/report').then(r => r.json()),
        fetch('/api/poam').then(r => r.json()),
      ])
      setFiles(af.files || [])
      setReport(rp)
      setPoam(pm)
    } catch (e) { console.error(e) }
  }

  async function handleUpload(e) {
    if (!e.target.files?.[0]) return
    const fd = new FormData()
    fd.append('file', e.target.files[0])
    try {
      const r = await fetch('/api/upload', { method: 'POST', body: fd })
      if (!r.ok) throw new Error()
      const j = await r.json()
      setContextFile(j.filename)
    } catch { alert('Upload failed') }
  }

  async function handleInfraUpload(e) {
    if (!e.target.files?.[0]) return
    const fd = new FormData()
    fd.append('file', e.target.files[0])
    try {
      const r = await fetch('/api/upload', { method: 'POST', body: fd })
      if (!r.ok) throw new Error()
      const j = await r.json()
      setInfraFile(j.filename)
    } catch { alert('Infrastructure file upload failed') }
  }

  async function runAssessment() {
    setRunning(true)
    setRunDone(false)
    setLog('')
    setTab('run')
    const payload = { applySuggestions, confidenceThreshold: parseFloat(confidenceThreshold), infraSource }
    if (infraSource !== 'live') {
      if (infraFile) payload.infraFile = infraFile
      if (infraSource === 'aws-config') {
        if (configS3Bucket) payload.configS3Bucket = configS3Bucket
        if (configS3Prefix) payload.configS3Prefix = configS3Prefix
      }
      if (infraSource === 'cloudformation' && cfnStacks) payload.cfnStacks = cfnStacks
    }
    if (awsProfile.trim()) payload.awsProfile = awsProfile.trim()
    if (awsRegion.trim()) payload.awsRegion = awsRegion.trim()
    if (awsAccessKeyId.trim()) payload.awsAccessKeyId = awsAccessKeyId.trim()
    if (awsSecretAccessKey.trim()) payload.awsSecretAccessKey = awsSecretAccessKey.trim()
    if (contextFile) payload.contextFile = contextFile
    try {
      await fetch('/api/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      pollLog()
    } catch (e) { console.error(e); setRunning(false) }
  }

  function pollLog() {
    const iv = setInterval(async () => {
      try {
        const j = await fetch('/api/log').then(r => r.json())
        setLog(j.log || '')
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
        if ((j.log || '').includes('Process exited')) {
          clearInterval(iv)
          setRunning(false)
          setRunDone(true)
          fetchAll()
          setTab('results')
        }
      } catch (e) { console.error(e) }
    }, 1500)
  }

  // Results are intentionally NOT pre-loaded on mount — the app starts in a
  // clean state. fetchAll() is called only after a run completes (in pollLog).

  const summaryStats = report?.summary || {}
  const families = report?.families || {}
  const poamItems = poam?.['plan-of-action-and-milestones']?.['poam-items'] || []

  const INFRA_OPTIONS = [
    { id: 'live',           label: 'Live API',        desc: 'Direct AWS API calls' },
    { id: 'terraform',      label: 'Terraform',       desc: '.tfstate file' },
    { id: 'aws-config',     label: 'AWS Config',      desc: 'Config snapshot' },
    { id: 'cloudformation', label: 'CloudFormation',  desc: 'Deployed stacks' },
  ]

  return (
    <div className="shell">
      {/* ── Official Banner ── */}
      <div className="gov-banner">
        <span className="flag">🛡️</span>
        NIST SP 800-53 Rev 5 Automated Compliance Assessment Tool
      </div>

      {/* ── Top Header ── */}
      <header className="top-header">
        <div className="top-header-left">
          <div className="brand-shield">B</div>
          <div>
            <div className="brand-name">B.O.B.B.I.E.</div>
            <div className="brand-desc">Bedrock-Orchestrated Baseline &amp; Behavior Intelligence Engine</div>
          </div>
        </div>
        <div className="header-meta">
          <span>AWS Bedrock Nova</span>
          <span>OSCAL 1.2.0</span>
          <span>
            <span className={`status-dot ${running ? 'active' : 'idle'}`} />
            {' '}{running ? 'Assessment Running' : 'Ready'}
          </span>
        </div>
      </header>

      <div className="shell-body">
        {/* ── Sidebar ── */}
        <aside className="sidebar">
          {/* Nova AI Controls */}
          <div className="sidebar-section">
            <div className="sidebar-section-title">Nova AI Configuration</div>
            <label className="toggle-row">
              <span>Apply Suggestions</span>
              <div className={`toggle ${applySuggestions ? 'on' : ''}`} onClick={() => !running && setApplySuggestions(v => !v)}>
                <div className="toggle-knob" />
              </div>
            </label>
            <div className="threshold-row">
              <span>Confidence Threshold: <strong>{parseFloat(confidenceThreshold).toFixed(2)}</strong></span>
              <input type="range" min="0.5" max="1.0" step="0.05" value={confidenceThreshold}
                onChange={e => setConfidenceThreshold(e.target.value)} disabled={running} />
            </div>
          </div>

          {/* Infrastructure Source */}
          <div className="sidebar-section">
            <div className="sidebar-section-title">Infrastructure Source</div>
            <div className="infra-source-grid">
              {INFRA_OPTIONS.map(opt => (
                <button
                  key={opt.id}
                  className={`infra-btn ${infraSource === opt.id ? 'active' : ''}`}
                  onClick={() => !running && setInfraSource(opt.id)}
                  disabled={running}
                  title={opt.desc}
                >
                  <span className="infra-btn-label">{opt.label}</span>
                  <span className="infra-btn-desc">{opt.desc}</span>
                </button>
              ))}
            </div>

            {infraSource === 'terraform' && (
              <div className="infra-sub">
                <label className="upload-label">
                  <input type="file" accept=".tfstate,.json" onChange={handleInfraUpload} disabled={running} style={{ display: 'none' }} />
                  <span className={`upload-btn${infraFile ? ' has-file' : ''}`}>{infraFile ? '✓ ' + infraFile : 'Upload .tfstate file'}</span>
                </label>
              </div>
            )}

            {infraSource === 'aws-config' && (
              <div className="infra-sub">
                <label className="upload-label">
                  <input type="file" accept=".json,.gz" onChange={handleInfraUpload} disabled={running} style={{ display: 'none' }} />
                  <span className={`upload-btn${infraFile ? ' has-file' : ''}`}>{infraFile ? '✓ ' + infraFile : 'Upload snapshot JSON'}</span>
                </label>
                <div className="infra-or">or pull from S3</div>
                <input className="infra-input" placeholder="S3 bucket name" value={configS3Bucket}
                  onChange={e => setConfigS3Bucket(e.target.value)} disabled={running} />
                <input className="infra-input" placeholder="Key prefix (optional)" value={configS3Prefix}
                  onChange={e => setConfigS3Prefix(e.target.value)} disabled={running} />
              </div>
            )}

            {infraSource === 'cloudformation' && (
              <div className="infra-sub">
                <input className="infra-input" placeholder="Stack names (comma-separated, blank = all)"
                  value={cfnStacks} onChange={e => setCfnStacks(e.target.value)} disabled={running} />
              </div>
            )}
          </div>

          {/* AWS Credentials — only visible for Live API source */}
          {infraSource === 'live' && <div className="sidebar-section">
            <div className="sidebar-section-title">
              AWS Credentials
              {credsSaved && <span className="creds-saved-badge">✓ Saved</span>}
            </div>
            <div className="infra-sub">
              <input
                className="infra-input"
                placeholder="Named profile (default: bobbie)"
                value={awsProfile}
                onChange={e => { setAwsProfile(e.target.value); setCredsSaved(false) }}
                disabled={running}
              />
              <input
                className="infra-input"
                placeholder="AWS region (default: us-east-1)"
                value={awsRegion}
                onChange={e => { setAwsRegion(e.target.value); setCredsSaved(false) }}
                disabled={running}
              />
              <div className="creds-divider">or use access keys</div>
              <input
                className="infra-input"
                placeholder="AWS Access Key ID"
                value={awsAccessKeyId}
                onChange={e => { setAwsAccessKeyId(e.target.value); setCredsSaved(false) }}
                disabled={running}
                autoComplete="off"
              />
              <div className="secret-row">
                <input
                  className="infra-input secret-input"
                  type={showSecret ? 'text' : 'password'}
                  placeholder="AWS Secret Access Key"
                  value={awsSecretAccessKey}
                  onChange={e => { setAwsSecretAccessKey(e.target.value); setCredsSaved(false) }}
                  disabled={running}
                  autoComplete="off"
                />
                <button
                  className="secret-toggle"
                  type="button"
                  onClick={() => setShowSecret(v => !v)}
                  tabIndex={-1}
                >{showSecret ? 'Hide' : 'Show'}</button>
              </div>
              <div className="creds-actions">
                <button
                  className="creds-save-btn"
                  type="button"
                  onClick={saveCredentials}
                  disabled={running}
                >Save credentials</button>
                {credsSaved && (
                  <button
                    className="creds-clear-btn"
                    type="button"
                    onClick={clearCredentials}
                    disabled={running}
                  >Clear</button>
                )}
              </div>
            </div>
          </div>}

          {/* Context Evidence */}
          <div className="sidebar-section">
            <div className="sidebar-section-title">Context Evidence</div>
            <div className="infra-sub">
              <label className="upload-label">
                <input type="file" accept=".json" onChange={handleUpload} disabled={running} style={{ display: 'none' }} />
                <span className={`upload-btn${contextFile ? ' has-file' : ''}`}>
                  {contextFile ? '✓ ' + contextFile : 'Upload context_evidence.json'}
                </span>
              </label>
              {contextFile && (
                <button
                  className="context-clear-btn"
                  type="button"
                  onClick={() => setContextFile(null)}
                  disabled={running}
                >✕ Clear evidence file</button>
              )}
              <p className="context-hint">Optional JSON file providing <code>control_evidence</code> for AC-2, AU-3, IA-5, RA-5, SI-2, and other evidence-driven controls.</p>
            </div>
          </div>

          {/* Run Button */}
          <button className={`run-btn ${running ? 'running' : ''}`} onClick={runAssessment} disabled={running}>
            {running ? <><span className="spinner" /> Running Assessment…</> : 'Run Assessment'}
          </button>

          {runDone && (
            <div className="run-done">
              Assessment complete
              <button className="view-results-btn" onClick={() => setTab('results')}>View Results →</button>
            </div>
          )}
        </aside>

        {/* ── Main Content ── */}
        <div className="main">
          <nav className="tabs">
            {[
              ['run',       'Live Log'],
              ['results',   'Results'],
              ['poam',      'POA&M'],
              ['artifacts', 'Artifacts'],
            ].map(([id, label]) => (
              <button key={id} className={`tab-btn ${tab === id ? 'active' : ''}`} onClick={() => setTab(id)}>
                {label}
              </button>
            ))}
          </nav>

          <div className="tab-content">
            {/* ── Live Log Tab ── */}
            {tab === 'run' && (
              <div className="log-panel">
                {summaryStats.total_controls != null && !running && (
                  <div className="summary-bar">
                    <div className="sstat"><span className="sstat-val">{summaryStats.total_controls}</span><span className="sstat-label">Total Controls</span></div>
                    <div className="sstat"><span className="sstat-val pass">{summaryStats.passed}</span><span className="sstat-label">Passed</span></div>
                    <div className="sstat"><span className="sstat-val fail">{summaryStats.failed}</span><span className="sstat-label">Failed</span></div>
                    <div className="sstat"><span className="sstat-val compliance">{summaryStats.compliance_score ?? '—'}%</span><span className="sstat-label">Compliance</span></div>
                  </div>
                )}
                <div className="log-status-row">
                  <span className={`dot ${running ? 'pulse' : 'idle'}`} />
                  {running ? 'Assessment in progress…' : log ? 'Last run output' : 'Ready to begin assessment'}
                </div>
                <pre ref={logRef} className="log-output">{log || 'Configure assessment parameters and click Run Assessment to begin.'}</pre>
              </div>
            )}

            {/* ── Results Tab ── */}
            {tab === 'results' && (
              <div className="results-panel">
                {!report ? (
                  <div className="empty-panel">No assessment results available. Run an assessment to generate findings.</div>
                ) : (
                  <>
                    <div className="summary-bar">
                      <div className="sstat"><span className="sstat-val">{summaryStats.total_controls}</span><span className="sstat-label">Total Controls</span></div>
                      <div className="sstat"><span className="sstat-val pass">{summaryStats.passed}</span><span className="sstat-label">Passed</span></div>
                      <div className="sstat"><span className="sstat-val fail">{summaryStats.failed}</span><span className="sstat-label">Failed</span></div>
              <div className="sstat"><span className="sstat-val compliance">{summaryStats.compliance_score ?? '—'}%</span><span className="sstat-label">Compliance</span></div>
                    </div>
                    {Object.entries(families).map(([fid, fdata]) => (
                      <FamilySection key={fid} familyId={fid} data={fdata} />
                    ))}
                  </>
                )}
              </div>
            )}

            {/* ── POA&M Tab ── */}
            {tab === 'poam' && (
              <div className="results-panel">
                {!poam ? (
                  <div className="empty-panel">No Plan of Action &amp; Milestones available. Run an assessment to generate POA&amp;M.</div>
                ) : (
                  <>
                    <div className="poam-meta">
                      <span>OSCAL Version {poam.oscal_version}</span>
                      <span>{poamItems.length} Items</span>
                      <span>Last Modified: {poam?.['plan-of-action-and-milestones']?.metadata?.['last-modified'] || '—'}</span>
                    </div>
                    <PoamTable items={poamItems} />
                  </>
                )}
              </div>
            )}

            {/* ── Artifacts Tab ── */}
            {tab === 'artifacts' && (
              <div className="results-panel">
                {files.length === 0 ? (
                  <div className="empty-panel">No artifacts generated yet.</div>
                ) : (
                  <div className="artifact-grid">
                    {files.map(f => {
                      const ext = f.split('.').pop()
                      const icon = ext === 'json' ? '{ }' : ext === 'txt' ? 'TXT' : ext === 'log' ? 'LOG' : 'DOC'
                      return (
                        <a key={f} href={`/api/artifacts/${f}`} target="_blank" rel="noreferrer" className="artifact-card">
                          <span className="artifact-icon">{icon}</span>
                          <span className="artifact-name">{f}</span>
                          <span className="artifact-dl">↓</span>
                        </a>
                      )
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
