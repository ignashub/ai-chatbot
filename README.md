# Health & Wellness AI Chatbot

A specialized AI chatbot application focused on health and wellness topics, built with Next.js frontend and Python Flask backend.

## Project Overview

This project implements an AI-powered chatbot that provides:

- Personalized health and wellness guidance
- Access to a knowledge base of health documents
- Ability to set reminders for health activities
- Nutrition information for food items
- Customizable AI parameters for different response styles

The application uses OpenAI's GPT models via LangChain, with a Next.js frontend and Flask backend architecture.

## Repository Structure

- **`/frontend`**: Next.js application with React components
- **`/backend`**: Python Flask server with LangChain integration

## Getting Started

For detailed setup instructions, please refer to:
- [Frontend README](/frontend/README.md) - Contains Next.js setup instructions
- Backend README - Contains Flask server setup instructions

### Quick Start

1. Clone the repository
2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   # Create .env with OPENAI_API_KEY
   python app.py
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   # Create .env.local with NEXT_PUBLIC_API_URL=http://127.0.0.1:5000
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Recommended Documents

For optimal performance with the knowledge base, download and upload these documents:

- [Introduction to Public Health (CDC)](https://www.cdc.gov/training-publichealth101/media/pdfs/introduction-to-public-health.pdf)
- [Concept of Health (Rai, 2016)](https://www.gfmer.ch/GFMER_members/pdf/Concept-health-Rai-2016.pdf)

## Features Implemented

- ✅ OpenAI API integration via LangChain
- ✅ Customizable AI parameters (temperature, top-p, frequency, etc.)
- ✅ Security guards to prevent misuse
- ✅ RAG functionality with document knowledge base
- ✅ Function calling for reminders and nutrition information
- ✅ Export conversations in multiple formats
- ✅ Interactive help feature
- ✅ Cost calculation for API usage

## Technologies Used

- **Frontend**: Next.js, React, TypeScript, TailwindCSS, PrimeReact
- **Backend**: Python, Flask, LangChain, OpenAI API
- **Data Storage**: Vector database for document embeddings

## License

This project is created for educational purposes as part of the Turing College curriculum. 