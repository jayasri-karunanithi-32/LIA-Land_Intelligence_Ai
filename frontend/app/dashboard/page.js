
"use client";

import { useState } from "react";
import styles from "./page.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default function Home() {
  const [village, setVillage] = useState("");
  const [taluk, setTaluk] = useState("");
  const [district, setDistrict] = useState("Tiruchirappalli");

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function askBackend(prompt) {
    if (!prompt.trim()) {
      setError("Please enter your input.");
      return;
    }

    if (!API_URL) {
      setError("Backend API URL is not configured.");
      return;
    }

    setLoading(true);
    setAnswer("");
    setError("");

    try {
      const response = await fetch(`${API_URL}/llm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to get response.");
      }

      setAnswer(data.answer);
    } catch (err) {
      setError(err.message || "Unable to connect to the backend.");
    } finally {
      setLoading(false);
    }
  }


  function handleExplore() {
    if (!village.trim() || !taluk.trim() || !district.trim()) {
      setError("Please enter Village, Taluk and District.");
      setAnswer("");
      return;
    }

    const locationPrompt = `Provide land and area insights for Village: ${village.trim()}, Taluk: ${taluk.trim()}, District: ${district.trim()}. Include transport resources, water resources and infrastructure where relevant.`;

    askBackend(locationPrompt);
  }

  function handleChat() {
    askBackend(question);
  }

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
            <input
              placeholder="Village"
              value={village}
              onChange={(e) => setVillage(e.target.value)}
            />

            <input
              placeholder="Taluk"
              value={taluk}
              onChange={(e) => setTaluk(e.target.value)}
            />

            <input
              placeholder="District"
              value={district}
              readOnly
            />

            <button onClick={handleExplore} disabled={loading}>
              Explore Area
            </button>
          </div>
        </section>

        <section className={styles.chat}>
          <h2>Ask LIA</h2>
          <p>
            Ask questions about transport, water resources and infrastructure.
          </p>

          <div className={styles.chatForm}>
            <input
              placeholder="Ask something about your area..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !loading) handleChat();
              }}
            />

            <button onClick={handleChat} disabled={loading}>
              Send
            </button>
          </div>
        </section>

        {loading && <p> LIA is processing your request...</p>}

        {error && <p className={styles.error}>{error}</p>}

        {answer && (
          <section className={styles.answer}>
            <h2>LIA Response</h2>
            <p>{answer}</p>
          </section>
        )}


      </main>
    </div>
  );
}
