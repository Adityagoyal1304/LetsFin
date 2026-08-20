const express = require('express');
const Report = require('../models/Report');
const auth = require('../middleware/auth');

const router = express.Router();

router.get('/', auth, async (req, res) => {
  try {
    const reports = await Report.find({ userId: req.userId }).sort({ createdAt: -1 });
    res.json(reports);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get('/:id', auth, async (req, res) => {
  try {
    const report = await Report.findOne({ _id: req.params.id, userId: req.userId });
    if (!report) return res.status(404).json({ error: 'Report not found' });
    res.json(report);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
