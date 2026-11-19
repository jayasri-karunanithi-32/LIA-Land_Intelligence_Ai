
"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

// Lazy-load the GitHub connect modal — only loaded when the user clicks
const GitHubConnect = dynamic(() => import("./GitHubConnect"), { ssr: false });

export default function PluginCard({ plugin }) {
  const [showGitHub, setShowGitHub] = useState(false);

  const handleClick = () => {
    if (plugin.id === "github") {
      setShowGitHub(true);
    } else {
      alert("Will be updated soon!");
    }
  };

  return (
    <>
      <div className="plugin-card">
        <div className="plugin-icon">
          {plugin.id === "github" ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src="/github.png" alt="GitHub" />
          ) : (
            plugin.icon
          )}
        </div>

        <h3>{plugin.name}</h3>

        <p>{plugin.description}</p>

        <button onClick={handleClick}>
          {plugin.id === "github" ? "Connect GitHub" : "Coming Soon"}
        </button>
      </div>

      {showGitHub && plugin.id === "github" && (
        <GitHubConnect onClose={() => setShowGitHub(false)} />
      )}
    </>
  );
}
