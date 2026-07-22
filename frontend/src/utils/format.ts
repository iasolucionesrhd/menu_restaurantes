export function formatMoney(value: string | number): string {
  const n = typeof value === "string" ? Number(value) : value;
  return `₡${n.toFixed(2)}`;
}

export function formatTranscurrido(desde: string): string {
  const minutos = Math.max(0, Math.floor((Date.now() - new Date(desde).getTime()) / 60000));
  if (minutos < 60) return `${minutos} min`;
  const horas = Math.floor(minutos / 60);
  return `${horas}h ${minutos % 60}min`;
}
