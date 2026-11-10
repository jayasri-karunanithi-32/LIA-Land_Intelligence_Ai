
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h2>Land Intelligence AI</h2>
        <span>Explore your land. Understand your area.</span>
      </header>

      <main className={styles.main}>
        <section className={styles.location}>
          <h1>Discover Your Land</h1>
          <p>Enter your location to explore area insights.</p>

          <div className={styles.locationForm}>
            <input placeholder="Village" />
            <input placeholder="Taluk" />
            <input placeholder="District" />
            <button>Explore Area</button>
          </div>
        </section>

        <section className={styles.chat}>
          <h2>Ask LIA</h2>
          <p>Ask questions about transport, water resources and infrastructure.</p>

          <div className={styles.chatForm}>
            <input placeholder="Ask something about your area..." />
            <button>Send</button>
          </div>
        </section>

        <section className={styles.insights}>
          <h2>Area Insights</h2>

          <div className={styles.insightGrid}>
            <div>Transport Resources</div>
            <div>Water Resources</div>
            <div>Infrastructure</div>
          </div>
        </section>
      </main>
    </div>
  );
}
