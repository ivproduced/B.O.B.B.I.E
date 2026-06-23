import React, { useEffect, useState, useRef } from 'react'
import './styles.css'
import {
  FAMILIES, familyName, familyBlurb, statusInfo, riskKey,
  readiness, artifactLabel, progressHint,
} from './lib'

/* ════════════════════════════════════════════════════════════════════
   Small presentational pieces
   ════════════════════════════════════════════════════════════════════ */

function StatusPill({ status }) {
  const { key, label } = statusInfo(status)
  return <span className={`pill pill-${key}`}>{label}</span>
}

function RiskPill({ level }) {
  if (!level) return null
  return <span className={`risk-pill risk-${riskKey(level)}`}>{String(level).toUpperCase()} risk</span>
}

function StatCard({ value, label, tone }) {
  return (
    <div className="stat-card">
      <div className={`stat-value ${tone || ''}`}>{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

function ScoreRing({ score }) {
  const s = Math.max(0, Math.min(100, Number(score) || 0))
  const tone = s >= 70 ? 'var(--ok)' : s >= 50 ? 'var(--warn)' : 'var(--bad)'
  return (
    <div className="score-ring" style={{ background: `conic-gradient(${tone} ${s * 3.6}deg, var(--surface-3) 0deg)` }}>
      <div className="score-ring-inner">
        <span className="score-ring-num">{s}%</span>
        <span className="score-ring-cap">Compliant</span>
      </div>
    </div>
  )
}

/* ════════════════════════════════════════════════════════════════════
   1. Start screen — guided, plain-language setup
   ════════════════════════════════════════════════════════════════════ */

const INFRA_OPTIONS = [
  { id: 'live',           label: 'Connect to AWS',     desc: 'Assess the live cloud environment directly' },
  { id: 'terraform',      label: 'Terraform file',     desc: 'Use an exported infrastructure (.tfstate) file' },
  { id: 'aws-config',     label: 'AWS Config export',  desc: 'Use a configuration snapshot' },
  { id: 'cloudformation', label: 'CloudFormation',     desc: 'Assess deployed CloudFormation stacks' },
]

function StartScreen(props) {
  const {
    running, hasResults, onViewResults, onRun,
    systemName, setSystemName,
    infraSource, setInfraSource,
    infraFile, handleInfraUpload,
    configS3Bucket, setConfigS3Bucket, configS3Prefix, setConfigS3Prefix,
    cfnStacks, setCfnStacks,
    contextFile, setContextFile, handleUpload,
    advanced, setAdvanced,
    awsProfile, setAwsProfile, awsRegion, setAwsRegion,
    awsAccessKeyId, setAwsAccessKeyId, awsSecretAccessKey, setAwsSecretAccessKey,
    showSecret, setShowSecret,
    llmProvider, setLlmProvider, llmModel, setLlmModel,
    llmBaseUrl, setLlmBaseUrl, llmApiKey, setLlmApiKey, showLlmKey, setShowLlmKey,
    applySuggestions, setApplySuggestions,
    confidenceThreshold, setConfidenceThreshold,
  } = props

  return (
    <div className="start-wrap">
      <div className="start-card">
        <div className="start-head">
          <h1>Start a compliance assessment</h1>
          <p>Answer a few questions and B.O.B.B.I.E. will evaluate the system against the NIST SP 800-53 security controls. No technical expertise required.</p>
        </div>

        {/* System name */}
        <section className="field-block">
          <label className="field-label" htmlFor="sysname">What system are you assessing?</label>
          <p className="field-help">This name appears on the assessment report.</p>
          <input id="sysname" className="text-input" placeholder="e.g. Agency Case Management System"
            value={systemName} onChange={e => setSystemName(e.target.value)} disabled={running} />
        </section>

        {/* Infra source */}
        <section className="field-block">
          <label className="field-label">Where should we gather information from?</label>
          <p className="field-help">Choose how B.O.B.B.I.E. should look at the system being assessed.</p>
          <div className="choice-grid">
            {INFRA_OPTIONS.map(opt => (
              <button key={opt.id} type="button"
                className={`choice-card ${infraSource === opt.id ? 'active' : ''}`}
                onClick={() => !running && setInfraSource(opt.id)} disabled={running}>
                <span className="choice-title">{opt.label}</span>
                <span className="choice-desc">{opt.desc}</span>
              </button>
            ))}
          </div>

          {infraSource === 'terraform' && (
            <label className="upload-label">
              <input type="file" accept=".tfstate,.json" onChange={handleInfraUpload} disabled={running} hidden />
              <span className={`upload-btn${infraFile ? ' has-file' : ''}`}>{infraFile ? '✓ ' + infraFile : 'Upload .tfstate file'}</span>
            </label>
          )}
          {infraSource === 'aws-config' && (
            <div className="sub-fields">
              <label className="upload-label">
                <input type="file" accept=".json,.gz" onChange={handleInfraUpload} disabled={running} hidden />
                <span className={`upload-btn${infraFile ? ' has-file' : ''}`}>{infraFile ? '✓ ' + infraFile : 'Upload snapshot file'}</span>
              </label>
              <div className="sub-or">or pull from S3</div>
              <input className="text-input" placeholder="S3 bucket name" value={configS3Bucket}
                onChange={e => setConfigS3Bucket(e.target.value)} disabled={running} />
              <input className="text-input" placeholder="Key prefix (optional)" value={configS3Prefix}
                onChange={e => setConfigS3Prefix(e.target.value)} disabled={running} />
            </div>
          )}
          {infraSource === 'cloudformation' && (
            <input className="text-input" placeholder="Stack names (comma-separated; leave blank for all)"
              value={cfnStacks} onChange={e => setCfnStacks(e.target.value)} disabled={running} />
          )}
        </section>

        {/* Evidence */}
        <section className="field-block">
          <label className="field-label">Supporting evidence <span className="optional">optional</span></label>
          <p className="field-help">If you have a JSON evidence file for controls like account management or audit logging, add it here.</p>
          <label className="upload-label">
            <input type="file" accept=".json" onChange={handleUpload} disabled={running} hidden />
            <span className={`upload-btn${contextFile ? ' has-file' : ''}`}>{contextFile ? '✓ ' + contextFile : 'Upload evidence file'}</span>
          </label>
          {contextFile && <button className="link-btn" type="button" onClick={() => setContextFile(null)} disabled={running}>Remove file</button>}
        </section>

        {/* Advanced */}
        <section className="field-block">
          <button type="button" className="advanced-toggle" onClick={() => setAdvanced(a => !a)}>
            <span className="chev">{advanced ? '▾' : '▸'}</span> Advanced settings
            <span className="advanced-note">connection, AI model, and tuning — defaults work for most users</span>
          </button>

          {advanced && (
            <div className="advanced-body">
              {infraSource === 'live' && (
                <div className="adv-group">
                  <h4>Connection (AWS)</h4>
                  <input className="text-input" placeholder="Named profile (default: bobbie)" value={awsProfile}
                    onChange={e => setAwsProfile(e.target.value)} disabled={running} />
                  <input className="text-input" placeholder="Region (default: us-east-1)" value={awsRegion}
                    onChange={e => setAwsRegion(e.target.value)} disabled={running} />
                  <div className="sub-or">or use access keys</div>
                  <input className="text-input" placeholder="Access Key ID" value={awsAccessKeyId} autoComplete="off"
                    onChange={e => setAwsAccessKeyId(e.target.value)} disabled={running} />
                  <div className="secret-row">
                    <input className="text-input" type={showSecret ? 'text' : 'password'} placeholder="Secret Access Key"
                      value={awsSecretAccessKey} autoComplete="off" onChange={e => setAwsSecretAccessKey(e.target.value)} disabled={running} />
                    <button className="secret-toggle" type="button" aria-label={showSecret ? 'Hide secret access key' : 'Show secret access key'} aria-pressed={showSecret} onClick={() => setShowSecret(v => !v)}>{showSecret ? 'Hide' : 'Show'}</button>
                  </div>
                </div>
              )}

              <div className="adv-group">
                <h4>AI narrative model</h4>
                <div className="seg">
                  <button type="button" className={llmProvider === 'bedrock' ? 'on' : ''} onClick={() => !running && setLlmProvider('bedrock')} disabled={running}>AWS Bedrock</button>
                  <button type="button" className={llmProvider === 'openai' ? 'on' : ''} onClick={() => !running && setLlmProvider('openai')} disabled={running}>OpenAI / compatible</button>
                </div>
                <input className="text-input" placeholder={llmProvider === 'bedrock' ? 'Model ID (default: amazon.nova-2-lite-v1:0)' : 'Model ID (default: gpt-4o)'}
                  value={llmModel} onChange={e => setLlmModel(e.target.value)} disabled={running} />
                {llmProvider === 'openai' && (
                  <>
                    <input className="text-input" placeholder="Base URL (e.g. http://localhost:11434/v1)" value={llmBaseUrl}
                      onChange={e => setLlmBaseUrl(e.target.value)} disabled={running} />
                    <div className="secret-row">
                      <input className="text-input" type={showLlmKey ? 'text' : 'password'} placeholder="API key" value={llmApiKey}
                        autoComplete="off" onChange={e => setLlmApiKey(e.target.value)} disabled={running} />
                      <button className="secret-toggle" type="button" aria-label={showLlmKey ? 'Hide API key' : 'Show API key'} aria-pressed={showLlmKey} onClick={() => setShowLlmKey(v => !v)}>{showLlmKey ? 'Hide' : 'Show'}</button>
                    </div>
                  </>
                )}
              </div>

              <div className="adv-group">
                <h4>Assessment tuning</h4>
                <label className="check-row">
                  <input type="checkbox" checked={applySuggestions} onChange={e => setApplySuggestions(e.target.checked)} disabled={running} />
                  <span>Let the AI auto-apply high-confidence status suggestions</span>
                </label>
                <div className="slider-row">
                  <span>Confidence threshold: <strong>{parseFloat(confidenceThreshold).toFixed(2)}</strong></span>
                  <input type="range" min="0.5" max="1.0" step="0.05" value={confidenceThreshold}
                    onChange={e => setConfidenceThreshold(e.target.value)} disabled={running} />
                </div>
              </div>
            </div>
          )}
        </section>

        <div className="start-actions">
          <button className="primary-btn big" onClick={onRun} disabled={running}>Begin assessment</button>
          {hasResults && <button className="ghost-btn" onClick={onViewResults} disabled={running}>View latest results</button>}
        </div>
      </div>
    </div>
  )
}

/* ════════════════════════════════════════════════════════════════════
   2. Progress view — plain-language running state
   ════════════════════════════════════════════════════════════════════ */

function ProgressView({ log, elapsed }) {
  const [showLog, setShowLog] = useState(false)
  const logRef = useRef(null)
  useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight }, [log])
  const mm = String(Math.floor(elapsed / 60)).padStart(2, '0')
  const ss = String(elapsed % 60).padStart(2, '0')
  return (
    <div className="progress-wrap">
      <div className="progress-card">
        <div className="big-spinner" />
        <h2>Assessment in progress</h2>
        <p className="progress-hint">{progressHint(log)}</p>
        <div className="progress-elapsed">Elapsed {mm}:{ss}</div>
        <p className="progress-reassure">This usually takes a minute or two. You can stay on this page — results will appear automatically when it finishes.</p>
        <button className="link-btn" onClick={() => setShowLog(s => !s)}>{showLog ? 'Hide technical details' : 'Show technical details'}</button>
        {showLog && <pre ref={logRef} className="tech-log">{log || 'Waiting for output…'}</pre>}
      </div>
    </div>
  )
}

/* ════════════════════════════════════════════════════════════════════
   3. Overview — single-engagement posture
   ════════════════════════════════════════════════════════════════════ */

function Overview({ report, poamItems, onJump }) {
  const s = report?.summary || {}
  const verdict = readiness(s.compliance_score)
  const families = report?.families || {}
  const top = (s.prioritized_findings || []).slice(0, 6)

  const riskCounts = poamItems.reduce((acc, it) => {
    const k = riskKey(it.risk_level); acc[k] = (acc[k] || 0) + 1; return acc
  }, {})
  const riskOrder = [['high', 'High'], ['medium', 'Medium'], ['low', 'Low']]
  const maxRisk = Math.max(1, ...riskOrder.map(([k]) => riskCounts[k] || 0))

  return (
    <div className="view-pad">
      <div className={`verdict-banner v-${verdict.key}`}>
        <ScoreRing score={s.compliance_score} />
        <div className="verdict-text">
          <h2>{verdict.title}</h2>
          <p>{verdict.blurb}</p>
          <p className="verdict-count">
            <strong>{s.failed ?? 0}</strong> of <strong>{s.total_controls ?? 0}</strong> assessed controls need attention.
          </p>
        </div>
      </div>

      <div className="stat-row">
        <StatCard value={s.total_controls ?? '—'} label="Controls assessed" />
        <StatCard value={s.passed ?? '—'} label="Compliant" tone="ok" />
        <StatCard value={s.failed ?? '—'} label="Need attention" tone="bad" />
        <StatCard value={(s.compliance_score ?? '—') + '%'} label="Compliance score" />
      </div>

      <div className="overview-cols">
        <section className="panel">
          <h3 className="panel-title">Top things to address</h3>
          {top.length === 0 ? (
            <p className="empty-note">No outstanding findings. Every assessed control is compliant.</p>
          ) : (
            <ul className="todo-list">
              {top.map((f, i) => (
                <li key={i} className="todo-item">
                  <button type="button" className="todo-button" onClick={() => onJump(f.control_id)}>
                    <span className="todo-main">
                      <RiskPill level={f.risk_level} />
                      <span className="todo-ctl">{f.control_id} · {familyName(f.family_id)}</span>
                    </span>
                    <span className="todo-finding">{f.finding}</span>
                    <span className="todo-link">Review control →</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel">
          <h3 className="panel-title">Findings by risk level</h3>
          {poamItems.length === 0 ? (
            <p className="empty-note">No risk-rated findings.</p>
          ) : (
            <div className="risk-bars">
              {riskOrder.map(([k, label]) => (
                <div key={k} className="risk-bar-row">
                  <span className="risk-bar-label">{label}</span>
                  <div className="risk-bar-track">
                    <div className={`risk-bar-fill rb-${k}`} style={{ width: `${((riskCounts[k] || 0) / maxRisk) * 100}%` }} />
                  </div>
                  <span className="risk-bar-num">{riskCounts[k] || 0}</span>
                </div>
              ))}
            </div>
          )}

          <h3 className="panel-title" style={{ marginTop: '1.5rem' }}>Control families</h3>
          <div className="family-mini-list">
            {Object.entries(families).map(([fid, fdata]) => {
              const fs = fdata.summary || {}
              const ok = fs.failed === 0
              return (
                <button key={fid} className="family-mini" onClick={() => onJump(null, fid)}>
                  <span className="fm-id">{fid}</span>
                  <span className="fm-name">{familyName(fid)}</span>
                  <span className={`fm-badge ${ok ? 'ok' : 'bad'}`}>{ok ? 'All clear' : `${fs.failed} to review`}</span>
                </button>
              )
            })}
          </div>
        </section>
      </div>
    </div>
  )
}

/* ════════════════════════════════════════════════════════════════════
   4. Review — controls, findings, evidence
   ════════════════════════════════════════════════════════════════════ */

function ControlCard({ fid, controlId, data, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen)
  const [showEvidence, setShowEvidence] = useState(false)
  useEffect(() => { if (defaultOpen) setOpen(true) }, [defaultOpen])

  const { key: skey } = statusInfo(data.status)
  const findings = data.findings || []
  const recs = data.recommendations || []
  const narrative = data.nova_narrative
  const ev = data.evidence || {}
  const title = ev.title ? ev.title.replace(/\b\w/g, c => c.toUpperCase()) : ''
  const baselines = ev.baselines ? Object.entries(ev.baselines).filter(([, v]) => v).map(([k]) => k) : []

  return (
    <div className={`control-card c-${skey}`} id={`ctl-${controlId}`}>
      <button className="control-head" onClick={() => setOpen(o => !o)}>
        <div className="control-head-main">
          <span className="control-id">{controlId}</span>
          {title && <span className="control-title">{title}</span>}
        </div>
        <div className="control-head-meta">
          <StatusPill status={data.status} />
          {skey === 'fail' && <RiskPill level={data.risk_level} />}
          <span className="chev">{open ? '▾' : '▸'}</span>
        </div>
      </button>

      {open && (
        <div className="control-body">
          {findings.length > 0 ? (
            <div className="cb-section">
              <h5>What we found</h5>
              <ul>{findings.map((f, i) => <li key={i}>{f}</li>)}</ul>
            </div>
          ) : skey === 'pass' ? (
            <p className="cb-clear">No issues found — this control meets its requirements.</p>
          ) : null}

          {recs.length > 0 && (
            <div className="cb-section">
              <h5>Recommended actions</h5>
              <ul>{recs.map((r, i) => <li key={i}>{r}</li>)}</ul>
            </div>
          )}

          {narrative && (
            <div className="cb-narrative">
              <span className="cb-narrative-label">Plain-language summary</span>
              <p>{narrative}</p>
            </div>
          )}

          <div className="cb-meta">
            {baselines.length > 0 && (
              <div className="baseline-tags">
                <span className="baseline-cap">Applies to baselines:</span>
                {baselines.map(b => <span key={b} className="baseline-tag">{b}</span>)}
              </div>
            )}
            {typeof data.confidence_score === 'number' && (
              <span className="confidence-note">Assessment confidence: {Math.round(data.confidence_score * 100)}%</span>
            )}
          </div>

          {ev && Object.keys(ev).length > 0 && (
            <div className="cb-section">
              <button className="link-btn" onClick={() => setShowEvidence(v => !v)}>
                {showEvidence ? 'Hide supporting evidence' : 'View supporting evidence'}
              </button>
              {showEvidence && <pre className="evidence-json">{JSON.stringify(ev, null, 2)}</pre>}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Review({ report, filters, setFilters, jumpControl }) {
  const families = report?.families || {}

  // Flatten controls with family id
  const all = []
  Object.entries(families).forEach(([fid, fdata]) => {
    Object.entries(fdata.controls || {}).forEach(([cid, cdata]) => {
      all.push({ fid, cid, cdata })
    })
  })

  const q = filters.q.trim().toLowerCase()
  const filtered = all.filter(({ fid, cid, cdata }) => {
    const sinfo = statusInfo(cdata.status).key
    if (filters.status !== 'all' && sinfo !== filters.status) return false
    if (filters.risk !== 'all' && riskKey(cdata.risk_level) !== filters.risk) return false
    if (filters.family !== 'all' && fid !== filters.family) return false
    if (q) {
      const hay = `${cid} ${familyName(fid)} ${(cdata.evidence?.title || '')} ${(cdata.findings || []).join(' ')}`.toLowerCase()
      if (!hay.includes(q)) return false
    }
    return true
  })

  // Group filtered controls by family
  const grouped = {}
  filtered.forEach(item => { (grouped[item.fid] = grouped[item.fid] || []).push(item) })

  const familyIds = Object.keys(families)

  return (
    <div className="view-pad">
      <div className="review-toolbar">
        <input className="search-input" placeholder="Search controls, findings…" value={filters.q}
          onChange={e => setFilters(f => ({ ...f, q: e.target.value }))} />
        <select value={filters.status} onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}>
          <option value="all">All statuses</option>
          <option value="fail">Needs attention</option>
          <option value="pass">Compliant</option>
        </select>
        <select value={filters.risk} onChange={e => setFilters(f => ({ ...f, risk: e.target.value }))}>
          <option value="all">All risk levels</option>
          <option value="high">High risk</option>
          <option value="medium">Medium risk</option>
          <option value="low">Low risk</option>
        </select>
        <select value={filters.family} onChange={e => setFilters(f => ({ ...f, family: e.target.value }))}>
          <option value="all">All families</option>
          {familyIds.map(fid => <option key={fid} value={fid}>{fid} · {familyName(fid)}</option>)}
        </select>
      </div>

      {filtered.length === 0 ? (
        <p className="empty-note">No controls match your filters.</p>
      ) : (
        Object.entries(grouped).map(([fid, items]) => (
          <section key={fid} className="family-block">
            <div className="family-block-head">
              <div>
                <span className="fb-id">{fid}</span>
                <span className="fb-name">{familyName(fid)}</span>
              </div>
              <span className="fb-blurb">{familyBlurb(fid)}</span>
            </div>
            {items.map(({ cid, cdata }) => (
              <ControlCard key={cid} fid={fid} controlId={cid} data={cdata} defaultOpen={cid === jumpControl} />
            ))}
          </section>
        ))
      )}
    </div>
  )
}

/* ════════════════════════════════════════════════════════════════════
   5. Report & Export
   ════════════════════════════════════════════════════════════════════ */

function ReportView({ report, poam, poamItems, files }) {
  const s = report?.summary || {}
  const meta = poam?.['plan-of-action-and-milestones']?.metadata || {}
  return (
    <div className="view-pad">
      <div className="report-actions no-print">
        <button className="primary-btn" onClick={() => window.print()}>Print / Save as PDF</button>
      </div>

      <div className="printable report-doc">
        <div className="report-doc-head">
          <h1>Compliance Assessment Report</h1>
          <div className="report-doc-meta">
            <div><span>System</span><strong>{report?.system_name || '—'}</strong></div>
            <div><span>Assessment date</span><strong>{(report?.assessment_date || '').slice(0, 10) || '—'}</strong></div>
            <div><span>Framework</span><strong>NIST SP 800-53 Rev 5</strong></div>
          </div>
        </div>

        <div className="report-summary-grid">
          <div><span className="rs-num">{s.total_controls ?? '—'}</span><span className="rs-cap">Controls assessed</span></div>
          <div><span className="rs-num ok">{s.passed ?? '—'}</span><span className="rs-cap">Compliant</span></div>
          <div><span className="rs-num bad">{s.failed ?? '—'}</span><span className="rs-cap">Need attention</span></div>
          <div><span className="rs-num">{(s.compliance_score ?? '—')}%</span><span className="rs-cap">Compliance score</span></div>
        </div>

        <h2 className="report-h2">Plan of Action &amp; Milestones</h2>
        <p className="report-sub no-print">OSCAL {poam?.oscal_version || '—'} · {poamItems.length} items · last modified {meta['last-modified'] || '—'}</p>
        {poamItems.length === 0 ? (
          <p className="empty-note">No open items. The system meets all assessed controls.</p>
        ) : (
          <table className="report-table">
            <thead>
              <tr><th>Item</th><th>Control</th><th>Family</th><th>Risk</th><th>Weakness</th></tr>
            </thead>
            <tbody>
              {poamItems.map(it => (
                <tr key={it.item_id}>
                  <td className="mono">{it.item_id}</td>
                  <td className="mono">{it.control_id}</td>
                  <td>{familyName(it.family_id)}</td>
                  <td><span className={`risk-pill risk-${riskKey(it.risk_level)}`}>{String(it.risk_level).toUpperCase()}</span></td>
                  <td>{it.weakness}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <section className="panel no-print" style={{ marginTop: '1.5rem' }}>
        <h3 className="panel-title">Downloadable artifacts</h3>
        {files.length === 0 ? (
          <p className="empty-note">No artifacts generated yet.</p>
        ) : (
          <div className="artifact-list">
            {files.map(f => (
              <a key={f} href={`/api/artifacts/${f}`} target="_blank" rel="noreferrer" className="artifact-row">
                <span className="artifact-ext">{f.split('.').pop().toUpperCase()}</span>
                <span className="artifact-label">{artifactLabel(f)}</span>
                <span className="artifact-file">{f}</span>
                <span className="artifact-dl">Download ↓</span>
              </a>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

/* ════════════════════════════════════════════════════════════════════
   Main App
   ════════════════════════════════════════════════════════════════════ */

export default function App() {
  const [phase, setPhase] = useState('setup')          // setup | running | results
  const [view, setView] = useState('overview')         // overview | review | report

  // config
  const [systemName, setSystemName] = useState('')
  const [infraSource, setInfraSource] = useState('live')
  const [infraFile, setInfraFile] = useState(null)
  const [configS3Bucket, setConfigS3Bucket] = useState('')
  const [configS3Prefix, setConfigS3Prefix] = useState('')
  const [cfnStacks, setCfnStacks] = useState('')
  const [contextFile, setContextFile] = useState(null)
  const [advanced, setAdvanced] = useState(false)
  const [awsProfile, setAwsProfile] = useState('')
  const [awsRegion, setAwsRegion] = useState('us-east-1')
  const [awsAccessKeyId, setAwsAccessKeyId] = useState('')
  const [awsSecretAccessKey, setAwsSecretAccessKey] = useState('')
  const [showSecret, setShowSecret] = useState(false)
  const [llmProvider, setLlmProvider] = useState('bedrock')
  const [llmModel, setLlmModel] = useState('')
  const [llmBaseUrl, setLlmBaseUrl] = useState('')
  const [llmApiKey, setLlmApiKey] = useState('')
  const [showLlmKey, setShowLlmKey] = useState(false)
  const [applySuggestions, setApplySuggestions] = useState(false)
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.9)

  // run + data
  const [running, setRunning] = useState(false)
  const [log, setLog] = useState('')
  const [elapsed, setElapsed] = useState(0)
  const [report, setReport] = useState(null)
  const [poam, setPoam] = useState(null)
  const [files, setFiles] = useState([])

  // review jump
  const [filters, setFilters] = useState({ q: '', status: 'all', risk: 'all', family: 'all' })
  const [jumpControl, setJumpControl] = useState(null)

  /* Restore saved settings */
  useEffect(() => {
    try {
      const c = JSON.parse(localStorage.getItem('bobbie_aws_creds') || 'null')
      if (c) { if (c.awsProfile) setAwsProfile(c.awsProfile); if (c.awsRegion) setAwsRegion(c.awsRegion); if (c.awsAccessKeyId) setAwsAccessKeyId(c.awsAccessKeyId) }
    } catch {}
    try {
      const c = JSON.parse(localStorage.getItem('bobbie_llm_settings') || 'null')
      if (c) { if (c.llmProvider) setLlmProvider(c.llmProvider); if (c.llmModel) setLlmModel(c.llmModel); if (c.llmBaseUrl) setLlmBaseUrl(c.llmBaseUrl) }
    } catch {}
  }, [])

  /* Elapsed timer while running */
  useEffect(() => {
    if (phase !== 'running') return
    setElapsed(0)
    const iv = setInterval(() => setElapsed(e => e + 1), 1000)
    return () => clearInterval(iv)
  }, [phase])

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

  async function uploadFile(file) {
    const fd = new FormData(); fd.append('file', file)
    const r = await fetch('/api/upload', { method: 'POST', body: fd })
    if (!r.ok) throw new Error('upload failed')
    return (await r.json()).filename
  }
  async function handleUpload(e) {
    if (!e.target.files?.[0]) return
    try { setContextFile(await uploadFile(e.target.files[0])) } catch { alert('Upload failed') }
  }
  async function handleInfraUpload(e) {
    if (!e.target.files?.[0]) return
    try { setInfraFile(await uploadFile(e.target.files[0])) } catch { alert('Upload failed') }
  }

  function persistSettings() {
    try { localStorage.setItem('bobbie_aws_creds', JSON.stringify({ awsProfile, awsRegion, awsAccessKeyId })) } catch {}
    try { localStorage.setItem('bobbie_llm_settings', JSON.stringify({ llmProvider, llmModel, llmBaseUrl })) } catch {}
  }

  async function runAssessment() {
    persistSettings()
    setRunning(true)
    setLog('')
    setPhase('running')
    const payload = {
      systemName: systemName.trim() || undefined,
      applySuggestions,
      confidenceThreshold: parseFloat(confidenceThreshold),
      infraSource,
      llmProvider,
      llmModel: llmModel.trim() || undefined,
      llmBaseUrl: llmBaseUrl.trim() || undefined,
      llmApiKey: llmApiKey.trim() || undefined,
    }
    if (infraSource !== 'live') {
      if (infraFile) payload.infraFile = infraFile
      if (infraSource === 'aws-config') { if (configS3Bucket) payload.configS3Bucket = configS3Bucket; if (configS3Prefix) payload.configS3Prefix = configS3Prefix }
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
    } catch (e) { console.error(e); setRunning(false); setPhase('setup') }
  }

  function pollLog() {
    const iv = setInterval(async () => {
      try {
        const j = await fetch('/api/log').then(r => r.json())
        setLog(j.log || '')
        if ((j.log || '').includes('Process exited')) {
          clearInterval(iv)
          setRunning(false)
          await fetchAll()
          setView('overview')
          setPhase('results')
        }
      } catch (e) { console.error(e) }
    }, 1500)
  }

  function jumpToControl(controlId, familyId) {
    setFilters({ q: '', status: 'all', risk: 'all', family: familyId || 'all' })
    setJumpControl(controlId || null)
    setView('review')
    if (controlId) {
      setTimeout(() => {
        const el = document.getElementById(`ctl-${controlId}`)
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }, 60)
    }
  }

  const poamItems = poam?.['plan-of-action-and-milestones']?.['poam-items'] || []
  const hasResults = !!report
  const providerLabel = llmProvider === 'bedrock' ? 'AWS Bedrock' : (llmBaseUrl ? 'Custom model endpoint' : 'OpenAI')

  return (
    <div className="app">
      <div className="gov-banner">
        <span className="flag">🛡️</span>
        Official U.S. Government compliance assessment tool · NIST SP 800-53 Rev 5
      </div>

      <header className="app-header">
        <div className="header-left">
          <div className="brand-shield">B</div>
          <div>
            <div className="brand-name">B.O.B.B.I.E.</div>
            <div className="brand-desc">Baseline &amp; Behavior Intelligence Engine</div>
          </div>
        </div>
        <div className="header-right">
          {phase === 'results' && (
            <nav className="app-nav">
              {[['overview', 'Overview'], ['review', 'Review controls'], ['report', 'Report']].map(([id, label]) => (
                <button key={id} className={view === id ? 'active' : ''} onClick={() => setView(id)}>{label}</button>
              ))}
            </nav>
          )}
          {phase === 'results' && <button className="ghost-btn sm" onClick={() => setPhase('setup')}>New assessment</button>}
          <span className="provider-chip">{providerLabel}</span>
        </div>
      </header>

      <main className="app-main">
        {phase === 'setup' && (
          <StartScreen
            running={running} hasResults={hasResults}
            onViewResults={() => { setView('overview'); setPhase('results') }}
            onRun={runAssessment}
            systemName={systemName} setSystemName={setSystemName}
            infraSource={infraSource} setInfraSource={setInfraSource}
            infraFile={infraFile} handleInfraUpload={handleInfraUpload}
            configS3Bucket={configS3Bucket} setConfigS3Bucket={setConfigS3Bucket}
            configS3Prefix={configS3Prefix} setConfigS3Prefix={setConfigS3Prefix}
            cfnStacks={cfnStacks} setCfnStacks={setCfnStacks}
            contextFile={contextFile} setContextFile={setContextFile} handleUpload={handleUpload}
            advanced={advanced} setAdvanced={setAdvanced}
            awsProfile={awsProfile} setAwsProfile={setAwsProfile}
            awsRegion={awsRegion} setAwsRegion={setAwsRegion}
            awsAccessKeyId={awsAccessKeyId} setAwsAccessKeyId={setAwsAccessKeyId}
            awsSecretAccessKey={awsSecretAccessKey} setAwsSecretAccessKey={setAwsSecretAccessKey}
            showSecret={showSecret} setShowSecret={setShowSecret}
            llmProvider={llmProvider} setLlmProvider={setLlmProvider}
            llmModel={llmModel} setLlmModel={setLlmModel}
            llmBaseUrl={llmBaseUrl} setLlmBaseUrl={setLlmBaseUrl}
            llmApiKey={llmApiKey} setLlmApiKey={setLlmApiKey}
            showLlmKey={showLlmKey} setShowLlmKey={setShowLlmKey}
            applySuggestions={applySuggestions} setApplySuggestions={setApplySuggestions}
            confidenceThreshold={confidenceThreshold} setConfidenceThreshold={setConfidenceThreshold}
          />
        )}

        {phase === 'running' && <ProgressView log={log} elapsed={elapsed} />}

        {phase === 'results' && view === 'overview' && <Overview report={report} poamItems={poamItems} onJump={jumpToControl} />}
        {phase === 'results' && view === 'review' && <Review report={report} filters={filters} setFilters={setFilters} jumpControl={jumpControl} />}
        {phase === 'results' && view === 'report' && <ReportView report={report} poam={poam} poamItems={poamItems} files={files} />}
      </main>
    </div>
  )
}
