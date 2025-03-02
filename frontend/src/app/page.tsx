import ChatInterface from './components/ChatInterface';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#f0f4f3]">
      <h1 className="text-2xl font-bold text-[#2e7d32] mb-8">Health and Wellness Coach</h1>
      <div className="w-full max-w-3xl mx-auto p-4">
        <ChatInterface />
      </div>
      <div className="fixed bottom-4 right-4 text-sm text-gray-400 dark:text-gray-500 opacity-70 font-light">
        Ignas Apsega @ Turing College 2025
      </div>
    </div>
  );
}