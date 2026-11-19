import type { Place } from "./api";

export interface Origin {
  lat: number;
  lon: number;
  label: string;
}

/** Where the user is: device GPS, else the saved default location, else an error. */
export function getOrigin(fallback: Place | null | undefined): Promise<Origin> {
  const useFallback = (reason: string): Origin => {
    if (fallback) return { lat: fallback.lat, lon: fallback.lon, label: "your saved default location" };
    throw new Error(reason);
  };

  if (!("geolocation" in navigator)) return Promise.resolve().then(() => useFallback("This browser can't share your location."));

  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          label: `your location (within ${Math.round(pos.coords.accuracy)} m)`,
        }),
      (err) => {
        try {
          resolve(
            useFallback(
              err.code === err.PERMISSION_DENIED
                ? "Location access was blocked. Allow location for this site in your browser settings."
                : "Couldn't find your location. Try again outdoors or near a window.",
            ),
          );
        } catch (e) {
          reject(e);
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 },
    );
  });
}
