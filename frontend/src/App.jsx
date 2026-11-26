import { useEffect, useState } from "react";
import ConfusionMatrix from "./ConfusionMatrix.jsx";

const SAMPLE_PHISHING =
  "URGENT: Your account has been suspended. Verify your password now at http://secure-login-bank.xyz/verify";
const SAMPLE_SAFE =
  "Hi team, the quarterly report is attached. Thanks, Anna. Agenda: https://docs.company.com/agenda";

const pct = (value) =>
  typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "—";

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 2.5 20 6v5.7c0 5.1-3.4 8.8-8 9.8-4.6-1-8-4.7-8-9.8V6l8-3.5Z" />
      <path d="m8.5 12 2.2 2.2 4.8-5" />
    </svg>
  );
}

function CopyIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="8" y="8" width="11" height="11" rx="2" />
      <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
    </svg>
  );
}

export default function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [metricsError, setMetricsError] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetch("/api/health")
      .then((response) => response.json())
      .then((health) => setBackendOnline(health.model_loaded))
      .catch(() => setBackendOnline(false));

    fetch("/api/metrics")
      .then(async (response) => {
        const body = await response.json();
        if (!response.ok) throw new Error(body.error || "Metrics unavailable");
        setMetrics(body);
      })
      .catch((requestError) => setMetricsError(requestError.message));
  }, []);

  async function classify() {
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const response = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || "Request failed");
      setResult(body);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function copyResult() {
    if (!result) return;
    const summary = `Phishing Email Detector: ${result.label} — ${pct(result.phishing_probability)} phishing probability`;
    await navigator.clipboard?.writeText(summary);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  const isPhishing = result?.label === "Phishing";

  return (
    <div className="app">
      <header className="topbar">
        <div className="header-inner">
          <div className="brand">
            <span className="brand-mark"><ShieldIcon /></span>
            <div>
              <h1>Phishing Email Detector</h1>
              <p>Security Intelligence Workspace</p>
            </div>
          </div>
          <StatusPill online={backendOnline} />
        </div>
      </header>

      <main>
        <section className="hero">
          <div>
            <span className="eyebrow">Email risk analysis</span>
            <h2>Detect deceptive email content</h2>
            <p>Analyze message language and embedded links with a machine-learning security model.</p>
          </div>
          {metrics && (
            <div className="hero-stat">
              <span>Model accuracy</span>
              <strong>{pct(metrics.accuracy)}</strong>
            </div>
          )}
        </section>

        <div className="workspace">
          <section className="card analyzer-card">
            <div className="card-head">
              <div className="heading-group">
                <span className="section-index">01</span>
                <h2>Analyze email</h2>
              </div>
              <span className="character-count">{(text?.length ?? 0).toLocaleString()} characters</span>
            </div>

            <label className="field-label" htmlFor="email-content">Email content</label>
            <textarea
              id="email-content"
              rows={11}
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder={"Paste an email subject and body here…\n\nExample: Action required — verify your account to avoid suspension."}
              aria-label="Email content"
            />

            <div className="actions">
              <div className="samples">
                <span>Try a sample</span>
                <button type="button" className="sample-button" onClick={() => setText(SAMPLE_PHISHING)}>Suspicious</button>
                <button type="button" className="sample-button" onClick={() => setText(SAMPLE_SAFE)}>Safe</button>
                <button type="button" className="clear-button" onClick={() => setText("")} disabled={!text}>Clear</button>
              </div>
              <button
                type="button"
                className="primary"
                onClick={classify}
                disabled={!text.trim() || loading || backendOnline === false}
              >
                {loading ? <><span className="spinner" />Analyzing…</> : "Run analysis"}
              </button>
            </div>

            {error && <div className="alert" role="alert">{error}</div>}
          </section>

          <aside className="result-column">
            {result ? (
              <section className={`result-card ${isPhishing ? "danger" : "safe"}`} aria-live="polite">
                <div className="result-head">
                  <div className="heading-group">
                    <span className="section-index">02</span>
                    <h2>Assessment</h2>
                  </div>
                  <button type="button" className="icon-button" onClick={copyResult} aria-label="Copy assessment result">
                    <CopyIcon />
                  </button>
                </div>

                <div className="risk-mark">
                  <span className="risk-dot" />
                  <div>
                    <span>Classification</span>
                    <strong>{result.label}</strong>
                  </div>
                </div>

                <div className="probability">
                  <div>
                    <span>Phishing probability</span>
                    <strong>{pct(result.phishing_probability)}</strong>
                  </div>
                  <div className="probability-track">
                    <span style={{ width: pct(result.phishing_probability) }} />
                  </div>
                </div>

                <div className="signal-list">
                  <Signal label="Links found" value={result.url_stats.count} />
                  <Signal label="Shortened URLs" value={result.url_stats.shortened} />
                  <Signal label="IP-based links" value={result.url_stats.ip_address_links} />
                  <Signal label="Suspicious domains" value={result.url_stats.suspicious_domain} />
                  <Signal label="Non-HTTPS links" value={result.url_stats.non_https} />
                </div>

                {result.urls_found.length > 0 && (
                  <div className="urls">
                    <span>Detected links</span>
                    <ul>{result.urls_found.map((url) => <li key={url}>{url}</li>)}</ul>
                  </div>
                )}
                {copied && <div className="copy-toast">Result copied</div>}
              </section>
            ) : (
              <section className="empty-result">
                <span className="empty-icon"><ShieldIcon /></span>
                <h2>Ready to analyze</h2>
                <p>Submit an email to generate a phishing risk assessment and detect suspicious URL signals.</p>
              </section>
            )}
          </aside>
        </div>

        <section className="card metrics-card">
          <div className="card-head">
            <div className="heading-group">
              <span className="section-index">03</span>
              <h2>Model performance</h2>
            </div>
            {metrics && <span className="evaluation">{metrics.evaluation}</span>}
          </div>

          {metricsError && <div className="alert">{metricsError}. Run the model training script first.</div>}

          {metrics && (
            <>
              <div className="metrics">
                <Metric label="Accuracy" value={metrics.accuracy} />
                <Metric label="Precision" value={metrics.precision} />
                <Metric label="Recall" value={metrics.recall} />
                <Metric label="F1-score" value={metrics.f1} />
              </div>

              <div className="cm-layout">
                <ConfusionMatrix matrix={metrics.confusion_matrix} labels={metrics.labels} />
                <div>
                  {metrics.holdout && (
                    <div className="holdout">
                      <div className="holdout-title">Held-out test split</div>
                      <dl>
                        <dt>Emails evaluated</dt>
                        <dd>{metrics.holdout.test_size}</dd>
                        <dt>Accuracy</dt>
                        <dd>{pct(metrics.holdout.accuracy)}</dd>
                        <dt>F1-score</dt>
                        <dd>{pct(metrics.holdout.f1)}</dd>
                      </dl>
                    </div>
                  )}
                  <p className="note">
                    Dataset: {metrics.dataset} ({(metrics.n_emails ?? 0).toLocaleString()} emails).
                    Template-generated data should be validated on a public corpus before real-world use.
                  </p>
                </div>
              </div>
            </>
          )}
        </section>
      </main>

      <footer className="footer">
        <span>Phishing Email Detector</span>
        <span>Machine-learning security prototype</span>
      </footer>
    </div>
  );
}

function StatusPill({ online }) {
  const state = online === null ? "checking" : online ? "online" : "offline";
  const text = state === "online" ? "System operational" : state === "offline" ? "API unavailable" : "Connecting";
  return <span className={`status ${state}`}><i />{text}</span>;
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{pct(value)}</strong>
    </div>
  );
}

function Signal({ label, value }) {
  return (
    <div className="signal">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
