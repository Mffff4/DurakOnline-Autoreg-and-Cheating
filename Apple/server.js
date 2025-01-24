const express = require('express');
const apple = require('./utils/apple_auth.js');

const app = express();
const port = 3000;
const hostname = 'localhost'

app.use(express.json());

app.post('/get_encrypted_a', (req, res) => {
  const postData = req.body;
  const encrypted_a = apple.get_encrypted_a(postData.email);
  res.json({ result: encrypted_a });
});

app.post('/get_complete_data', async (req, res) => {
  const postData = req.body;
  const complete_data = await apple.get_complete_data(postData.s);
  res.json({result: complete_data});
});

app.listen(port, hostname, () => {
  console.log(`Сервер запущен на http://${hostname}:${port}`);
});