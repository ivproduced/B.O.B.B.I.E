/* ════════════════════════════════════════════════════════════════════
   B.O.B.B.I.E. — shared constants & helpers
   ════════════════════════════════════════════════════════════════════ */

/* NIST SP 800-53 Rev 5 control families — name + plain-language purpose. */
export const FAMILIES = {
  AC: { name: 'Access Control', blurb: 'Who can get into the system and what they are allowed to do.' },
  AT: { name: 'Awareness and Training', blurb: 'Making sure staff are trained on security responsibilities.' },
  AU: { name: 'Audit and Accountability', blurb: 'Recording activity so actions can be traced and reviewed.' },
  CA: { name: 'Assessment, Authorization, and Monitoring', blurb: 'Ongoing checks that security controls work as intended.' },
  CM: { name: 'Configuration Management', blurb: 'Keeping track of system components and approved settings.' },
  CP: { name: 'Contingency Planning', blurb: 'Being ready to recover if the system is disrupted.' },
  IA: { name: 'Identification and Authentication', blurb: 'Confirming users and devices are who they claim to be.' },
  IR: { name: 'Incident Response', blurb: 'Detecting, reporting, and responding to security incidents.' },
  MA: { name: 'Maintenance', blurb: 'Performing system maintenance safely and securely.' },
  MP: { name: 'Media Protection', blurb: 'Protecting information stored on physical and digital media.' },
  PE: { name: 'Physical and Environmental Protection', blurb: 'Securing the physical spaces that house the system.' },
  PL: { name: 'Planning', blurb: 'Documenting how the system will be secured.' },
  PM: { name: 'Program Management', blurb: 'Organization-wide management of the security program.' },
  PS: { name: 'Personnel Security', blurb: 'Managing security risks tied to people and their roles.' },
  PT: { name: 'PII Processing and Transparency', blurb: 'Handling personal information responsibly and openly.' },
  RA: { name: 'Risk Assessment', blurb: 'Identifying and rating risks to the system.' },
  SA: { name: 'System and Services Acquisition', blurb: 'Building security into what the organization buys and builds.' },
  SC: { name: 'System and Communications Protection', blurb: 'Protecting data as it moves and is stored.' },
  SI: { name: 'System and Information Integrity', blurb: 'Keeping the system and its data accurate and free of threats.' },
  SR: { name: 'Supply Chain Risk Management', blurb: 'Managing risks from suppliers and third parties.' },
}

export function familyName(id) {
  return FAMILIES[id]?.name || id
}
export function familyBlurb(id) {
  return FAMILIES[id]?.blurb || ''
}

/* Plain-language status mapping. */
export function statusInfo(status) {
  const s = (status || '').toUpperCase()
  if (s === 'PASS') return { key: 'pass', label: 'Compliant' }
  if (s === 'FAIL') return { key: 'fail', label: 'Needs attention' }
  return { key: 'unknown', label: 'Not assessed' }
}

export function riskKey(level) {
  const l = (level || '').toUpperCase()
  if (l === 'HIGH' || l === 'CRITICAL') return 'high'
  if (l === 'MEDIUM' || l === 'MODERATE') return 'medium'
  if (l === 'LOW') return 'low'
  return 'none'
}

/* Overall readiness verdict derived from compliance score. */
export function readiness(score) {
  const s = Number(score) || 0
  if (s >= 90) return { key: 'strong',  title: 'Strong compliance posture',
    blurb: 'Most assessed controls are satisfied. Address the remaining items to maintain readiness.' }
  if (s >= 70) return { key: 'moderate', title: 'Moderate compliance posture',
    blurb: 'A solid foundation is in place, but several controls need attention before authorization.' }
  if (s >= 50) return { key: 'limited', title: 'Limited compliance posture',
    blurb: 'Significant gaps remain. Prioritize the high-risk findings below.' }
  return { key: 'early', title: 'Early compliance posture',
    blurb: 'Major remediation is needed across multiple control families.' }
}

/* Friendly labels for known artifact filenames. */
export function artifactLabel(filename) {
  const map = {
    'assessment_report.json': 'Full assessment report (machine-readable)',
    'assessment_summary.txt': 'Plain-text summary',
    'poam.json': 'Plan of Action & Milestones (OSCAL)',
    'infra_snapshot.json': 'Infrastructure snapshot',
    'web_run.log': 'Technical run log',
  }
  return map[filename] || filename
}

/* Turn a raw run log into a short, friendly status line. */
export function progressHint(log) {
  if (!log) return 'Starting up…'
  const lines = log.split('\n').map(l => l.trim()).filter(Boolean)
  for (let i = lines.length - 1; i >= 0; i--) {
    const l = lines[i]
    if (l.includes('Process exited')) return 'Finishing up…'
    if (/snapshot/i.test(l) && /saved/i.test(l)) return 'Reviewing system configuration…'
    if (/infrastructure source/i.test(l)) return 'Gathering system information…'
    if (/\bsnapshot\b/i.test(l)) return 'Gathering system information…'
    if (/assess|control|family/i.test(l)) return 'Evaluating security controls…'
  }
  return 'Working…'
}
