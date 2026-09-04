"use client";

import { useState } from "react";

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);
  return (
    <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 720, margin: "40px auto", padding: "0 16px" }}>
      <h1>VCM Settings</h1>
      <p>Configure local project-management behavior. Values are saved by the host integration.</p>
      <label style={{ display: "block", margin: "20px 0" }}>
        Default provider
        <select defaultValue="local-fallback" style={{ display: "block", marginTop: 8, padding: 8, width: "100%" }}>
          <option value="local-fallback">Local fallback</option>
          <option value="siliconflow">SiliconFlow</option>
        </select>
      </label>
      <label style={{ display: "block", margin: "20px 0" }}>
        <input type="checkbox" defaultChecked /> Require user confirmation before migration writes
      </label>
      <button type="button" onClick={() => setSaved(true)} style={{ padding: "8px 14px" }}>Save settings</button>
      {saved && <p role="status">Settings staged for persistence.</p>}
    </main>
  );
}
