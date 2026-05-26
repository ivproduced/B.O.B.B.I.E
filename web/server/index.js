const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const multer = require('multer');

const app = express();
app.use(cors());
app.use(express.json());

const UPLOADS_DIR = path.resolve(__dirname, '../../data/uploads');
const ARTIFACTS_DIR = path.resolve(__dirname, '../../artifacts/final_run');
const RUN_LOG = path.join(ARTIFACTS_DIR, 'web_run.log');

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
      cb(null, file.originalname);
    }
  })
});

app.post('/api/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }
  res.json({ filename: req.file.filename });
});

app.get('/api/artifacts', (req, res) => {
  fs.readdir(ARTIFACTS_DIR, (err, files) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ files });
  });
});

app.get('/api/artifacts/:name', (req, res) => {
  const rawName = req.params.name;
  const safeName = path.basename(rawName);

  // Reject traversal/path-component input; only allow simple filenames
  if (!safeName || safeName !== rawName || safeName === '.' || safeName === '..') {
    return res.status(400).json({ error: 'invalid artifact name' });
  }

  const filePath = path.join(ARTIFACTS_DIR, safeName);
  if (!fs.existsSync(filePath)) return res.status(404).json({ error: 'not found' });
  res.sendFile(filePath);
});

app.post('/api/run', (req, res) => {
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
    const uploadsBase = UPLOADS_DIR.endsWith(path.sep) ? UPLOADS_DIR : UPLOADS_DIR + path.sep;
    const contextPath = path.resolve(UPLOADS_DIR, contextFile);
    if (!contextPath.startsWith(uploadsBase)) {
      return res.status(400).json({ error: 'Invalid context file path' });
    }
    if (!fs.existsSync(contextPath)) {
        return res.status(400).json({ error: `Context file not found: ${contextFile}` });
    }
    args.push('--context-file', contextPath);
  }

  // Infrastructure source options
  if (infraSource && infraSource !== 'live') {
    args.push('--infra-source', infraSource);
  }

  if (infraFile) {
    const infraPath = path.join(UPLOADS_DIR, infraFile);
    if (!fs.existsSync(infraPath)) {
      return res.status(400).json({ error: `Infrastructure file not found: ${infraFile}` });
    }
    args.push('--infra-file', infraPath);
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

app.get('/api/log', (req, res) => {
  if (!fs.existsSync(RUN_LOG)) return res.json({ log: '' });
  const data = fs.readFileSync(RUN_LOG, 'utf8');
  res.json({ log: data });
});

app.get('/api/report', (req, res) => {
  const reportPath = path.join(ARTIFACTS_DIR, 'assessment_report.json');
  if (!fs.existsSync(reportPath)) return res.json(null);
  try {
    const data = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    res.json(data);
  } catch (e) {
    res.status(500).json({ error: 'Failed to parse report' });
  }
});

app.get('/api/poam', (req, res) => {
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
