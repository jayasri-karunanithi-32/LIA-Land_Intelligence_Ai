
"use client";

import { useState } from "react";
import styles from "./page.module.css";
import Sidebar from "../components/Sidebar";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

const suggestions = [
  "What infrastructure is available in Trichy?",
  "Explain the water resources in my area.",
  "What transport facilities are nearby?",
  "Give me an overview of land resources in Trichy.",
];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleChat(text = question) {
    const prompt = text.trim();

    if (!prompt || loading) return;

    if (!API_URL) {
      setError("Backend API URL is not configured.");
      return;
    }

    setMessages((previous) => [
      ...previous,
      { role: "user", content: prompt },
    ]);

    setQuestion("");
    setLoading(true);
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

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.answer || "No response received.",
        },
      ]);
    } catch (err) {
      setError(err.message || "Unable to connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  function handleNewChat() {
    setMessages([]);
    setQuestion("");
    setError("");
  }

  const hasMessages = messages.length > 0;

  return (
    <div className={styles.layout}>
      <Sidebar onNewChat={handleNewChat} />

      <main className={styles.main}>
        <header className={styles.topbar}>
          <span>Land Intelligence AI</span>
          <span className={styles.status}>● LIA Assistant</span>
        </header>

        <section className={styles.chatArea}>
          {!hasMessages ? (
            <div className={styles.welcome}>
              <div className={styles.welcomeIcon}>🌿</div>
              <h1>Explore your land with LIA</h1>
              <p>
                Ask anything about land, infrastructure, transport
                and water resources across Tiruchirappalli.
              </p>

              <div className={styles.suggestions}>
                {suggestions.map((item) => (
                  <button
                    key={item}
                    onClick={() => handleChat(item)}
                    disabled={loading}
                  >
                    {item}
                    <span>↗</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className={styles.messages}>
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={
                    message.role === "user"
                      ? styles.userMessage
                      : styles.assistantMessage
                  }
                >
                  <div className={styles.messageLabel}>
                    {message.role === "user" ? "You" : "🌿 LIA"}
                  </div>
                  <div className={styles.messageContent}>
                    {message.content}
                  </div>
                </div>
              ))}

              {loading && (
                <div className={styles.assistantMessage}>
                  <div className={styles.messageLabel}>🌿 LIA</div>
                  <div className={styles.messageContent}>
                    LIA is thinking...
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {error && <p className={styles.error}>{error}</p>}

        <div className={styles.inputArea}>
          <div className={styles.inputBox}>
            <textarea
              placeholder="Ask LIA about your land or area..."
              value={question}
              rows={1}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleChat();
                }
              }}
            />

            <button
              onClick={() => handleChat()}
              disabled={loading || !question.trim()}
              aria-label="Send message"
            >
              ↑
            </button>
          </div>
          <p> LIA can make mistakes. Verify important land information.</p>
        </div>
      </main>
    </div>
  );
}
