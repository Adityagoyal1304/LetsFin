const express = require('express');
const Watchlist = require('../models/Watchlist');
const auth = require('../middleware/auth');

const router = express.Router();

router.get('/', auth, async (req, res) => {
  try {
    let watchlist = await Watchlist.findOne({ userId: req.userId });
    if (!watchlist) {
      watchlist = new Watchlist({ userId: req.userId, tickers: [] });
      await watchlist.save();
    }
    res.json(watchlist);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.post('/', auth, async (req, res) => {
  try {
    const { tickers } = req.body;
    let watchlist = await Watchlist.findOne({ userId: req.userId });
    if (!watchlist) {
      watchlist = new Watchlist({ userId: req.userId, tickers: [] });
    }
    watchlist.tickers = tickers;
    await watchlist.save();
    res.json(watchlist);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
