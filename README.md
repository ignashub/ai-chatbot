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

### Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- OpenAI API Key

### Setup and Installation

1. **Clone the repository**

```bash
git clone https://github.com/ignashub/ai-chatbot.git
cd ai-chatbot
```

2. **Backend Setup**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Create a `.env` file in the backend directory with your OpenAI API key**

```
OPENAI_API_KEY=your_api_key_here
```

4. **Start the backend server**

```bash
python app.py
```

5. **Frontend Setup**

```bash
cd ../frontend
npm install
```

6. **Create a `.env.local` file in the frontend directory**

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:5000
```

7. **Start the frontend development server**

```bash
npm run dev
```

8. **Open [http://localhost:3000](http://localhost:3000) with your browser to see the application**

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