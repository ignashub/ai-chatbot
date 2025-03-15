'use client';

import ChatInterface from './components/ChatInterface';
import RemindersPanel from './components/RemindersPanel';
import NutritionSearch from './components/NutritionSearch';
import KnowledgeBase from './components/KnowledgeBase';
import DocumentUploader from './components/DocumentUploader';

export default function Home() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4">
      <div className="md:col-span-2">
        <ChatInterface />
      </div>
      <div className="space-y-4">
        <RemindersPanel />
        <NutritionSearch />
        <KnowledgeBase />
        <DocumentUploader />
      </div>
    </div>
  );
}