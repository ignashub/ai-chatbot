# Health & Wellness AI Chatbot

This project is a specialized AI chatbot focused on health and wellness topics. It provides personalized guidance, nutrition information, and allows users to set reminders for health activities.

## Features

- **Knowledge Base Search**: Ask questions about health documents in the knowledge base
- **Reminder Setting**: Set reminders for health activities
- **Nutrition Information**: Get nutrition facts for food items
- **Customizable AI Parameters**: Adjust temperature, top-p, frequency penalty, and presence penalty
- **Export Conversations**: Download conversations in JSON, CSV, or PDF formats

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- OpenAI API Key

### Setup and Installation

1. **Clone the repository**

```bash
git clone <repository-url>
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

## Project Task Requirements

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

Easy:

Ask ChatGPT to critique your solution from the usability, security, and prompt-engineering sides.
Improving the chatbot to be more specialized for your specific domain: IT, HR, marketing, finance, etc.
Adding a separate text field for the system prompt.
Implementing more security constraints, like user input validation and system prompt validation. Could we consider utilizing ChatGPT to verify these aspects?
Add an interactive help feature or chatbot guide explaining how to use the app.


Medium:

Adding all of the OpenAI settings (models, temperature, frequency, etc.) for the user to tune as sliders/fields.
Deploying your app to the Internet.
Calculating and providing output to the user on the price of the prompt.
Read OpenAI API documentation, think of your own improvement, and implement it.
Implement function calling function calling, like a calculator, a map renderer, currency converter, etc.
Try to jailbreak (break into) your own application. Provide the results of this experiment in an Excel sheet.
Adding RAG functionality to the app: adding a knowledge base, retrieving when a similar is found, and sending it to ChatGPT.
Provide the user with the ability to choose from a list of LLMs (Gemini, OpenAI, etc.) for this project.
Think of a creative way; how could you use image generation inside this project and implement it using code?
Allow users to download conversations or generated data in formats like PDF, CSV, or JSON.


Hard:

Using Streamlit (Python) or React (JS) components, implementing a full-fledged chatbot application instead of a one-time call to the OpenAI API.
Deploy your app to one of these cloud providers: Gemini, AWS, or Azure.
Add a vector database to your project (saving, comparing, and calculating vectors).
Use open-source LLMs (not Gemini, OpenAI, etc.) for the project.
Fine-tine an LLM to have an interview preparation focus.
Add User Session Management to log in, register, and save chat history for the user.
Implement secure and anonymized logging to track errors and performance without exposing sensitive data.
