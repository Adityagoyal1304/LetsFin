const mongoose = require('mongoose');

const reportSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  ticker: {
    type: String,
    required: true
  },
  question: {
    type: String,
    required: true
  },
  threadId: {
    type: String,
    required: true,
    unique: true
  },
  status: {
    type: String,
    enum: ['running', 'awaiting_approval', 'complete', 'failed'],
    default: 'running'
  },
  memo: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  evidence: {
    type: Array,
    default: []
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  completedAt: {
    type: Date
  }
});

module.exports = mongoose.model('Report', reportSchema);
