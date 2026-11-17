import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

function App() {
  const [status, setStatus] = useState('Checking API...');
  const [cards, setCards] = useState([]);
  useEffect(() => {
    fetch('/api/status', {cache:'no-store'})
      .then(r => r.ok ? r.json() : Promise.reject(new Error('API not ready')))
      .then(v => setStatus(`${v.api} · database ${v.database}`))
      .catch(() => setStatus('API/database not available'));
    fetch('/api/catalog', {cache:'no-store'})
      .then(r => r.ok ? r.json() : Promise.reject(new Error('Catalog not ready')))
      .then(v => setCards(v.items || []))
      .catch(() => setCards([]));
  }, []);
  return <main>
    <header className="topline"><span className="brand">ATLAS <small>/ infrastructure reference</small></span><span className="tag">AWS SOLUTIONS LAB</span></header>
    <section className="hero">
      <div className="copy"><p className="eyebrow">SECURE / RESILIENT / OBSERVABLE</p>
        <h1>Built for the days when traffic changes.</h1>
        <p>A working React and Python sample for a multi-zone AWS architecture. Private infrastructure, signed image delivery, measured operations.</p>
        <div className="health"><span className="pulse" aria-hidden="true" /> {status}</div>
      </div><img className="heroart" src="/images/atlas-banner.png" alt="Abstract architecture nodes" />
    </section>
    <section className="features"><h2>What this architecture protects</h2>
      <div className="tilegrid">{cards.length ? cards.map(x => <article key={x.slug}><h3>{x.title}</h3><p>{x.detail}</p></article>) :
        <article><h3>Waiting for the database</h3><p>When RDS connectivity is available, this area will display live catalog data from the API.</p></article>}</div>
    </section>
    <footer>Project Atlas · Reference implementation · Managed through CloudFormation</footer>
  </main>;
}

createRoot(document.getElementById('root')).render(<App />);
