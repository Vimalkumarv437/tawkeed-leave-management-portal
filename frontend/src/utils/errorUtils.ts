/**
 * Error Parsing Utilities
 */

export function extractErrorMessage(error: any, defaultMessage: string = 'An unexpected error occurred.'): string {
  if (!error) return defaultMessage;

  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: any) => d.msg || d.message || JSON.stringify(d)).join(', ');
    }
  }

  if (error.message) return error.message;

  return defaultMessage;
}
