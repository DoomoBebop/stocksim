/* ── State ──────────────────────────────────────────────────── */
let positions  = [];   // pending positions list
let buyType    = 'date';
let sellType   = 'date';
let chartRefs  = {};   // chart.js instances keyed by position id

/* ── Init ───────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  loadTickers();
  // Default dates: 1 year ago → today
  const today = new Date();
  const oneYearAgo = new Date(today);
  oneYearAgo.setFullYear(today.getFullYear() - 1);
  document.getElementById('buy-date').value  = fmt(oneYearAgo);
  document.getElementById('sell-date').value = fmt(today);
});

function fmt(d) {
  return d.toISOString().slice(0, 10);
}

/* ── Market / tickers ───────────────────────────────────────── */
async function loadTickers() {
  const market  = document.getElementById('market').value;
  const sel     = document.getElementById('ticker');
  sel.innerHTML = '<option>chargement…</option>';

  const res   = await fetch(`/api/tickers/${encodeURIComponent(market)}`);
  const ticks = await res.json();

  sel.innerHTML = ticks.map(([t, n]) =>
    `<option value="${t}">${t} — ${n}</option>`
  ).join('');

  fetchCurrentPrice();
}

/* ── Live price ─────────────────────────────────────────────── */
async function fetchCurrentPrice() {
  const ticker = document.getElementById('ticker').value;
  const el     = document.getElementById('live-price');
  el.textContent = '…';
  try {
    const res  = await fetch(`/api/price/${encodeURIComponent(ticker)}`);
    const data = await res.json();
    if (data.error) { el.textContent = 'N/A'; return; }
    el.textContent = `${data.price.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 4 })} ${data.currency}`;
  } catch {
    el.textContent = 'erreur';
  }
}

/* ── Buy/Sell type toggle ───────────────────────────────────── */
function setBuyType(type) {
  buyType = type;
  document.getElementById('buy-date-field').style.display = type === 'date'      ? '' : 'none';
  document.getElementById('buy-cond-field').style.display = type === 'condition' ? '' : 'none';
  document.getElementById('buy-date-btn').classList.toggle('active', type === 'date');
  document.getElementById('buy-cond-btn').classList.toggle('active', type === 'condition');
}

function setSellType(type) {
  sellType = type;
  document.getElementById('sell-date-field').style.display = type === 'date'      ? '' : 'none';
  document.getElementById('sell-cond-field').style.display = type === 'condition' ? '' : 'none';
  document.getElementById('sell-date-btn').classList.toggle('active', type === 'date');
  document.getElementById('sell-cond-btn').classList.toggle('active', type === 'condition');
}

/* ── Add position ───────────────────────────────────────────── */
function addPosition() {
  const tickerSel = document.getElementById('ticker');
  const ticker    = tickerSel.value;
  const tickerLabel = tickerSel.options[tickerSel.selectedIndex].text;

  const pos = {
    id: Date.now(),
    ticker,
    tickerLabel,
    market:        document.getElementById('market').value,
    product_type:  document.getElementById('product-type').value,
    leverage:      parseFloat(document.getElementById('leverage-range').value),
    amount:        parseFloat(document.getElementById('amount').value) || 1000,
    buy_type:      buyType,
    buy_date:      document.getElementById('buy-date').value,
    buy_condition_op:    document.getElementById('buy-op').value,
    buy_condition_value: parseFloat(document.getElementById('buy-val').value) || 0,
    sell_type:     sellType,
    sell_date:     document.getElementById('sell-date').value,
    sell_condition_op:    document.getElementById('sell-op').value,
    sell_condition_value: parseFloat(document.getElementById('sell-val').value) || 0,
  };

  positions.push(pos);
  renderPositionList();
}

/* ── Render position list ───────────────────────────────────── */
function renderPositionList() {
  const list = document.getElementById('position-list');
  document.getElementById('pos-count').textContent = positions.length;

  if (positions.length === 0) {
    list.innerHTML = '<div class="empty-state">aucune position — ajoutez-en une ci-dessus</div>';
    document.getElementById('sim-btn').disabled = true;
    document.getElementById('total-invested').textContent = '0 €';
    return;
  }

  const total = positions.reduce((s, p) => s + p.amount, 0);
  document.getElementById('total-invested').textContent =
    total.toLocaleString('fr-FR', { maximumFractionDigits: 0 }) + ' €';
  document.getElementById('sim-btn').disabled = false;

  list.innerHTML = positions.map(p => {
    const buyDesc  = p.buy_type  === 'date'
      ? `achat le ${p.buy_date}`
      : `achat si prix ${p.buy_condition_op} ${p.buy_condition_value}`;
    const sellDesc = p.sell_type === 'date'
      ? `vente le ${p.sell_date}`
      : `vente si prix ${p.sell_condition_op} ${p.sell_condition_value}`;
    const prodLabel = {
      stock: 'stock', etf: 'ETF', cfd: 'CFD',
      option_call: 'CALL', option_put: 'PUT'
    }[p.product_type] || p.product_type;

    return `
    <div class="pos-item" id="pos-${p.id}">
      <span class="pos-ticker">${p.ticker}</span>
      <div class="pos-details">
        <div>${buyDesc}</div>
        <div>${sellDesc}</div>
      </div>
      <span class="pos-amount">${p.amount.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} €</span>
      <span class="pos-lev">${prodLabel} × ${p.leverage.toFixed(1)}</span>
      <button class="pos-remove" onclick="removePosition(${p.id})" title="supprimer">×</button>
    </div>`;
  }).join('');
}

function removePosition(id) {
  positions = positions.filter(p => p.id !== id);
  renderPositionList();
}

/* ── Run simulation ─────────────────────────────────────────── */
async function runSimulation() {
  const btn = document.getElementById('sim-btn');
  btn.innerHTML = '<span class="spinner"></span>simulation…';
  btn.disabled = true;

  // Destroy old charts
  Object.values(chartRefs).forEach(c => c.destroy());
  chartRefs = {};

  const panel = document.getElementById('results-panel');
  panel.style.display = '';

  const summaryEl = document.getElementById('summary-row');
  const listEl    = document.getElementById('results-list');
  summaryEl.innerHTML = '<div style="padding:1.5rem;color:var(--muted)"><span class="spinner"></span> simulation en cours…</div>';
  listEl.innerHTML = '';

  panel.scrollIntoView({ behavior: 'smooth', block: 'start' });

  const results = [];

  for (const pos of positions) {
    const payload = {
      ticker:    pos.ticker,
      market:    pos.market,
      buy_type:  pos.buy_type,
      buy_date:  pos.buy_date,
      buy_condition_op:    pos.buy_condition_op,
      buy_condition_value: pos.buy_condition_value,
      sell_type:  pos.sell_type,
      sell_date:  pos.sell_date,
      sell_condition_op:    pos.sell_condition_op,
      sell_condition_value: pos.sell_condition_value,
      amount:      pos.amount,
      leverage:    pos.leverage,
      product_type: pos.product_type,
    };

    try {
      const res  = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      results.push({ pos, data });
    } catch (e) {
      results.push({ pos, data: { error: e.message } });
    }
  }

  renderResults(results);
  btn.innerHTML = 'simuler tout →';
  btn.disabled = false;
}

/* ── Render results ─────────────────────────────────────────── */
function renderResults(results) {
  const summaryEl = document.getElementById('summary-row');
  const listEl    = document.getElementById('results-list');

  // Aggregate
  let totalInvested = 0, totalFinal = 0, totalPnL = 0, openCount = 0;
  results.forEach(({ pos, data }) => {
    totalInvested += pos.amount;
    if (data.status === 'ok') {
      totalFinal += data.final_value;
      totalPnL   += data.pnl_eur;
      if (data.still_open) openCount++;
    } else {
      totalFinal += pos.amount;
    }
  });
  const totalPct = totalInvested ? (totalPnL / totalInvested) * 100 : 0;

  const pnlClass = totalPnL >= 0 ? 'pos-val' : 'neg-val';
  summaryEl.innerHTML = `
    <div class="summary-cell">
      <div class="summary-label">investi total</div>
      <div class="summary-value neu-val">${totalInvested.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} €</div>
    </div>
    <div class="summary-cell">
      <div class="summary-label">valeur finale</div>
      <div class="summary-value ${pnlClass}">${totalFinal.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} €</div>
    </div>
    <div class="summary-cell">
      <div class="summary-label">P&L total</div>
      <div class="summary-value ${pnlClass}">${totalPnL >= 0 ? '+' : ''}${totalPnL.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} €</div>
    </div>
    <div class="summary-cell">
      <div class="summary-label">rendement</div>
      <div class="summary-value ${pnlClass}">${totalPct >= 0 ? '+' : ''}${totalPct.toFixed(2)}%</div>
    </div>`;

  listEl.innerHTML = '';

  results.forEach(({ pos, data }, idx) => {
    const cardId = `rc-${pos.id}`;
    const chartId = `chart-${pos.id}`;

    if (data.error) {
      listEl.insertAdjacentHTML('beforeend', `
        <div class="result-card rc-untriggered">
          <div class="rc-left">
            <div class="rc-ticker">${pos.ticker}</div>
            <div class="rc-note err">erreur : ${data.error}</div>
          </div>
          <div class="rc-right">
            <div class="rc-pnl-pct neg-val">N/A</div>
          </div>
        </div>`);
      return;
    }

    if (data.status === 'not_triggered') {
      listEl.insertAdjacentHTML('beforeend', `
        <div class="result-card rc-untriggered" id="${cardId}">
          <div class="rc-left">
            <div class="rc-ticker">${pos.ticker}</div>
            <div class="rc-meta">achat non déclenché · ${pos.amount.toLocaleString('fr-FR')} € prévus</div>
            <div class="rc-note warn">${data.note}</div>
          </div>
          <div class="rc-right">
            <div class="rc-pnl-pct" style="color:var(--muted)">—</div>
            <div class="rc-pnl-eur" style="color:var(--muted)">pas exécuté</div>
          </div>
        </div>`);
      return;
    }

    const pnlClass  = data.pnl_eur >= 0 ? 'pos-val' : 'neg-val';
    const pnlSign   = data.pnl_eur >= 0 ? '+' : '';
    const pctSign   = data.pnl_pct >= 0 ? '+' : '';
    const prodLabel = {
      stock: 'stock', etf: 'ETF', cfd: 'CFD',
      option_call: 'CALL', option_put: 'PUT (short)'
    }[data.product_type] || data.product_type;

    const levNote = data.leverage > 1 ? ` · levier ×${data.leverage}` : '';

    listEl.insertAdjacentHTML('beforeend', `
      <div class="result-card" id="${cardId}">
        <div class="rc-left">
          <div class="rc-ticker">${data.ticker}</div>
          <div class="rc-meta">
            ${prodLabel}${levNote} · ${data.amount_invested.toLocaleString('fr-FR')} € investis<br>
            achat le ${data.buy_date} @ ${data.buy_price.toLocaleString('fr-FR', { minimumFractionDigits: 2 })} · vente le ${data.sell_date} @ ${data.sell_price.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}<br>
            ${data.shares.toLocaleString('fr-FR', { maximumFractionDigits: 4 })} unités ${data.leverage > 1 ? '(position avec levier)' : ''}
          </div>
          ${data.still_open ? `<span class="rc-open-badge">position ouverte</span>` : ''}
          <div class="rc-note">${data.buy_note}</div>
          <div class="rc-note${data.still_open ? ' warn' : ''}">${data.sell_note}</div>
          <div class="rc-chart"><canvas id="${chartId}" role="img" aria-label="Évolution du prix de ${data.ticker}"></canvas></div>
        </div>
        <div class="rc-right">
          <div class="rc-pnl-pct ${pnlClass}">${pctSign}${data.pnl_pct.toFixed(2)}%</div>
          <div class="rc-pnl-eur ${pnlClass}">${pnlSign}${data.pnl_eur.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} €</div>
          <div class="rc-final">→ ${data.final_value.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} €</div>
        </div>
      </div>`);

    // Mini sparkline chart
    if (data.sparkline && data.sparkline.length > 1) {
      setTimeout(() => {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;
        const labels = data.sparkline.map(d => d.date);
        const prices = data.sparkline.map(d => d.price);
        const color  = data.pnl_eur >= 0 ? '#7fffb2' : '#ff6b6b';

        chartRefs[pos.id] = new Chart(canvas, {
          type: 'line',
          data: {
            labels,
            datasets: [{
              data: prices,
              borderColor: color,
              backgroundColor: color + '18',
              fill: true,
              tension: 0.4,
              pointRadius: 0,
              borderWidth: 1.5,
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: {
              x: { display: false },
              y: { display: false }
            },
            animation: { duration: 600 }
          }
        });
      }, 50);
    }
  });
}
