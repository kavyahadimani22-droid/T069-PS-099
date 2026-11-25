"""Built-in HTTP dashboard server for visualizing T069-PS-099 pricing, matching, and settlements."""

import json
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from app.commands.command_processor import run_command_file
from app.database.connection import initialize_database
from app.models.entities import Load
from app.repositories.freight_repository import FreightRepository
from app.services.exceptions import RuleError, rupee
from app.services.pricing_service import price_load
from app.services.reporting_service import export_csv_reports
from app.services.sample_loader import load_engine_from_csv_dir


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>T069-PS-099 | Freight Exchange & Dynamic Pricing Engine</title>
  <style>
    :root {
      --bg: #0b1220;
      --panel: #121b2e;
      --panel-2: #18243d;
      --border: #263554;
      --text: #e6edf7;
      --muted: #93a4c3;
      --accent: #38bdf8;
      --green: #22c55e;
      --amber: #f59e0b;
      --red: #ef4444;
      --purple: #a78bfa;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; font-family: Inter, Segoe UI, system-ui, sans-serif;
      background: var(--bg); color: var(--text); line-height: 1.5;
    }
    header {
      background: linear-gradient(135deg, #0f172a, #172554);
      border-bottom: 1px solid var(--border);
      padding: 18px 28px; display: flex; flex-wrap: wrap;
      justify-content: space-between; align-items: center; gap: 14px;
    }
    header h1 { margin: 0; font-size: 20px; letter-spacing: 0.2px; }
    header p { margin: 3px 0 0; color: var(--muted); font-size: 13px; }
    .btn {
      background: var(--accent); color: #061322; border: none;
      padding: 10px 16px; border-radius: 8px; font-weight: 700;
      cursor: pointer; font-size: 13px; transition: opacity .15s;
    }
    .btn:hover { opacity: 0.9; }
    .btn-secondary {
      background: var(--panel-2); color: var(--text); border: 1px solid var(--border);
    }
    main { max-width: 1360px; margin: 0 auto; padding: 22px 24px 48px; }
    .kpis {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px; margin-bottom: 22px;
    }
    .kpi {
      background: var(--panel); border: 1px solid var(--border);
      border-radius: 12px; padding: 14px 16px;
    }
    .kpi .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .5px; }
    .kpi .val { font-size: 24px; font-weight: 700; margin-top: 6px; color: var(--accent); }
    .grid-2 { display: grid; grid-template-columns: 1.1fr 1fr; gap: 18px; margin-bottom: 20px; }
    @media (max-width: 960px) { .grid-2 { grid-template-columns: 1fr; } }
    .card {
      background: var(--panel); border: 1px solid var(--border);
      border-radius: 12px; padding: 18px; margin-bottom: 20px;
    }
    .card h2 { margin: 0 0 12px; font-size: 16px; display: flex; align-items: center; justify-content: space-between; }
    .badge {
      display: inline-block; padding: 2px 8px; border-radius: 999px;
      font-size: 11px; font-weight: 700; background: var(--panel-2); border: 1px solid var(--border);
    }
    .b-settled { color: var(--green); border-color: rgba(34,197,94,.4); }
    .b-aborted, .b-cancelled { color: var(--red); border-color: rgba(239,68,68,.4); }
    .b-matched { color: var(--amber); border-color: rgba(245,158,11,.4); }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--border); }
    th { color: var(--muted); font-weight: 600; font-size: 12px; text-transform: uppercase; }
    tr:hover td { background: rgba(56,189,248,.05); }
    .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(145px, 1fr)); gap: 10px; }
    label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
    select, input {
      width: 100%; padding: 8px 10px; border-radius: 8px;
      background: var(--panel-2); color: var(--text); border: 1px solid var(--border); font-size: 13px;
    }
    .sim-result {
      margin-top: 14px; background: var(--panel-2); border: 1px solid var(--border);
      border-radius: 10px; padding: 12px 14px; font-size: 13px;
    }
    .scroll-x { overflow-x: auto; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>T069-PS-099 &mdash; Freight Exchange &amp; Dynamic Pricing Engine</h1>
      <p>Capstone Live Dashboard &bull; Pricing (BR-01&ndash;08), Eligibility &amp; HOS (BR-09&ndash;14), Bidding (BR-15&ndash;16), Settlement &amp; GST/TDS (BR-17&ndash;30)</p>
    </div>
    <div style="display:flex;gap:10px;">
      <button class="btn" onclick="runSamplePack()">Run Full Sample Pack</button>
      <button class="btn btn-secondary" onclick="loadState()">Refresh State</button>
    </div>
  </header>

  <main>
    <div class="kpis" id="kpis"></div>

    <div class="grid-2">
      <div class="card">
        <h2>Interactive Dynamic Pricing Simulator <span class="badge">BR-01 to BR-08 + BR-29/30</span></h2>
        <div class="form-grid">
          <div>
            <label>Origin</label>
            <select id="simOrigin"></select>
          </div>
          <div>
            <label>Destination</label>
            <select id="simDest"></select>
          </div>
          <div>
            <label>Truck Type</label>
            <select id="simType">
              <option>LCV</option><option selected>17FT</option><option>22FT</option>
              <option>32FT_MXL</option><option>TRAILER</option>
            </select>
          </div>
          <div>
            <label>Material</label>
            <select id="simMat">
              <option>GENERAL</option><option>HAZARDOUS</option>
              <option>PERISHABLE</option><option>OVERSIZE</option>
            </select>
          </div>
          <div>
            <label>Extra Stops (BR-29)</label>
            <input id="simStops" type="number" min="0" value="0" />
          </div>
          <div>
            <label>Fuel Index % (BR-30)</label>
            <input id="simFuel" type="number" step="0.5" value="0" />
          </div>
        </div>
        <div style="margin-top:12px;">
          <button class="btn" onclick="simulatePrice()">Calculate Recommended Price</button>
        </div>
        <div class="sim-result" id="simResult">Click "Calculate Recommended Price" to inspect live dynamic adjustments.</div>
      </div>

      <div class="card">
        <h2>Carrier Ratings &amp; Annual Payouts <span class="badge">BR-25, BR-27, BR-28</span></h2>
        <div class="scroll-x">
          <table id="carriersTable">
            <thead><tr><th>Carrier</th><th>Rating</th><th>2nd Driver</th><th>Annual Payout</th><th>Eligible (&ge;3.0)</th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>Dynamic Price Breakdowns <span class="badge">All Posted Loads</span></h2>
      <div class="scroll-x">
        <table id="loadsTable">
          <thead>
            <tr>
              <th>Load</th><th>Lane</th><th>Type</th><th>Material</th>
              <th>Km (Billable)</th><th>Base (&#8377;)</th><th>Ratio</th>
              <th>Surge</th><th>Backhaul</th><th>Poor City</th><th>Mat.</th><th>Recommended (&#8377;)</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <h2>Trips, Settlements &amp; Shipper Invoices <span class="badge">GST / RCM / TDS</span></h2>
      <div class="scroll-x">
        <table id="tripsTable">
          <thead>
            <tr>
              <th>Trip</th><th>Truck</th><th>State</th><th>Agreed (&#8377;)</th>
              <th>Detention (&#8377;)</th><th>Toll (&#8377;)</th><th>Platform 6%</th>
              <th>TDS 1%</th><th>Carrier Payout</th><th>GST 5%</th><th>Shipper Invoice</th><th>RCM</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <h2>Truck Eligibility Rejection Audit <span class="badge">BR-09 to BR-12, BR-26, BR-28</span></h2>
      <div class="scroll-x">
        <table id="rejectionsTable">
          <thead><tr><th>Minute</th><th>Load</th><th>Truck</th><th>Rejection Reasons</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </main>

  <script>
    async function fetchJSON(url, opts) {
      const res = await fetch(url, opts);
      return await res.json();
    }

    function fmt(v) { return v === null || v === undefined ? "-" : v; }

    function populateCities(cities) {
      const o = document.getElementById("simOrigin");
      const d = document.getElementById("simDest");
      if (o.options.length) return;
      cities.forEach(c => {
        o.add(new Option(c, c));
        d.add(new Option(c, c));
      });
      o.value = "Bengaluru";
      d.value = "Chennai";
    }

    async function loadState() {
      const data = await fetchJSON("/api/state");
      populateCities(data.cities);

      const k = data.kpis;
      document.getElementById("kpis").innerHTML = [
        ["Loads Processed", k.loads],
        ["Settled Trips", k.settled_trips],
        ["Cancelled / Aborted", k.cancelled_or_aborted],
        ["Freight Volume", "&#8377;" + k.total_freight],
        ["Platform Revenue (6%)", "&#8377;" + k.total_platform_fee],
        ["TDS Deducted (1%)", "&#8377;" + k.total_tds],
      ].map(([lbl, val]) => `<div class="kpi"><div class="label">${lbl}</div><div class="val">${val}</div></div>`).join("");

      document.querySelector("#carriersTable tbody").innerHTML = data.carriers.map(c => `
        <tr>
          <td><strong>${c.id}</strong><br><span style="color:var(--muted);font-size:12px">${c.name}</span></td>
          <td class="mono">${c.rating}</td>
          <td>${c.second_driver ? "Yes" : "No"}</td>
          <td class="mono">&#8377;${c.annual_payout}</td>
          <td><span class="badge ${Number(c.rating) >= 3 ? "b-settled" : "b-aborted"}">${Number(c.rating) >= 3 ? "ELIGIBLE" : "EXCLUDED"}</span></td>
        </tr>`).join("");

      document.querySelector("#loadsTable tbody").innerHTML = data.loads.map(l => `
        <tr>
          <td class="mono"><strong>${l.load_id}</strong></td>
          <td>${l.origin} &rarr; ${l.destination}</td>
          <td>${l.truck_type}</td>
          <td>${l.material}</td>
          <td class="mono">${l.distance_km} (${l.chargeable_km})</td>
          <td class="mono">&#8377;${l.base_price}</td>
          <td class="mono">${l.demand_supply_ratio}</td>
          <td class="mono">${l.surge_pct}%</td>
          <td class="mono">${l.return_load_pct}%</td>
          <td class="mono">${l.backhaul_poor_pct}%</td>
          <td class="mono">${l.material_pct}%</td>
          <td class="mono"><strong>&#8377;${l.recommended_price}</strong></td>
        </tr>`).join("");

      document.querySelector("#tripsTable tbody").innerHTML = data.trips.map(t => {
        const cls = t.state === "SETTLED" ? "b-settled" : (t.state === "MATCHED" ? "b-matched" : "b-aborted");
        const s = t.settlement || {};
        return `
        <tr>
          <td class="mono"><strong>${t.id}</strong></td>
          <td class="mono">${t.truck_id}</td>
          <td><span class="badge ${cls}">${t.state}</span></td>
          <td class="mono">&#8377;${t.agreed_price}</td>
          <td class="mono">${fmt(s.detention_total ?? s.detention)}</td>
          <td class="mono">${fmt(s.toll)}</td>
          <td class="mono">${fmt(s.platform_fee)}</td>
          <td class="mono">${fmt(s.tds)}</td>
          <td class="mono"><strong>${fmt(s.carrier_payout ?? s.abort_base_compensation)}</strong></td>
          <td class="mono">${fmt(s.gst)}</td>
          <td class="mono"><strong>${fmt(s.shipper_invoice)}</strong></td>
          <td>${s.rcm_flag === undefined ? "-" : (s.rcm_flag ? "RCM" : "Regular")}</td>
        </tr>`;
      }).join("");

      document.querySelector("#rejectionsTable tbody").innerHTML = data.rejections.map(r => `
        <tr>
          <td class="mono">${r.cycle_minute}</td>
          <td class="mono">${r.load_id}</td>
          <td class="mono">${r.truck_id}</td>
          <td>${r.reasons.join(", ")}</td>
        </tr>`).join("");
    }

    async function runSamplePack() {
      await fetchJSON("/api/run-sample-pack", { method: "POST" });
      await loadState();
    }

    async function simulatePrice() {
      const payload = {
        origin: document.getElementById("simOrigin").value,
        destination: document.getElementById("simDest").value,
        truck_type: document.getElementById("simType").value,
        material: document.getElementById("simMat").value,
        extra_stops: Number(document.getElementById("simStops").value || 0),
        fuel_index_pct: Number(document.getElementById("simFuel").value || 0),
      };
      const res = await fetchJSON("/api/price-simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const box = document.getElementById("simResult");
      if (res.error) {
        box.innerHTML = `<span style="color:var(--red)"><strong>RuleError:</strong> ${res.error}</span>`;
        return;
      }
      box.innerHTML = `
        <strong>Lane:</strong> ${res.origin} &rarr; ${res.destination} (${res.distance_km} km, billable ${res.chargeable_km} km @ &#8377;${res.rate_per_km}/km)<br/>
        <strong>Base:</strong> &#8377;${res.base_price} | <strong>Demand/Supply Ratio:</strong> ${res.demand_supply_ratio} (${res.open_loads} open / ${res.available_trucks_200km} trucks)<br/>
        <strong>Modifiers:</strong> Surge ${res.surge_pct}%, Return-load ${res.return_load_pct}%, Backhaul-poor ${res.backhaul_poor_pct}%, Material ${res.material_pct}%, Fuel ${res.fuel_index_pct}%, Multi-drop &#8377;${res.multi_drop_fee}<br/>
        <strong style="color:var(--green);font-size:15px;">Recommended Price: &#8377;${res.recommended_price}</strong>
      `;
    }

    loadState();
  </script>
</body>
</html>
"""


class DashboardState:
    """Holds the live engine instance rendered and mutated by the dashboard server."""

    def __init__(self, sample_dir: Path, output_dir: Path):
        self.sample_dir = sample_dir
        self.output_dir = output_dir
        self.engine = self._build_fresh_sample_run()

    def _build_fresh_sample_run(self):
        engine = load_engine_from_csv_dir(self.sample_dir, post_loads=True)
        if (self.sample_dir / "commands.jsonl").exists():
            run_command_file(engine, self.sample_dir / "commands.jsonl", stop_on_error=True)
        export_csv_reports(engine, self.output_dir)
        conn = initialize_database(self.output_dir / "freight_exchange.db")
        try:
            FreightRepository(conn).save_engine_snapshot(engine)
        finally:
            conn.close()
        return engine

    def reset_and_run(self) -> None:
        self.engine = self._build_fresh_sample_run()

    def serialize(self) -> dict:
        cities = sorted({c for pair in self.engine.distances for c in pair})
        loads = []
        for load in sorted(self.engine.loads.values(), key=lambda x: x.id):
            if load.price:
                loads.append({k: str(v) for k, v in load.price.items()})

        trips = []
        total_freight = Decimal("0")
        total_platform = Decimal("0")
        total_tds = Decimal("0")
        settled_count = 0
        cancelled_aborted = 0

        for t in sorted(self.engine.trips.values(), key=lambda x: x.id):
            if t.state.value == "SETTLED":
                settled_count += 1
                total_freight += Decimal(str(t.settlement.get("freight", 0)))
                total_platform += Decimal(str(t.settlement.get("platform_fee", 0)))
                total_tds += Decimal(str(t.settlement.get("tds", 0)))
            elif t.state.value in {"CANCELLED", "ABORTED"}:
                cancelled_aborted += 1
            trips.append(
                {
                    "id": t.id,
                    "load_id": t.load_id,
                    "truck_id": t.truck_id,
                    "state": t.state.value,
                    "agreed_price": str(rupee(t.agreed_price)),
                    "settlement": {k: (v if isinstance(v, bool) else str(v)) for k, v in t.settlement.items()},
                }
            )

        carriers = [
            {
                "id": c.id,
                "name": c.name,
                "rating": str(c.rating),
                "second_driver": c.second_driver,
                "annual_payout": str(rupee(c.annual_payout)),
            }
            for c in sorted(self.engine.carriers.values(), key=lambda x: x.id)
        ]

        return {
            "cities": cities,
            "kpis": {
                "loads": len(self.engine.loads),
                "settled_trips": settled_count,
                "cancelled_or_aborted": cancelled_aborted,
                "total_freight": str(rupee(total_freight)),
                "total_platform_fee": str(rupee(total_platform)),
                "total_tds": str(rupee(total_tds)),
            },
            "loads": loads,
            "trips": trips,
            "carriers": carriers,
            "rejections": self.engine.rejection_records,
        }


def make_handler(state: DashboardState):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict, status: int = 200) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/":
                body = DASHBOARD_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if path == "/api/state":
                self._send_json(state.serialize())
                return
            self.send_error(404)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/run-sample-pack":
                state.reset_and_run()
                self._send_json(state.serialize())
                return
            if path == "/api/price-simulate":
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length).decode("utf-8")
                data = json.loads(raw or "{}")
                try:
                    probe = Load(
                        "SIM-LOAD",
                        "SHP-001",
                        data["origin"],
                        data["destination"],
                        Decimal("5"),
                        data["truck_type"],
                        60,
                        360,
                        material=data.get("material", "GENERAL"),
                        length_ft=Decimal("14"),
                        extra_stops=int(data.get("extra_stops", 0)),
                    )
                    price = price_load(
                        probe,
                        list(state.engine.trucks.values()),
                        list(state.engine.loads.values()) + [probe],
                        state.engine.distances,
                        state.engine.poor_cities,
                        fuel_index_pct=Decimal(str(data.get("fuel_index_pct", 0))),
                    )
                    self._send_json({k: str(v) for k, v in price.items()})
                except RuleError as exc:
                    self._send_json({"error": str(exc)}, status=400)
                return
            self.send_error(404)

        def log_message(self, format: str, *args) -> None:
            return  # Keep terminal output clean

    return Handler


def start_dashboard(
    host: str = "127.0.0.1",
    port: int = 8069,
    sample_dir: str | Path = "sample_data",
    output_dir: str | Path = "outputs",
) -> None:
    """Start the local interactive dashboard HTTP server."""
    state = DashboardState(Path(sample_dir), Path(output_dir))
    server = ThreadingHTTPServer((host, port), make_handler(state))
    print(f"T069-PS-099 Dashboard running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server.")
    finally:
        server.server_close()
