require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');

const authRoutes = require('./routes/auth');
const researchRoutes = require('./routes/research');
const reportsRoutes = require('./routes/reports');
const watchlistRoutes = require('./routes/watchlist');

const app = express();

app.use(cors());
app.use(express.json());

app.use('/api/auth', authRoutes);
app.use('/api/research', researchRoutes);
app.use('/api/reports', reportsRoutes);
app.use('/api/watchlist', watchlistRoutes);

// Health check endpoint (for Render free-tier cold-starts)
app.get('/api/health', async (req, res) => {
  try {
    const pythonApi = process.env.PYTHON_API_URL || 'http://127.0.0.1:8000';
    // Ping Python backend to wake it up
    await fetch(`${pythonApi}/health`);
  } catch (err) {
    // Ignore error, python might be booting
  }
  res.json({ status: 'ok' });
});

const PORT = process.env.PORT || 3000;
let MONGO_URI = process.env.MONGO_URI;

const startServer = async () => {
  if (!MONGO_URI) {
    console.log('No MONGO_URI provided. Starting mongodb-memory-server...');
    const { MongoMemoryServer } = require('mongodb-memory-server');
    const mongod = await MongoMemoryServer.create();
    MONGO_URI = mongod.getUri();
  }

  mongoose.connect(MONGO_URI)
    .then(() => {
      console.log(`Connected to MongoDB at ${MONGO_URI}`);
      app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
    })
    .catch(err => console.error('MongoDB connection error:', err));
};

startServer();
