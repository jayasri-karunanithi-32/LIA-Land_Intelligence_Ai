
"use client";

import Sidebar from "../components/Sidebar";
import plugins from "../components/plugins/pluginsData";
import PluginCard from "../components/plugins/PluginCard";
import "./plugins.css";

export default function PluginsPage() {
  return (
    <div className="plugins-layout">
      <Sidebar />

      <main className="plugins-container">
        <div className="plugins-header">
          <h1>Plugins</h1>
          <p>Extend LIA with additional integrations and tools.</p>
        </div>

        <div className="plugins-grid">
          {plugins.map((plugin) => (
            <PluginCard key={plugin.id} plugin={plugin} />
          ))}
        </div>
      </main>
    </div>
  );
}
