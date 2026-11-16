
import Sidebar from "../components/Sidebar";
import styles from "./page.module.css";

export default function WaterLevelPage() {
    return (
        <div className={styles.layout}>
            <Sidebar />

            <main className={styles.main}>
                <div className={styles.content}>
                    <div className={styles.icon}>💧</div>
                    <h1>Know Water Level</h1>
                    <p>
                        Water level insights for your selected location will be
                        available here.
                    </p>
                    <span className={styles.badge}>Coming Soon</span>
                </div>
            </main>
        </div>
    );
}
