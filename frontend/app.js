const API_BASE = "http://127.0.0.1:8000";

const companyListEl = document.getElementById("company-list");
const compareSelect1 = document.getElementById("compare-symbol-1");
const compareSelect2 = document.getElementById("compare-symbol-2");
const compareButton = document.getElementById("compare-button");
const rangeButtons = document.querySelectorAll(".range-btn");
const summaryContentEl = document.getElementById("summary-content");
const topGainersEl = document.getElementById("top-gainers");
const topLosersEl = document.getElementById("top-losers");
const chartTitleEl = document.getElementById("chart-title");

const priceCanvas = document.getElementById("price-chart");
const compareCanvas = document.getElementById("compare-chart");

let priceChart = null;
let compareChart = null;

let companies = [];
let selectedSymbol = null;
let currentRangeDays = 30;

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Request failed with status ${res.status}`);
  }
  return await res.json();
}

async function loadCompanies() {
  const data = await fetchJson(`${API_BASE}/companies`);
  companies = data;
  companyListEl.innerHTML = "";
  compareSelect1.innerHTML = "";
  compareSelect2.innerHTML = "";

  data.forEach((c, idx) => {
    const li = document.createElement("li");
    li.textContent = c.symbol;
    li.dataset.symbol = c.symbol;
    li.addEventListener("click", () => onCompanyClick(c.symbol));
    companyListEl.appendChild(li);

    const opt1 = document.createElement("option");
    opt1.value = c.symbol;
    opt1.textContent = c.symbol;
    compareSelect1.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = c.symbol;
    opt2.textContent = c.symbol;
    compareSelect2.appendChild(opt2);

    if (idx === 0) {
      selectedSymbol = c.symbol;
      li.classList.add("active");
      compareSelect1.value = c.symbol;
      compareSelect2.value = c.symbol;
    }
  });

  if (selectedSymbol) {
    await updateMainSymbol(selectedSymbol);
  }

  await updateTopMovers();
}

function setActiveCompany(symbol) {
  const items = companyListEl.querySelectorAll("li");
  items.forEach((li) => {
    if (li.dataset.symbol === symbol) {
      li.classList.add("active");
    } else {
      li.classList.remove("active");
    }
  });
}

async function onCompanyClick(symbol) {
  selectedSymbol = symbol;
  setActiveCompany(symbol);
  await updateMainSymbol(symbol);
}

function sliceByRange(data, days) {
  if (!Array.isArray(data) || data.length === 0) return [];
  if (days >= data.length) return data;
  return data.slice(data.length - days);
}

function linearRegression(xs, ys) {
  const n = xs.length;
  if (n === 0) {
    return { slope: 0, intercept: 0 };
  }
  let sumX = 0;
  let sumY = 0;
  let sumXY = 0;
  let sumXX = 0;
  for (let i = 0; i < n; i++) {
    sumX += xs[i];
    sumY += ys[i];
    sumXY += xs[i] * ys[i];
    sumXX += xs[i] * xs[i];
  }
  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
}

function buildPredictionSeries(dates, closes) {
  if (dates.length < 2) {
    return { futureDates: [], futureValues: [] };
  }
  const xs = dates.map((d, idx) => idx);
  const ys = closes;
  const { slope, intercept } = linearRegression(xs, ys);
  const futurePoints = 7;
  const futureDates = [];
  const futureValues = [];
  const lastDate = new Date(dates[dates.length - 1]);
  for (let i = 1; i <= futurePoints; i++) {
    const futureIdx = xs.length - 1 + i;
    const futureValue = slope * futureIdx + intercept;
    const fd = new Date(lastDate);
    fd.setDate(fd.getDate() + i);
    futureDates.push(fd.toISOString().slice(0, 10));
    futureValues.push(futureValue);
  }
  return { futureDates, futureValues };
}

function updatePriceChart(symbol, data) {
  const dates = data.map((d) => d.date);
  const closes = data.map((d) => d.close);

  const { futureDates, futureValues } = buildPredictionSeries(dates, closes);
  const allLabels = dates.concat(futureDates);

  const historyData = closes.concat(Array(futureValues.length).fill(null));
  const predictionData = Array(closes.length - 1)
    .fill(null)
    .concat([closes[closes.length - 1]])
    .concat(futureValues);

  if (priceChart) {
    priceChart.destroy();
  }

  priceChart = new Chart(priceCanvas.getContext("2d"), {
    type: "line",
    data: {
      labels: allLabels,
      datasets: [
        {
          label: "Close",
          data: historyData,
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59,130,246,0.15)",
          tension: 0.2,
        },
        {
          label: "Prediction",
          data: predictionData,
          borderColor: "#f97316",
          borderDash: [6, 4],
          pointRadius: 0,
          tension: 0.2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          top: 10,
          right: 12,
          bottom: 24,
          left: 12,
        },
      },
      scales: {
        x: {
          ticks: {
            maxTicksLimit: 8,
            color: "#e5e7eb",
            padding: 8,
          },
          grid: {
            color: "rgba(55,65,81,0.4)",
          },
        },
        y: {
          ticks: {
            color: "#e5e7eb",
            padding: 8,
          },
          grid: {
            color: "rgba(31,41,55,0.5)",
          },
        },
      },
      plugins: {
        legend: {
          labels: {
            color: "#e5e7eb",
          },
        },
      },
    },
  });

  chartTitleEl.textContent = `${symbol} Close Price and Prediction`;
}

function updateSummary(symbol, summary) {
  summaryContentEl.innerHTML = `
    <p>Symbol: ${summary.symbol}</p>
    <p>52w High: ${summary.high_52w.toFixed(2)}</p>
    <p>52w Low: ${summary.low_52w.toFixed(2)}</p>
    <p>Avg Close: ${summary.avg_close.toFixed(2)}</p>
  `;
}

function updateCompareChart(compareData) {
  const labels = [compareData.symbol1.symbol, compareData.symbol2.symbol];
  const returns = [compareData.symbol1.return_30d * 100, compareData.symbol2.return_30d * 100];
  const vols = [compareData.symbol1.avg_volatility_30d * 100, compareData.symbol2.avg_volatility_30d * 100];

  if (compareChart) {
    compareChart.destroy();
  }

  compareChart = new Chart(compareCanvas.getContext("2d"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "30d Return (%)",
          data: returns,
          backgroundColor: "rgba(34,197,94,0.6)",
        },
        {
          label: "Avg Volatility 30d (%)",
          data: vols,
          backgroundColor: "rgba(239,68,68,0.6)",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          top: 10,
          right: 12,
          bottom: 24,
          left: 12,
        },
      },
      plugins: {
        legend: {
          labels: {
            color: "#e5e7eb",
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "#e5e7eb",
            padding: 6,
          },
        },
        y: {
          ticks: {
            color: "#e5e7eb",
            padding: 6,
          },
        },
      },
    },
  });
}

async function updateMainSymbol(symbol) {
  const rawSymbol = symbol.replace(".NS", "");
  const data = await fetchJson(`${API_BASE}/data/${rawSymbol}`);
  const sliced = sliceByRange(data, currentRangeDays);
  if (sliced.length === 0) return;

  updatePriceChart(symbol, sliced);

  const summary = await fetchJson(`${API_BASE}/summary/${rawSymbol}`);
  updateSummary(symbol, summary);
}

async function onCompareClick() {
  const s1 = compareSelect1.value.replace(".NS", "");
  const s2 = compareSelect2.value.replace(".NS", "");
  if (!s1 || !s2) return;
  const compareData = await fetchJson(
    `${API_BASE}/compare?symbol1=${encodeURIComponent(s1)}&symbol2=${encodeURIComponent(s2)}`
  );
  updateCompareChart(compareData);
}

function computeReturn30d(data) {
  if (!Array.isArray(data) || data.length < 2) return null;
  const start = data[0].close;
  const end = data[data.length - 1].close;
  if (!start || start === 0) return null;
  return (end - start) / start;
}

async function updateTopMovers() {
  const results = [];
  for (const c of companies) {
    const raw = c.symbol.replace(".NS", "");
    try {
      const data = await fetchJson(`${API_BASE}/data/${raw}`);
      const ret = computeReturn30d(data);
      if (ret !== null) {
        results.push({ symbol: c.symbol, return30d: ret });
      }
    } catch (e) {
    }
  }
  results.sort((a, b) => b.return30d - a.return30d);

  const gainers = results.slice(0, 5);
  const losers = results.slice(-5).reverse();

  topGainersEl.innerHTML = "";
  topLosersEl.innerHTML = "";

  gainers.forEach((g) => {
    const li = document.createElement("li");
    li.textContent = `${g.symbol}: ${(g.return30d * 100).toFixed(2)}%`;
    topGainersEl.appendChild(li);
  });

  losers.forEach((l) => {
    const li = document.createElement("li");
    li.textContent = `${l.symbol}: ${(l.return30d * 100).toFixed(2)}%`;
    topLosersEl.appendChild(li);
  });
}

rangeButtons.forEach((btn) => {
  btn.addEventListener("click", async () => {
    rangeButtons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentRangeDays = parseInt(btn.dataset.range, 10);
    if (selectedSymbol) {
      await updateMainSymbol(selectedSymbol);
    }
  });
});

compareButton.addEventListener("click", onCompareClick);

loadCompanies().catch((err) => {
  console.error(err);
});
