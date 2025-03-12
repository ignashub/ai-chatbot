import ChatInterface from './components/ChatInterface';
import RemindersPanel from './components/RemindersPanel';
import NutritionSearch from './components/NutritionSearch';
import KnowledgeBase from './components/KnowledgeBase';
import DocumentUploader from './components/DocumentUploader';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 lg:p-12">
      <div className="w-full max-w-5xl">
        <h1 className="text-3xl font-bold mb-6 text-center">AI Health Assistant</h1>
        
        <DocumentUploader />
        
        <KnowledgeBase />
        
        <ChatInterface />
        
        <footer className="mt-8 text-center text-sm text-gray-500">
          <p>Powered by OpenAI GPT-4 • Built with Next.js and PrimeReact</p>
        </footer>
        <div className="fixed bottom-4 right-4 text-sm text-gray-400 dark:text-gray-500 opacity-70 font-light">
          Ignas Apsega @ Turing College 2025
        </div>
      </div>
    </main>
  );
}