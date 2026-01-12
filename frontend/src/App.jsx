import { useState } from 'react';
import UploadForm from './components/UploadForm';
import ProgressIndicator from './components/ProgressIndicator';
import ResultsDisplay from './components/ResultsDisplay';
import './App.css';

function App() {
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleOptimizationStart = (taskId) => {
    setCurrentTaskId(taskId);
    setResults(null);
    setError(null);
  };

  const handleOptimizationComplete = (resultsData) => {
    setResults(resultsData);
    setCurrentTaskId(null);
  };

  const handleOptimizationError = (errorMessage) => {
    setError(errorMessage);
    setCurrentTaskId(null);
  };

  const handleReset = () => {
    setCurrentTaskId(null);
    setResults(null);
    setError(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Solar + Storage Optimization</h1>
        <p>Optimize your solar PV + battery energy storage system configuration</p>
      </header>

      <main className="app-main">
        {error && (
          <div className="error-banner">
            <h3>Error</h3>
            <p>{error}</p>
            <button onClick={handleReset} className="button-secondary">
              Try Again
            </button>
          </div>
        )}

        {!currentTaskId && !results && (
          <UploadForm onOptimizationStart={handleOptimizationStart} />
        )}

        {currentTaskId && !results && (
          <ProgressIndicator
            taskId={currentTaskId}
            onComplete={handleOptimizationComplete}
            onError={handleOptimizationError}
          />
        )}

        {results && (
          <div>
            <ResultsDisplay results={results} />
            <div className="action-buttons">
              <button onClick={handleReset} className="button-primary">
                Run New Optimization
              </button>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Solar + Storage Optimization Model v0.1.0</p>
      </footer>
    </div>
  );
}

export default App;
