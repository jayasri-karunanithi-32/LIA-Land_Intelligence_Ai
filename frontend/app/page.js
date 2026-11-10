
import Link from "next/link";
import styles from "./page.module.css";

export default function Home() {
    return (
        <main className={styles.page}>
            <div className={styles.overlay}>
                <section className={styles.content}>
                    <h1>Land Intelligence AI</h1>

                    <p>
                        Explore Your Land. Understand Your Area.
                    </p>

                    <span>
                        Discover transport, water resources,
                        infrastructure and valuable area insights
                        through intelligent location-based research.
                    </span>

                    <Link href="/dashboard" className={styles.button}>
                        Get Started →
                    </Link>
                </section>
            </div>
        </main>
    );
}
