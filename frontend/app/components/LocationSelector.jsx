"use client";

import { useState } from "react";
import talukVillageData from "../data/trichy_taluk_villages.json";

export default function LocationSelector({
  taluk,
  village,
  setTaluk,
  setVillage,
}) {
  const taluks = Object.keys(talukVillageData);

  const villages = taluk
    ? talukVillageData[taluk] || []
    : [];

  return (
    <div>
      <label>Taluk</label>
      <select
        value={taluk}
        onChange={(e) => {
          setTaluk(e.target.value);
          setVillage("");
        }}
      >
        <option value="">Select Taluk</option>

        {taluks.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>

      <label>Village</label>
      <select
        value={village}
        disabled={!taluk}
        onChange={(e) => setVillage(e.target.value)}
      >
        <option value="">Select Village</option>

        {villages.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
    </div>
  );
}