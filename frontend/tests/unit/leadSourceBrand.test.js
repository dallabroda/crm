import { describe, it, expect } from 'vitest'
import { leadSourceBrand } from '@/utils/leadSourceBrand'

describe('leadSourceBrand', () => {
  it('finds the brand of the Figma sources', () => {
    expect(leadSourceBrand('Google Ads: Consignado INSS').image).toBeTruthy()
    expect(leadSourceBrand('Typeform: Simulação').image).toBeTruthy()
    expect(leadSourceBrand('Site: Fale com a gente').image).toBeTruthy()
    expect(leadSourceBrand('Webhook: Zapier')).toEqual({
      icon: 'lucide-webhook',
    })
  })

  it('prefers the tool behind a webhook', () => {
    expect(leadSourceBrand('Webhook: RD Station')).toEqual(
      leadSourceBrand('RD Station'),
    )
    expect(leadSourceBrand('Webhook: RD Station').image).toBeTruthy()
  })

  it('falls back to a neutral icon and skips empty sources', () => {
    expect(leadSourceBrand('Exhibition')).toEqual({
      icon: 'lucide-radio-tower',
    })
    expect(leadSourceBrand('')).toBeNull()
  })
})
