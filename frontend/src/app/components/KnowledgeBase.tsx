"use client";

import { useState } from 'react';
import axios from 'axios';
import { InputText } from 'primereact/inputtext';
import { Button } from 'primereact/button';
import { Card } from 'primereact/card';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Tooltip } from 'primereact/tooltip';

interface KnowledgeResult {
  document: {
    title: string;
    content: string;
  };
  similarity: number;
}

interface KnowledgeResponse {
  query: string;
  results: KnowledgeResult[];
}

const KnowledgeBase = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<KnowledgeResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const searchKnowledge = async () => {
    if (!query) return;

    setLoading(true);
    setResults([]);
    setError(null);

    try {
      console.log('Searching knowledge base for:', query);
      const response = await axios.post('/api/knowledge', { query });
      console.log('Knowledge base response:', response.data);
      
      setResults(response.data.results);
      
      if (response.data.results.length === 0) {
        setError('No relevant information found in the knowledge base.');
      }
    } catch (error) {
      console.error('Error searching knowledge base:', error);
      setError('Failed to search the knowledge base. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      searchKnowledge();
    }
  };

  const cardTitle = (
    <div className="flex items-center gap-2">
      <span>Health Knowledge Base</span>
      <i 
        className="pi pi-info-circle cursor-pointer knowledge-tooltip" 
        data-pr-tooltip="Search our health and wellness knowledge base for information on exercise, nutrition, sleep, stress management, and more."
        data-pr-position="right"
        data-pr-at="right+5 top"
        style={{ fontSize: '0.9rem' }}
      />
    </div>
  );

  return (
    <Card title={cardTitle} className="shadow-lg mb-4">
      <Tooltip target=".knowledge-tooltip" />
      
      <div className="flex gap-2 mb-4">
        <InputText
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for health information..."
          className="w-full"
          onKeyPress={handleKeyPress}
        />
        <Button 
          label="Search" 
          icon="pi pi-search" 
          onClick={searchKnowledge} 
          disabled={loading || !query}
        />
      </div>
      
      {loading && (
        <div className="flex justify-center my-4">
          <ProgressSpinner style={{ width: '50px', height: '50px' }} />
        </div>
      )}
      
      {error && !loading && (
        <div className="p-3 border rounded bg-red-50 text-red-700 mb-3">
          {error}
        </div>
      )}
      
      {results.length > 0 && (
        <div className="knowledge-results">
          {results.map((result, index) => (
            <div key={index} className="mb-4 p-3 border rounded bg-blue-50">
              <h3 className="text-xl font-bold mb-2">{result.document.title}</h3>
              <p className="mb-2">{result.document.content}</p>
              <div className="text-sm text-gray-500">
                Relevance: {Math.round(result.similarity * 100)}%
              </div>
            </div>
          ))}
        </div>
      )}
      
      {!loading && !error && results.length === 0 && (
        <div className="text-center p-4 border rounded bg-gray-50">
          <p>Search our knowledge base for health and wellness information.</p>
          <p className="text-sm text-gray-500 mt-2">
            Try searching for topics like "exercise benefits", "healthy eating", "sleep", or "stress management".
          </p>
        </div>
      )}
    </Card>
  );
};

export default KnowledgeBase; 