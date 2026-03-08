export function formatEur(value: number | null): string {
  if (value === null) return "N/A";
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatSurface(value: number | null): string {
  if (value === null) return "N/A";
  return `${new Intl.NumberFormat("fr-FR").format(value)} m\u00B2`;
}

export function formatDate(value: string | null): string {
  if (!value) return "N/A";
  return new Intl.DateTimeFormat("fr-FR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(value));
}
