// Calendar dates must follow the station's local day. `toISOString()` is in
// UTC and returns yesterday's date between 00:00 and 03:00 in Madagascar.
export function localIsoDate(value: Date = new Date()): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function daysAgo(days: number, from: Date = new Date()): Date {
  const result = new Date(from)
  result.setDate(result.getDate() - days)
  return result
}
