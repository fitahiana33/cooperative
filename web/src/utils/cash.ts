// Closing a cash desk records the cash actually counted; any difference with
// the expected balance is kept as a discrepancy by the API.
export function askCountedAmount(expected: number | string | null | undefined): number | null {
  const suggestion = Number(expected ?? 0)
  const answer = window.prompt(
    `Montant compté dans la caisse (solde attendu : ${suggestion.toLocaleString('fr-FR')} Ar).\nSaisissez le montant réellement présent :`,
    String(suggestion),
  )
  if (answer === null) return null
  const value = Number(answer.replace(/\s/g, '').replace(',', '.'))
  if (!Number.isFinite(value) || value < 0) {
    window.alert('Montant invalide.')
    return null
  }
  return value
}

export function discrepancyMessage(ecart: number | string | null | undefined): string {
  const value = Number(ecart ?? 0)
  if (!value) return 'Caisse clôturée, sans écart.'
  return `Caisse clôturée. Écart de ${value > 0 ? '+' : ''}${value.toLocaleString('fr-FR')} Ar (${value > 0 ? 'excédent' : 'manque'}).`
}
