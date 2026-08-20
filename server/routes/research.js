const express = require('express');
const { v4: uuidv4 } = require('uuid');
const fetch = require('node-fetch');
const Report = require('../models/Report');
const auth = require('../middleware/auth');

const router = express.Router();
const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

async function relayStream(pythonResponse, expressResponse, report) {
  // Requirement 1: No buffering, set headers
  expressResponse.setHeader('Content-Type', 'text/event-stream');
  expressResponse.setHeader('Cache-Control', 'no-cache');
  expressResponse.setHeader('Connection', 'keep-alive');
  expressResponse.flushHeaders();

  let browserConnected = true;
  expressResponse.on('close', () => {
    browserConnected = false;
    // Requirement 3: Do not abort the python stream! Let it run to completion.
  });

  const decoder = new TextDecoder();
  let buffer = '';

  // node-fetch response.body is a Node Readable stream
  pythonResponse.body.on('data', async (chunk) => {
    if (browserConnected) {
      expressResponse.write(chunk);
    }
    
    // Parse the stream to update the DB on interrupt/final
    buffer += decoder.decode(chunk, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop() || '';

    for (const part of parts) {
      if (part.startsWith('data: ')) {
        try {
          const data = JSON.parse(part.slice(6));
          if (data.type === 'interrupt') {
            report.status = 'awaiting_approval';
            report.memo = typeof data.draft === 'string' ? JSON.parse(data.draft || '{}') : data.draft;
            await report.save();
          } else if (data.type === 'final') {
            report.status = 'complete';
            report.memo = typeof data.memo === 'string' ? JSON.parse(data.memo || '{}') : data.memo;
            report.completedAt = new Date();
            await report.save();
          } else if (data.type === 'error') {
            report.status = 'failed';
            await report.save();
          }
        } catch (err) {
          // Ignore JSON parse errors for incomplete chunks
        }
      }
    }
  });

  pythonResponse.body.on('end', () => {
    if (browserConnected) {
      expressResponse.end();
    }
  });
  
  pythonResponse.body.on('error', (err) => {
    if (browserConnected) {
      expressResponse.end();
    }
  });
}

router.post('/', auth, async (req, res) => {
  try {
    const { ticker, question } = req.body;
    
    // Requirement 2: Express generates threadId and saves it. Client never sets it.
    const threadId = uuidv4();
    
    const report = new Report({
      userId: req.userId,
      ticker,
      question,
      threadId,
      status: 'running'
    });
    await report.save();

    const pythonRes = await fetch(`${PYTHON_API_URL}/research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker, question, thread_id: threadId })
    });

    await relayStream(pythonRes, res, report);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.post('/:id/approve', auth, async (req, res) => {
  try {
    const { decision } = req.body;
    const report = await Report.findOne({ _id: req.params.id, userId: req.userId });
    
    if (!report) return res.status(404).json({ error: 'Report not found' });
    if (report.status !== 'awaiting_approval') {
      return res.status(400).json({ error: 'Report is not awaiting approval' });
    }

    report.status = 'running';
    await report.save();

    const pythonRes = await fetch(`${PYTHON_API_URL}/resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: report.threadId, decision })
    });

    await relayStream(pythonRes, res, report);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
