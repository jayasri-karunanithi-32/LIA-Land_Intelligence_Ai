
"use client";

import { useState } from "react";
import Sidebar from "../components/Sidebar";
import LocationSelector from "../components/LocationSelector";
import { createClient } from "@/lib/supabase/client";
import styles from "./page.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ExplorePage() {
  const [village, setVillage] = useState("");
  const [taluk, setTaluk] = useState("");
  const [district] = useState("Tiruchirappalli");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleExplore() {
    if (!village.trim() || !taluk.trim()) {
      setError("Please select Village and Taluk.");
      return;
    }

    if (!API_URL) {
      setError("Backend API URL is not configured.");
      return;
    }

    const prompt = `Provide land and area insights for Village: ${village.trim()}, Taluk: ${taluk.trim()}, District: ${district}. Include transport resources, water resources and infrastructure where relevant.`;

    setLoading(true);
    setAnswer("");
    setError("");

    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      const token = session?.access_token;

      if (!token) {
        setError("Authentication required. Please log in.");
        return;
      }

      const response = await fetch(`${API_URL}/llm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ prompt }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to get response.");
      }

      setAnswer(data.answer || "No response received.");
    } catch (err) {
      setError(err.message || "Unable to connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.layout}>
      <Sidebar />

      <main className={styles.main}>
        <header className={styles.header}>
          <h2>Explore Area</h2>
          <p>Discover land and infrastructure insights by location.</p>
        </header>

        <section className={styles.card}>
          <h1>Select Your Location</h1>
          <p>Choose a village and taluk to explore its details.</p>

          <LocationSelector
            village={village}
            taluk={taluk}
            setVillage={setVillage}
            setTaluk={setTaluk}
          />

          <div className={styles.district}>
            <label>District</label>
            <input value={district} readOnly />
          </div>

          <button onClick={handleExplore} disabled={loading}>
            {loading ? "Exploring..." : "Explore Area"}
          </button>
        </section>

        {error && <p className={styles.error}>{error}</p>}

        {answer && (
          <section className={styles.result}>
            <h2>Area Insights</h2>
            <p>{answer}</p>
          </section>
        )}
      </main>
    </div>
  );
}
