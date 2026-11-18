
"use client";

import talukVillageData from "../data/trichy_taluk_villages.json";
import styles from "./LocationSelector.module.css";

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
    <div className={styles.locationGrid}>
      <div className={styles.field}>
        <label htmlFor="taluk">Taluk</label>
        <select
          id="taluk"
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
      </div>

      <div className={styles.field}>
        <label htmlFor="village">Village</label>
        <select
          id="village"
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
    </div>
  );
}
