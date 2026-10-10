import React, { useState } from 'react';
import './styles/neo-brutalism.css';
import { Header, type TabId } from './components/ui/Header';
import { Footer } from './components/ui/Footer';
import { CompressPage } from './pages/CompressPage';
import { DecompressPage } from './pages/DecompressPage';
import { ImageOptimizerPage } from './pages/ImageOptimizerPage';
import { BenchmarkPage } from './pages/BenchmarkPage';
import { InspectPage } from './pages/InspectPage';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('compress');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="nb-container" style={{ flex: 1, paddingTop: '2rem' }}>
        {activeTab === 'compress' && <CompressPage />}
        {activeTab === 'decompress' && <DecompressPage />}
        {activeTab === 'image' && <ImageOptimizerPage />}
        {activeTab === 'benchmark' && <BenchmarkPage />}
        {activeTab === 'inspect' && <InspectPage />}
      </main>

      <Footer />
    </div>
  );
};

export default App;
