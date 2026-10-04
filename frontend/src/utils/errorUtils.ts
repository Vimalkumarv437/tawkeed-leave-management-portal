/**
 * Error Parsing Utilities
 */

export function extractErrorMessage(error: unknown, defaultMessage: string = 'An unexpected error occurred.'): string {
  if (!error) return defaultMessage;

  const errObj = error as { response?: { data?: { detail?: unknown } }; message?: string };

  if (errObj.response?.data?.detail) {
    const detail = errObj.response.data.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: Record<string, unknown>) => (d?.msg || d?.message || JSON.stringify(d)) as string).join(', ');
    }
  }

  if (errObj.message) return errObj.message;

  return defaultMessage;
}
