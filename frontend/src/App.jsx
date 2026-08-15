import { useEffect, useState } from "react";
import { getExposure, getFunds } from "./api";
import FundSelector from "./components/FundSelector";
import ResultsView from "./components/ResultsView";

export default function App() {
  const [funds, setFunds] = useState([]);
  const [selected, setSelected] = useState([]);
  const [exposure, setExposure] = useState(null);
  const [fundsError, setFundsError] = useState("");
  const [resultsError, setResultsError] = useState("");
  const [loadingFunds, setLoadingFunds] = useState(true);
  const [loadingExposure, setLoadingExposure] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getFunds()
      .then((data) => {
        if (!cancelled) setFunds(data.funds || []);
      })
      .catch((err) => {
        if (!cancelled) setFundsError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoadingFunds(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function toggleFund(name) {
    setSelected((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    );
  }

  async function handleSubmit() {
    if (selected.length < 2) return;
    setLoadingExposure(true);
    setResultsError("");
    try {
      const data = await getExposure(selected);
      setExposure(data);
    } catch (err) {
      setExposure(null);
      setResultsError(err.message);
    } finally {
      setLoadingExposure(false);
    }
  }

  return (
    <div className="page">
      <FundSelector
        funds={funds}
        selected={selected}
        onToggle={toggleFund}
        onSubmit={handleSubmit}
        loading={loadingFunds}
        submitting={loadingExposure}
        error={fundsError}
      />
      <ResultsView
        exposure={exposure}
        loading={loadingExposure}
        error={resultsError}
        hasSelection={selected.length >= 2}
      />
    </div>
  );
}
