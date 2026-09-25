export interface Waypoint {
  id: number;
  lat: number;
  lng: number;
}

let nextId = 0;

export function addWaypoint(
  waypoints: Waypoint[],
  lat: number,
  lng: number,
): Waypoint[] {
  return [...waypoints, { id: nextId++, lat, lng }];
}

export function removeWaypoint(waypoints: Waypoint[], id: number): Waypoint[] {
  return waypoints.filter((w) => w.id !== id);
}

export function moveWaypoint(
  waypoints: Waypoint[],
  id: number,
  lat: number,
  lng: number,
): Waypoint[] {
  return waypoints.map((w) => (w.id === id ? { ...w, lat, lng } : w));
}

export function reorderWaypoint(
  waypoints: Waypoint[],
  id: number,
  direction: "up" | "down",
): Waypoint[] {
  const index = waypoints.findIndex((w) => w.id === id);
  const target = direction === "up" ? index - 1 : index + 1;

  // At boundaries, disable reorder
  if (index === -1 || target < 0 || target >= waypoints.length) {
    return waypoints;
  }

  const result = [...waypoints];
  [result[index], result[target]] = [result[target], result[index]];
  return result;
}

export function clearWaypoints(_waypoints: Waypoint[]): Waypoint[] {
  return [];
}

export function serializeWaypoints(waypoints: Waypoint[]): string {
  return JSON.stringify(
    waypoints.map(({ lat, lng }) => ({ lat, lng })),
    null,
    2,
  );
}

export function parseWaypoints(json: string): Waypoint[] {
  const raw: unknown = JSON.parse(json);
  if (!Array.isArray(raw)) {
    throw new Error("Invalid waypoints file: expected an array");
  }
  return raw.map((entry) => {
    const { lat, lng } = entry ?? {};
    if (typeof lat !== "number" || typeof lng !== "number") {
      throw new Error(
        "Invalid waypoints file: each entry needs numeric lat/lng",
      );
    }
    return { id: nextId++, lat, lng };
  });
}
