const HANDLE = /^@?([A-Za-z0-9_]{1,15})$/;

/** Mirror of the backend's normalize_x_input: accepts @handle, handle, or an x.com / twitter.com URL. */
export function normalizeHandle(raw: string): string | null {
  let value = raw.trim();
  if (!value) return null;
  if (/(^|\/\/|\.)(x|twitter)\.com\//i.test(value)) {
    try {
      const url = new URL(/^https?:\/\//i.test(value) ? value : `https://${value}`);
      value = url.pathname.split("/").filter(Boolean)[0] ?? "";
    } catch {
      return null;
    }
  }
  const match = HANDLE.exec(value);
  return match ? match[1] : null;
}
