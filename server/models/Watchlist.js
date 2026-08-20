const mongoose = require('mongoose');

const watchlistSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    unique: true
  },
  tickers: {
    type: [String],
    default: []
  }
});

module.exports = mongoose.model('Watchlist', watchlistSchema);
