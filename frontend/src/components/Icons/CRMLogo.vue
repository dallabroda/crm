<template>
  <!-- Cred Hub: marca "C" da CredTech (mesma geometria de crm/public/images/logo.svg) -->
  <svg
    width="300"
    height="300"
    viewBox="0 0 512 512"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    aria-label="Cred Hub"
  >
    <defs>
      <mask :id="maskId">
        <rect width="512" height="512" fill="black" />
        <g transform="translate(12.8 12.8) scale(0.95)">
          <path
            fill="white"
            fill-rule="evenodd"
            d="M66 256a147 147 0 1 0 294 0a147 147 0 1 0 -294 0Z M149 256a147 147 0 1 0 294 0a147 147 0 1 0 -294 0Z"
          />
          <rect x="345" y="208" width="167" height="90" fill="black" />
        </g>
      </mask>
    </defs>
    <rect width="512" height="512" rx="112" fill="#111111" />
    <rect width="512" height="512" fill="#ffffff" :mask="`url(#${maskId})`" />
  </svg>
</template>
<script setup>
// one mask id per instance: the logo can appear several times on a page
const maskId = `credhub-c-${Math.random().toString(36).slice(2, 8)}`
</script>
