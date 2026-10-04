/**
 * Date Utilities
 */

export function formatDate(dateString?: string | null): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return isNaN(date.getTime())
    ? dateString
    : date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
}

export function formatDateTime(dateTimeString?: string | null): string {
  if (!dateTimeString) return '-';
  const date = new Date(dateTimeString);
  return isNaN(date.getTime())
    ? dateTimeString
    : date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
}

export function isWeekend(date: Date): boolean {
  const day = date.getDay();
  return day === 0 || day === 6; // Sunday = 0, Saturday = 6
}
