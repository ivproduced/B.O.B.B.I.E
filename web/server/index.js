const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const multer = require('multer');
const rateLimit = require('express-rate-limit');

const app = express();
app.use(cors());
app.use(express.json());

// General read endpoints: 120 requests per 15-minute fixed window per IP
const readLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 120,
  standardHeaders: true,
  legacyHeaders: false,
});

// File upload: 30 requests per 15-minute fixed window per IP
const uploadLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 30,
  standardHeaders: true,
  legacyHeaders: false,
});

// Assessment run: 10 requests per 15-minute fixed window per IP (spawns a process)
const runLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
});

const UPLOADS_DIR = path.resolve(__dirname, '../../data/uploads');
const ARTIFACTS_DIR = path.resolve(__dirname, '../../artifacts/final_run');
const RUN_LOG = path.join(ARTIFACTS_DIR, 'web_run.log');

function resolvePathInUploads(userProvidedPath) {
  if (typeof userProvidedPath !== 'string' || userProvidedPath.trim() === '') {
    return null;
  }

  // Reject inputs containing path separators or null bytes before any path operation
  if (userProvidedPath.includes('/') || userProvidedPath.includes('\\') || userProvidedPath.includes('\0')) {
    return null;
  }

  // Extract the bare filename — strips any remaining directory components
  const safeName = path.basename(userProvidedPath);
  if (!safeName || safeName === '.' || safeName === '..') {
    return null;
  }

  return path.join(UPLOADS_DIR, safeName);
}

// Configure multer storage
const upload = multer({ 
  storage: multer.diskStorage({
    destination: (req, file, cb) => {
      if (!fs.existsSync(UPLOADS_DIR)) {
        fs.mkdirSync(UPLOADS_DIR, { recursive: true });
      }
      cb(null, UPLOADS_DIR);
    },
    filename: (req, file, cb) => {
      cb(null, path.basename(file.originalname));
    }
  })
});

app.post('/api/upload', uploadLimiter, upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }
  res.json({ filename: req.file.filename });
});

app.get('/api/artifacts', readLimiter, (req, res) => {
  fs.readdir(ARTIFACTS_DIR, (err, files) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ files });
  });
});

app.get('/api/artifacts/:name', readLimiter, (req, res) => {
  const rawName = req.params.name;
  const safeName = path.basename(rawName);

  // Reject traversal/path-component input; only allow simple filenames
  if (!safeName || safeName !== rawName || safeName === '.' || safeName === '..') {
    return res.status(400).json({ error: 'invalid artifact name' });
  }

  const filePath = path.resolve(ARTIFACTS_DIR, safeName);
  const relativePath = path.relative(ARTIFACTS_DIR, filePath);
  if (relativePath.startsWith('..') || path.isAbsolute(relativePath)) {
    return res.status(403).json({ error: 'forbidden' });
  }
  if (!fs.existsSync(filePath)) return res.status(404).json({ error: 'not found' });
  res.sendFile(filePath);
});

app.post('/api/run', runLimiter, (req, res) => {
  // spawn the Python assessment using the project virtualenv
  const pythonPath = path.resolve(__dirname, '../../.venv/bin/python');
  if (!fs.existsSync(pythonPath)) {
    return res.status(500).json({ error: 'Python executable not found at .venv/bin/python' });
  }

  // ensure artifacts dir exists
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
  const out = fs.createWriteStream(RUN_LOG, { flags: 'a' });

  const args = [
    'run_assessment.py',
    '--deterministic',
    '--nova-narrative',
    '--output-dir', 'artifacts/final_run',
    '--system-name', 'BOBBIE Web Run'
  ];

  const {
    applySuggestions,
    confidenceThreshold,
    contextFile,
    infraSource,
    infraFile,
    configS3Bucket,
    configS3Prefix,
    cfnStacks,
    awsProfile,
    awsRegion,
    awsAccessKeyId,
    awsSecretAccessKey,
    collectOnly,
  } = req.body;

  if (applySuggestions) {
    args.push('--apply-nova-suggestions');
  }

  if (typeof confidenceThreshold === 'number') {
    args.push('--nova-confidence-threshold', String(confidenceThreshold));
  }

  if (contextFile) {
    if (!resolvePathInUploads(contextFile)) {
      return res.status(400).json({ error: 'Invalid context file path' });
    }
    // Re-derive from fixed base + sanitized basename to break the taint chain
    const safeContextPath = path.join(UPLOADS_DIR, path.basename(contextFile));
    if (!fs.existsSync(safeContextPath)) {
        return res.status(400).json({ error: `Context file not found: ${contextFile}` });
    }
    args.push('--context-file', safeContextPath);
  }

  // Infrastructure source options
  if (infraSource && infraSource !== 'live') {
    args.push('--infra-source', infraSource);
  }

  if (infraFile) {
    if (!resolvePathInUploads(infraFile)) {
      return res.status(400).json({ error: 'Invalid infrastructure file path' });
    }
    // Re-derive from fixed base + sanitized basename to break the taint chain
    const safeInfraPath = path.join(UPLOADS_DIR, path.basename(infraFile));
    if (!fs.existsSync(safeInfraPath)) {
      return res.status(400).json({ error: `Infrastructure file not found: ${infraFile}` });
    }
    args.push('--infra-file', safeInfraPath);
  }

  if (configS3Bucket) {
    args.push('--config-s3-bucket', configS3Bucket);
  }

  if (configS3Prefix) {
    args.push('--config-s3-prefix', configS3Prefix);
  }

  if (cfnStacks) {
    args.push('--cfn-stacks', cfnStacks);
  }

  if (awsProfile) {
    args.push('--aws-profile', awsProfile);
  }

  if (awsRegion) {
    args.push('--aws-region', awsRegion);
  }

  if (collectOnly) {
    args.push('--collect-only');
  }

  const proc = spawn(pythonPath, args, {
    env: Object.assign({}, process.env, {
      AWS_PROFILE: awsProfile || process.env.AWS_PROFILE || 'bobbie',
      AWS_REGION: awsRegion || process.env.AWS_REGION || 'us-east-1',
      AWS_DEFAULT_REGION: awsRegion || process.env.AWS_DEFAULT_REGION || 'us-east-1',
      ...(awsAccessKeyId ? { AWS_ACCESS_KEY_ID: awsAccessKeyId } : {}),
      ...(awsSecretAccessKey ? { AWS_SECRET_ACCESS_KEY: awsSecretAccessKey } : {}),
    }),
    cwd: path.resolve(__dirname, '../..')
  });

  proc.stdout.on('data', (data) => {
    out.write(data);
  });
  proc.stderr.on('data', (data) => {
    out.write(data);
  });
  proc.on('close', (code) => {
    out.write(`\nProcess exited with ${code}\n`);
    out.end();
  });

  res.json({ pid: proc.pid, log: '/api/artifacts/web_run.log' });
});

app.get('/api/log', readLimiter, (req, res) => {
  if (!fs.existsSync(RUN_LOG)) return res.json({ log: '' });
  const data = fs.readFileSync(RUN_LOG, 'utf8');
  res.json({ log: data });
});

app.get('/api/report', readLimiter, (req, res) => {
  const reportPath = path.join(ARTIFACTS_DIR, 'assessment_report.json');
  if (!fs.existsSync(reportPath)) return res.json(null);
  try {
    const data = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    res.json(data);
  } catch (e) {
    res.status(500).json({ error: 'Failed to parse report' });
  }
});

app.get('/api/poam', readLimiter, (req, res) => {
  const poamPath = path.join(ARTIFACTS_DIR, 'poam.json');
  if (!fs.existsSync(poamPath)) return res.json(null);
  try {
    const data = JSON.parse(fs.readFileSync(poamPath, 'utf8'));
    res.json(data);
  } catch (e) {
    res.status(500).json({ error: 'Failed to parse poam' });
  }
});

const port = process.env.PORT || 3001;
app.listen(port, () => console.log(`Bobbie web server listening on ${port}`));
