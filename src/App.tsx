import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Clock3,
  Fan,
  Gauge,
  LayoutDashboard,
  MapPin,
  Menu,
  Plus,
  Search,
  Settings2,
  SlidersHorizontal,
  Sparkles,
  Thermometer,
  X,
} from "lucide-react";
import { api, type Device, type Overview, type Project, type Trend } from "./api";

type Page = "dashboard" | "projects" | "devices" | "automations";

const pageLabels: Record<Page, string> = {
  dashboard: "Overview",
  projects: "Projects",
  devices: "Devices & points",
  automations: "Sequences",
};

function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [trend, setTrend] = useState<Trend | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  async function loadStudio() {
    setLoading(true);
    setError("");
    try {
      const [nextOverview, nextProjects, nextDevices] = await Promise.all([
        api.overview(),
        api.projects(),
        api.devices(),
      ]);
      setOverview(nextOverview);
      setProjects(nextProjects);
      setDevices(nextDevices);
      const firstPoint = nextDevices[0]?.points[0];
      setTrend(firstPoint ? await api.trend(firstPoint.id) : null);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Could not connect to the local BMS service.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadStudio();
    const interval = window.setInterval(() => void loadStudio(), 30_000);
    return () => window.clearInterval(interval);
  }, []);

  const primaryProject = projects[0];
  const todayLabel = new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(new Date()).toUpperCase();

  async function handleProjectCreated() {
    setWizardOpen(false);
    setPage("projects");
    await loadStudio();
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNavOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><Activity size={19} strokeWidth={2.5} /></div>
          <span>fieldnote<span className="brand-dot">.</span></span>
          <button className="icon-button mobile-close" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation"><X size={18} /></button>
        </div>
        <div className="workspace-switcher">
          <div className="workspace-icon">N</div>
          <div className="workspace-name"><strong>{primaryProject?.name ?? "Local workspace"}</strong><small>LOCAL STUDIO</small></div>
          <ChevronDown size={15} />
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <nav className="primary-nav" aria-label="Main navigation">
          <NavItem icon={<LayoutDashboard size={17} />} label="Overview" active={page === "dashboard"} onClick={() => setPage("dashboard")} />
          <NavItem icon={<MapPin size={17} />} label="Projects" active={page === "projects"} onClick={() => setPage("projects")} count={projects.length} />
          <NavItem icon={<Gauge size={17} />} label="Devices & points" active={page === "devices"} onClick={() => setPage("devices")} />
          <NavItem icon={<SlidersHorizontal size={17} />} label="Sequences" active={page === "automations"} onClick={() => setPage("automations")} />
        </nav>
        <div className="nav-caption integrations-caption">INTEGRATIONS</div>
        <div className="integration-list">
          <span className="integration-dot connected" /> Simulator <span className="connection-state">Connected</span>
          <div className="integration-coming"><span className="integration-dot pending" /> BACnet / Modbus <span className="soon">Planned</span></div>
        </div>
        <div className="sidebar-bottom">
          <div className="help-card"><div className="help-icon"><CircleHelp size={16} /></div><div><strong>Need a hand?</strong><span>Explore the quick guide</span></div><ChevronRight size={15} /></div>
          <div className="profile-row"><div className="avatar">S</div><div className="profile-name"><strong>Studio operator</strong><span>Local session</span></div><Settings2 size={17} /></div>
        </div>
      </aside>

      {mobileNavOpen && <button className="nav-backdrop" onClick={() => setMobileNavOpen(false)} aria-label="Close menu" />}
      <main className="main-content">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setMobileNavOpen(true)} aria-label="Open navigation"><Menu size={19} /></button>
          <div className="breadcrumbs"><span>Workspace</span><ChevronRight size={14} /><strong>{pageLabels[page]}</strong></div>
          <div className="topbar-actions">
            <div className="local-badge"><span />Local mode</div>
            <button className="icon-button search-button" aria-label="Search"><Search size={17} /></button>
            <button className="icon-button notification-button" aria-label="Notifications"><Bell size={17} /><i /></button>
            <div className="top-avatar">S</div>
          </div>
        </header>
        {error && <div className="error-banner"><AlertTriangle size={16} /><span>Local API unavailable: {error}</span><button onClick={() => void loadStudio()}>Retry</button></div>}
        {loading && !overview ? (
          <div className="loading-state"><div className="spinner" />Connecting to your local studio…</div>
        ) : (
          <>
            {page === "dashboard" && <Dashboard overview={overview} trend={trend} project={primaryProject} onCreate={() => setWizardOpen(true)} onNavigate={setPage} />}
            {page === "projects" && <Projects projects={projects} onCreate={() => setWizardOpen(true)} />}
            {page === "devices" && <Devices devices={devices} />}
            {page === "automations" && <Sequences />}
          </>
        )}
      </main>
      {wizardOpen && <ProjectWizard onClose={() => setWizardOpen(false)} onCreated={handleProjectCreated} />}
    </div>
  );
}

function NavItem({ icon, label, active, onClick, count }: { icon: ReactNode; label: string; active: boolean; onClick: () => void; count?: number }) {
  return <button className={`nav-item ${active ? "active" : ""}`} onClick={onClick}>{icon}<span>{label}</span>{count !== undefined && <span className="nav-count">{count}</span>}</button>;
}

function Dashboard({ overview, trend, project, onCreate, onNavigate }: { overview: Overview | null; trend: Trend | null; project?: Project; onCreate: () => void; onNavigate: (page: Page) => void }) {
  const chart = useMemo(() => {
    if (!trend?.points.length) return "";
    const values = trend.points.map((point) => point.value);
    const min = Math.min(...values) - 0.8;
    const max = Math.max(...values) + 0.8;
    return values.map((value, index) => `${(index / (values.length - 1)) * 100},${36 - ((value - min) / (max - min)) * 32}`).join(" ");
  }, [trend]);

  return (
    <div className="page-wrap">
      <section className="welcome-row">
        <div><div className="eyebrow"><span className="eyebrow-line" /> {todayLabel}</div><h1>Good morning, operator <span className="wave">✳</span></h1><p>Here’s what’s happening across your building today.</p></div>
        <button className="button button-primary" onClick={onCreate}><Plus size={17} /> New project</button>
      </section>

      <section className="site-strip">
        <div className="site-symbol"><MapPin size={19} /></div>
        <div className="site-info"><strong>{project?.site_name ?? "No site configured"}</strong><span>{project?.location ?? "Create a project to get started"}</span></div>
        <span className="site-divider" />
        <span className="site-live"><i /> Simulation running</span>
        <button className="text-button site-details" onClick={() => onNavigate("projects")}>Site details <ChevronRight size={15} /></button>
        <div className="site-weather"><span className="weather-sun">☼</span><strong>12°</strong><span>Outside</span></div>
      </section>

      <div className="section-heading"><div><h2>Building at a glance</h2><span>Live simulated data · refreshes every 30 seconds</span></div><button className="subtle-select"><Clock3 size={14} /> Last 24 hours <ChevronDown size={14} /></button></div>
      <section className="metric-grid">
        <MetricCard icon={<Fan size={17} />} label="Equipment" value={overview?.equipment_count ?? 0} unit="units" detail="Across all zones" tint="mint" trend="up" />
        <MetricCard icon={<Activity size={17} />} label="Points monitored" value={overview?.point_count ?? 0} unit="points" detail="All signals healthy" tint="blue" trend="stable" />
        <MetricCard icon={<AlertTriangle size={17} />} label="Active alarms" value={overview?.active_alarms.length ?? 0} unit="alarms" detail="No critical events" tint="amber" trend="clear" />
        <MetricCard icon={<MapPin size={17} />} label="Projects" value={overview?.project_count ?? 0} unit="sites" detail="Local workspace" tint="lavender" trend="stable" />
      </section>

      <section className="content-grid">
        <article className="panel trend-panel">
          <div className="panel-heading"><div><div className="panel-title-icon mint"><Thermometer size={17} /></div><div><h3>Supply air temperature</h3><span>AHU-01 · North Wing</span></div></div><button className="icon-button more-button" aria-label="More trend options"><ChevronDown size={16} /></button></div>
          <div className="trend-reading"><strong>{trend?.points[trend.points.length - 1]?.value.toFixed(1) ?? "—"}<small>°C</small></strong><span className="positive-change"><ArrowDownRight size={15} /> 0.4° <em>vs yesterday</em></span></div>
          <div className="chart-wrap">
            <div className="chart-y-labels"><span>22°</span><span>20°</span><span>18°</span><span>16°</span></div>
            <div className="chart-area">
              <div className="chart-grid-line line-1" /><div className="chart-grid-line line-2" /><div className="chart-grid-line line-3" /><div className="chart-grid-line line-4" />
              {chart && <svg className="trend-svg" viewBox="0 0 100 40" preserveAspectRatio="none" aria-label="24-hour supply air temperature trend"><defs><linearGradient id="trend-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#4c9f76" stopOpacity=".2" /><stop offset="100%" stopColor="#4c9f76" stopOpacity="0" /></linearGradient></defs><polygon points={`0,40 ${chart} 100,40`} fill="url(#trend-fill)" /><polyline points={chart} fill="none" stroke="#438e69" strokeWidth=".55" vectorEffect="non-scaling-stroke" strokeLinejoin="round" strokeLinecap="round" /></svg>}
              <div className="chart-x-labels"><span>12 am</span><span>6 am</span><span>12 pm</span><span>6 pm</span><span>Now</span></div>
            </div>
          </div>
          <div className="chart-footer"><span><i className="legend-dot" /> Supply temperature</span><span>Last 24 hours</span></div>
        </article>

        <article className="panel equipment-panel">
          <div className="panel-heading"><div><div className="panel-title-icon blue"><Fan size={17} /></div><div><h3>Equipment status</h3><span>Across your active project</span></div></div><button className="text-button" onClick={() => onNavigate("devices")}>View all <ChevronRight size={15} /></button></div>
          {overview?.latest_readings.length ? (
            <div className="equipment-list">{overview.latest_readings.slice(0, 4).map((reading, index) => <div className="equipment-row" key={reading.id}><div className={`equipment-icon equipment-icon-${index % 3}`}>{index === 0 ? <Thermometer size={16} /> : index === 1 ? <Activity size={16} /> : <Gauge size={16} />}</div><div className="equipment-label"><strong>{reading.name}</strong><span>{reading.id.includes("outdoor") ? "Weather station" : "AHU-01 · North Wing"}</span></div><div className="equipment-value"><strong>{reading.value}{reading.unit === "°C" ? "°" : ` ${reading.unit}`}</strong><span className="healthy-dot" /> <small>Normal</small></div></div>)}</div>
          ) : <EmptyState text="Add a simulated device to see equipment readings." />}
          <button className="add-device-row" onClick={() => onNavigate("devices")}><Plus size={15} /> Explore devices and points</button>
        </article>
      </section>

      <section className="bottom-grid">
        <article className="panel alarm-panel">
          <div className="panel-heading"><div><div className="panel-title-icon amber"><Bell size={16} /></div><div><h3>Recent alarms</h3><span>Events that may need attention</span></div></div><span className="count-pill">{overview?.active_alarms.length ?? 0}</span></div>
          {overview?.active_alarms.length ? overview.active_alarms.map((alarm) => <div className="alarm-item" key={alarm.id}><span className="alarm-severity" /><div><strong>{alarm.name}</strong><span>{alarm.equipment_name} · {alarm.value} {alarm.unit}</span></div><small>Active</small></div>) : <div className="all-clear"><div className="all-clear-icon"><Activity size={17} /></div><div><strong>All quiet for now</strong><span>No active alarms in your local simulation.</span></div><span className="clear-badge">All clear</span></div>}
        </article>
        <article className="panel automation-panel">
          <div className="panel-heading"><div><div className="panel-title-icon lavender"><Sparkles size={16} /></div><div><h3>Sequences & schedules</h3><span>Configured for this project</span></div></div><button className="text-button" onClick={() => onNavigate("automations")}>Explore <ChevronRight size={15} /></button></div>
          <div className="schedule-card"><div className="schedule-icon"><Clock3 size={16} /></div><div><strong>Weekday occupancy</strong><span>Mon–Fri · 07:00–19:00</span></div><span className="enabled-pill">Enabled</span></div>
          <div className="schedule-card sequence-card"><div className="schedule-icon sequence-icon"><SlidersHorizontal size={16} /></div><div><strong>Supply air reset</strong><span>Draft sequence · simulation only</span></div><span className="draft-pill">Draft</span></div>
        </article>
      </section>
      <footer className="page-footer"><span>FIELDNOTE BMS STUDIO <b>·</b> LOCAL-FIRST BY DESIGN</span><span>Read-only monitoring <i /> No live control enabled</span></footer>
    </div>
  );
}

function MetricCard({ icon, label, value, unit, detail, tint, trend }: { icon: ReactNode; label: string; value: number; unit: string; detail: string; tint: string; trend: "up" | "stable" | "clear" }) {
  return <article className="metric-card"><div className="metric-top"><span className={`metric-icon ${tint}`}>{icon}</span><span className={`trend-chip ${trend}`}>{trend === "up" ? <><ArrowUpRight size={13} /> Live</> : trend === "clear" ? "Clear" : "Steady"}</span></div><div className="metric-label">{label}</div><div className="metric-number">{value}<span>{unit}</span></div><div className="metric-detail">{detail}</div></article>;
}

function Projects({ projects, onCreate }: { projects: Project[]; onCreate: () => void }) {
  return <div className="page-wrap inner-page"><section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-line" /> YOUR WORKSPACE</div><h1>Projects</h1><p>Keep your sites, zones, and equipment organized in one local workspace.</p></div><button className="button button-primary" onClick={onCreate}><Plus size={17} /> New project</button></section>
    {projects.length ? <div className="project-grid">{projects.map((project) => <article className="project-card" key={project.id}><div className="project-card-top"><div className="project-building-icon"><MapPin size={20} /></div><span className="project-status"><i /> Local project</span></div><h3>{project.name}</h3><p><MapPin size={14} />{project.location}</p><div className="project-meta"><span>{project.building_type}</span><span>{project.equipment_count} equipment</span><span>{project.point_count} points</span></div><div className="project-card-footer"><span>Simulation adapter</span><button className="icon-button" aria-label={`Open ${project.name}`}><ChevronRight size={17} /></button></div></article>)}</div> : <EmptyState text="Your projects will appear here." action={<button className="button button-primary" onClick={onCreate}><Plus size={16} /> Create your first project</button>} />}
    <div className="data-note"><Activity size={15} /><span>Your project data stays on this device in a local SQLite database.</span></div>
  </div>;
}

function Devices({ devices }: { devices: Device[] }) {
  return <div className="page-wrap inner-page"><section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-line" /> LIVE MONITORING</div><h1>Devices & points</h1><p>Read-only view of simulated equipment and its monitored points.</p></div><span className="read-only-pill"><span /> Read-only</span></section>
    {devices.length ? <div className="device-stack">{devices.map((device) => <article className="panel device-card" key={device.id}><div className="device-card-heading"><div className="device-main-icon"><Fan size={18} /></div><div><h3>{device.name}</h3><span>{device.site_name} <b>·</b> {device.zone_name} <b>·</b> {device.equipment_type}</span></div><span className="adapter-tag"><i /> {device.adapter}</span></div><div className="points-table"><div className="points-header"><span>POINT</span><span>TYPE</span><span>VALUE</span><span>QUALITY</span></div>{device.points.map((point) => <div className="point-row" key={point.id}><div><strong>{point.name}</strong><small>{point.id}</small></div><span className="point-type">{point.point_type.replace("-", " ")}</span><strong className="point-value">{point.value}{point.unit === "°C" ? "°C" : ` ${point.unit}`}</strong><span className="quality-good"><i /> {point.quality}</span></div>)}</div></article>)}</div> : <EmptyState text="No equipment is connected to this project yet." />}
    <div className="read-only-note"><AlertTriangle size={16} /><span><strong>Live writes are disabled.</strong> Device control and protocol write operations are not available in this version.</span></div>
  </div>;
}

function Sequences() {
  return <div className="page-wrap inner-page"><section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-line" /> AUTOMATION DESIGN</div><h1>Sequences & schedules</h1><p>Review the starter schedule and keep sequence drafts safely in simulation.</p></div><span className="read-only-pill"><Sparkles size={14} /> Draft mode</span></section>
    <div className="automation-callout"><div className="callout-icon"><Sparkles size={18} /></div><div><strong>Designed for safe iteration</strong><p>Sequence execution is not enabled. Future AI-assisted drafts will be structured, validated, and simulated before an operator can apply them.</p></div></div>
    <div className="sequence-layout"><article className="panel sequence-list-panel"><div className="panel-heading"><div><div className="panel-title-icon blue"><Clock3 size={17} /></div><div><h3>Schedules</h3><span>Occupancy and operating hours</span></div></div><span className="enabled-pill">1 enabled</span></div><div className="schedule-card"><div className="schedule-icon"><Clock3 size={16} /></div><div><strong>Weekday occupancy</strong><span>Mon–Fri · 07:00–19:00</span></div><span className="enabled-pill">Enabled</span></div></article>
      <article className="panel sequence-list-panel"><div className="panel-heading"><div><div className="panel-title-icon lavender"><SlidersHorizontal size={17} /></div><div><h3>Sequence drafts</h3><span>Not executed on live equipment</span></div></div><span className="draft-pill">1 draft</span></div><div className="schedule-card sequence-card"><div className="schedule-icon sequence-icon"><SlidersHorizontal size={16} /></div><div><strong>Supply air reset</strong><span>AHU-01 · simulation only</span></div><span className="draft-pill">Draft</span></div></article>
    </div>
  </div>;
}

function ProjectWizard({ onClose, onCreated }: { onClose: () => void; onCreated: () => Promise<void> }) {
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [buildingType, setBuildingType] = useState("Office");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async   function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createProject({ name, location, building_type: buildingType });
      await onCreated();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not create project.");
    } finally {
      setSaving(false);
    }
  }

  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><section className="wizard-modal" role="dialog" aria-modal="true" aria-labelledby="wizard-title"><div className="wizard-top"><div className="wizard-step"><span>01</span> PROJECT SETUP</div><button className="icon-button" onClick={onClose} aria-label="Close project wizard"><X size={18} /></button></div><div className="wizard-progress"><i /></div><div className="wizard-content"><div className="wizard-illustration"><MapPin size={22} /></div><h2 id="wizard-title">Start a new project</h2><p>Set up a local project workspace. You can add zones, equipment, and points next.</p><form onSubmit={submit}><label htmlFor="project-name">Project name</label><input id="project-name" autoFocus required minLength={2} maxLength={100} placeholder="e.g. Northwind Workspace" value={name} onChange={(event) => setName(event.target.value)} /><label htmlFor="project-location">Site location</label><input id="project-location" required minLength={2} maxLength={120} placeholder="City, region" value={location} onChange={(event) => setLocation(event.target.value)} /><label htmlFor="building-type">Building type</label><div className="select-wrap"><select id="building-type" value={buildingType} onChange={(event) => setBuildingType(event.target.value)}><option>Office</option><option>Residential</option><option>Education</option><option>Healthcare</option><option>Retail</option><option>Industrial</option><option>Other</option></select><ChevronDown size={15} /></div>{error && <div className="form-error"><AlertTriangle size={14} />{error}</div>}<div className="wizard-note"><Activity size={14} /><span>Created locally. No cloud connection required.</span></div><div className="wizard-actions"><button type="button" className="button button-quiet" onClick={onClose}>Cancel</button><button type="submit" className="button button-primary" disabled={saving}>{saving ? "Creating…" : "Create project"} <ChevronRight size={16} /></button></div></form></div></section></div>;
}

function EmptyState({ text, action }: { text: string; action?: ReactNode }) {
  return <div className="empty-state"><div className="empty-icon"><Activity size={19} /></div><p>{text}</p>{action}</div>;
}

export default App;
