export interface Point {
  id: string;
  name: string;
  value: number;
  unit: string;
  point_type: string;
  quality: string;
  observed_at: string;
}

export interface Device {
  id: number;
  name: string;
  equipment_type: string;
  adapter: string;
  zone_name: string;
  site_name: string;
  points: Point[];
}

export interface Project {
  id: number;
  name: string;
  building_type: string;
  site_name: string;
  location: string;
  equipment_count: number;
  point_count: number;
}

export interface Overview {
  project_count: number;
  equipment_count: number;
  point_count: number;
  active_alarms: Array<{
    id: string;
    name: string;
    value: number;
    unit: string;
    equipment_name: string;
  }>;
  latest_readings: Point[];
}

export interface Trend {
  point_id: string;
  name: string;
  unit: string;
  points: Array<{ time: string; value: number }>;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  overview: () => request<Overview>("/api/overview"),
  devices: () => request<Device[]>("/api/devices"),
  projects: () => request<Project[]>("/api/projects"),
  createProject: (payload: {
    name: string;
    location: string;
    building_type: string;
  }) =>
    request<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  trend: (pointId: string) =>
    request<Trend>(`/api/trends/${encodeURIComponent(pointId)}`),
};
