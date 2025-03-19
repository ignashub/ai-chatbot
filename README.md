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

## Task Requirements

The exact task requirements are as follows:

Figure out how your chatbot will work.
Create an OpenAI API Key for this project.
Use the available components from StreamLit or Next.js ecosystem, or write your own components. If you want to use Python and Next.js at the same time (harder) or other JS frontend frameworks, please do, but understand that this will take more time.
Tune at least one OpenAI setting (temperature, Top-p, frequency, etc).
Add at least one security guard to your app to prevent misuse, like users trying to jailbreak your app or writing biased prompts. Be creative!
Use LangChain for calling the OpenAI API.
The user should be able to send messages to the bot and get replies.
Optional Tasks
After the main functionality is implemented and your code works correctly, and you feel that you want to upgrade your project, choose one or more improvements from this list. The list is sorted by difficulty levels.

Caution: Some of the tasks in medium or hard categories may contain tasks with concepts or libraries that may be introduced in later sections or even require outside knowledge/time to research outside of the course.

## Easy:

Ask ChatGPT to critique your solution from the usability, security, and prompt-engineering sides.
Improve the chatbot to be more specialized for your specific domain: IT, HR, marketing, finance, etc.
Add a separate text field for the system prompt.
Implement more security constraints, like user input validation and system prompt validation. Could we consider utilizing ChatGPT to verify these aspects?
Add an interactive help feature or chatbot guide explaining how to use the app.

## Medium:

Add all of the OpenAI settings (models, temperature, frequency, etc.) for the user to tune as sliders/fields.
Deploy your app to the Internet.
Calculate and provide output to the user on the price of the prompt.
Read OpenAI API documentation, think of your own improvement, and implement it.
Implement function calling function calling, like a calculator, a map renderer, currency converter, etc.
Try to jailbreak (break into) your own application. Provide the results of this experiment in an Excel sheet.
Add RAG functionality to the app: adding a knowledge base, retrieving when a similar is found, and sending it to ChatGPT.
Provide the user with the ability to choose from a list of LLMs (Gemini, OpenAI, etc.) for this project.
Think of a creative way; how could you use image generation inside this project and implement it using code?
Allow users to download conversations or generated data in formats like PDF, CSV, or JSON.

## Hard:

Using Streamlit (Python) or React (JS) components, implement a full-fledged chatbot application instead of a one-time call to the OpenAI API.
Deploy your app to one of these cloud providers: Gemini, AWS, or Azure.
Add a vector database to your project (saving, comparing, and calculating vectors).
Use open-source LLMs (not Gemini, OpenAI, etc.) for the project.
Fine-tune an LLM to have an interview preparation focus.
Add User Session Management to log in, register, and save chat history for the user.
Implement secure and anonymized logging to track errors and performance without exposing sensitive data.

## Feedback:

It was the second project review with Ignas and again he demonstrated solid knowledge on the project and presented quite interesting work for this project. So, for this project Ignas developed a simple RAG system where all components technically worked, however there were some lack of arguments and solution explainability during the review. For example, talking about shunning strategy, that should be tested & experimented in order to find the best one, as well as retrieval part should take appropriate number of most similar chunks, not hardcoded one. We clearly discussed that during the project review. 
Moreover, I would suggest to improve user interface in a way to generate more valuable outcomes for the end user. It was a good idea to leverage functionality of PDF parser which worked well and was connected to chunking mechanism. In this area, I would suggest to polish the chunking part in order to avoid covering multiple parts of paragraph per single chunk. That relatively strongly impact overall RAG performance.
I am sure Ignas is a strong and motivated learner and I believe in case having more time he would build even more efficient application in all perspectives. I hope that the review was useful and wishing all the best in further assignments in the course!