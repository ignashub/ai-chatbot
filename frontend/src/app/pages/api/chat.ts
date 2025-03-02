import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    try {
      const { message } = req.body;
      const response = await axios.post('http://localhost:5000/chat', { message });
      res.status(200).json({ response: response.data.response });
    } catch (error) {
      res.status(500).json({ error: 'Error communicating with the chatbot' });
    }
  } else {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}