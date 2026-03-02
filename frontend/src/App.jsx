import { useMemo, useState } from "react";

const defaults = {
  bi: import.meta.env.VITE_BI_BASE_URL || "http://localhost:8101",
  api: import.meta.env.VITE_API_HUB_BASE_URL || "http://localhost:8102",
  content: import.meta.env.VITE_CONTENT_BASE_URL || "http://localhost:8103",
  fusional: import.meta.env.VITE_FUSIONAL_BASE_URL || "http://localhost:8089",
};

const services = [
  { key: "bi", name: "Business Intelligence MCP", path: "/health" },
  { key: "api", name: "API Integration Hub", path: "/health" },
  { key: "content", name: "Content Automation MCP", path: "/health" },
  { key: "fusional", name: "FusionAL Engine", path: "/health" },
];

export default function App() {
  const [status, setStatus] = useState({});
  const [checking, setChecking] = useState(false);

  const checks = useMemo(
    () =>
      services.map((service) => ({
        ...service,
        url: `${defaults[service.key]}${service.path}`,
      })),
    []
  );

  const checkAll = async () => {
    setChecking(true);
    const next = {};

    await Promise.all(
      checks.map(async (service) => {
        try {
          const response = await fetch(service.url, { method: "GET" });
          next[service.key] = response.ok ? "healthy" : `http-${response.status}`;
        } catch {
          next[service.key] = "offline";
        }
      })
    );

    setStatus(next);
    setChecking(false);
  };

  return (
    <main className="app-shell">
      <section className="hero">
        <h1>MCP Consulting Kit</h1>
        <p>Production dashboard for service health, endpoint visibility, and deployment readiness.</p>
        <button type="button" onClick={checkAll} disabled={checking}>
          {checking ? "Checking..." : "Run health check"}
        </button>
      </section>

      <section className="grid">
        {checks.map((service) => (
          <article key={service.key} className="card">
            <h2>{service.name}</h2>
            <p className="endpoint">{service.url}</p>
            <p className={`badge ${status[service.key] || "unknown"}`}>
              {status[service.key] || "unknown"}
            </p>
          </article>
        ))}
      </section>
    </main>
  );
}
