import { defineStore } from 'pinia'
import { getCurrentInstance } from 'vue'

export const globalStore = defineStore('crm-global', () => {
  const app = getCurrentInstance()
  const { $dialog, $socket } = app.appContext.config.globalProperties

  let callMethod = () => {}

  function setMakeCall(value) {
    callMethod = value
  }

  // deal: the card the call is made from, so the call lands on its timeline
  function makeCall(number, deal = null) {
    callMethod(number, deal)
  }

  return {
    $dialog,
    $socket,
    makeCall,
    setMakeCall,
  }
})
