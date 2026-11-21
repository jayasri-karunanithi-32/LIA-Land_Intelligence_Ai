
"use client";

import { useState } from "react";
import Sidebar from "../components/Sidebar";
import LocationSelector from "../components/LocationSelector";
import { createClient } from "@/lib/supabase/client";
import styles from "./page.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function WaterLevelPage() {
  const [village, setVillage] = useState("");
  const [taluk, setTaluk] = useState("");
  const [district] = useState("Tiruchirappalli");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleWaterLevel() {
    if (!village.trim() || !taluk.trim()) {
      setError("Please select Taluk and Village.");
      return;
    }

    if (!API_URL) {
      setError("Backend API URL is not configured.");
      return;
    }

    const prompt = `Provide water level information for Village: ${village.trim()}, Taluk: ${taluk.trim()}, District: ${district}. Return available water level data and relevant insights.`;

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
        throw new Error(data.detail || "Failed to retrieve water level data.");
      }

      const result =
        typeof data.answer === "string" ? data.answer.trim() : "";

      setAnswer(
        result || "Water level data unavailable for this village."
      );
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
          <h2>Know Water Level</h2>
          <p>Explore groundwater information for villages in Tiruchirappalli.</p>
        </header>

        <section className={styles.card}>
          <div className={styles.icon}>💧</div>
          <h1>Village Water Level</h1>
          <p>Select your location to retrieve water level information.</p>

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

          <button onClick={handleWaterLevel} disabled={loading}>
            {loading ? "Fetching Data..." : "Get Water Level"}
          </button>
        </section>

        {error && <p className={styles.error}>{error}</p>}

        {answer && (
          <section className={styles.result}>
            <h2>Water Level Information</h2>
            <p>{answer}</p>
          </section>
        )}
      </main>
    </div>
  );
}
