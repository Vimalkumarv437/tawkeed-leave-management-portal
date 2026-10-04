/**
 * Cookie Management Utilities for Frontend Cookie Storage
 */

export function getCookie(name: string): string | null {
  const nameEQ = `${encodeURIComponent(name)}=`;
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') {
      c = c.substring(1, c.length);
    }
    if (c.indexOf(nameEQ) === 0) {
      return decodeURIComponent(c.substring(nameEQ.length, c.length));
    }
  }
  return null;
}

export function setCookie(name: string, value: string, days: number = 7): void {
  const d = new Date();
  d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
  const expires = `expires=${d.toUTCString()}`;
  const isHttps = window.location.protocol === 'https:';
  const sameSite = isHttps ? 'SameSite=None; Secure' : 'SameSite=Lax';
  document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; ${expires}; path=/; ${sameSite}`;
}

export function deleteCookie(name: string): void {
  const isHttps = window.location.protocol === 'https:';
  const sameSite = isHttps ? 'SameSite=None; Secure' : 'SameSite=Lax';
  document.cookie = `${encodeURIComponent(name)}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; ${sameSite}`;
}
