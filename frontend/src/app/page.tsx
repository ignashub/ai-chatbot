import ChatInterface from './components/ChatInterface';
import RemindersPanel from './components/RemindersPanel';
import NutritionSearch from './components/NutritionSearch';
import KnowledgeBase from './components/KnowledgeBase';
import DocumentUploader from './components/DocumentUploader';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-8 md:p-24">
      <div className="w-full max-w-5xl">
        <h1 className="text-4xl font-bold mb-8 text-center">Health & Wellness AI Assistant</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2">
            <ChatInterface />
            <KnowledgeBase />
            <DocumentUploader />
          </div>
          <div className="md:col-span-1">
            <RemindersPanel />
            <NutritionSearch />
          </div>
        </div>
        
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