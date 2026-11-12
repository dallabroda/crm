import credtechMark from '@/assets/sources/credtech.svg'
import googleAdsLogo from '@/assets/sources/google-ads.svg'
import typeformLogo from '@/assets/sources/typeform.svg'
import rdStationLogo from '@/assets/sources/rd-station.svg'
import FacebookIcon from '@/components/Icons/FacebookIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'

// Logo of a lead source in the "Origem" column (Figma "Vendas · Lista · Origem
// dos leads", 1750:23623). Sources are named "<channel>: <form>" ("Site: Fale
// com a gente", "Google Ads: Consignado INSS", "Webhook: RD Station"), so the
// brand is found by name; the tool behind a webhook wins over "Webhook".
// Returns { image } (brand mark, 16px box), { component } (one-color logo) or
// { icon } (whole Lucide class name, so its CSS is generated).
const BRANDS = [
  { match: /google/, image: googleAdsLogo },
  { match: /typeform/, image: typeformLogo },
  { match: /\brd\b|rd ?station/, image: rdStationLogo },
  { match: /whats ?app/, component: WhatsAppIcon },
  { match: /facebook|instagram|\bmeta\b/, component: FacebookIcon },
  { match: /^(site|website|web form)\b|formul[aá]rio/, image: credtechMark },
  { match: /webhook|zapier|\bmake\b|\bapi\b/, icon: 'lucide-webhook' },
  { match: /indica[cç][aã]o|reference|refer[eê]ncia/, icon: 'lucide-users' },
  { match: /e-?mail/, icon: 'lucide-mail' },
  { match: /liga[cç][aã]o|cold calling|telefone|phone/, icon: 'lucide-phone' },
]

const FALLBACK = { icon: 'lucide-radio-tower' }

export function leadSourceBrand(source) {
  if (!source) return null
  const name = String(source).toLowerCase().trim()
  const brand = BRANDS.find((b) => b.match.test(name))
  if (!brand) return FALLBACK
  const { match, ...rest } = brand
  return rest
}
