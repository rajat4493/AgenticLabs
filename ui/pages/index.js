export default function Home() {
  return (
    <main style={{padding: 24, fontFamily: "ui-sans-serif"}}>
      <h1>AgenticLabs UI</h1>
      <p>Next.js is running. API base: {process.env.NEXT_PUBLIC_API_BASE_URL || 'not set'}</p>
      <p>Try: <code>curl http://localhost:8000/healthz</code></p>
    </main>
  );
}
