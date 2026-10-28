export class FCRMNote {
  onRender() {
    // only cards (and old leads) have a page to open; notes of an organization
    // or a contact are written on its own page (credtech#214)
    let pages = { 'CRM Deal': __('Card'), 'CRM Lead': __('Lead') }
    if (pages[this.doc.reference_doctype] && this.doc.reference_docname) {
      let label = pages[this.doc.reference_doctype]

      this.actions = [
        {
          name: 'Redirect Action',
          label: __('Open {0}', [label]),
          onClick: (close) => {
            if (!this.doc.reference_docname) return
            let name =
              this.doc.reference_doctype == 'CRM Deal' ? 'Deal' : 'Lead'
            let params = { leadId: this.doc.reference_docname }
            if (name == 'Deal') {
              params = { dealId: this.doc.reference_docname }
            }
            this.router.push({ name: name, params: params })
            close?.()
          },
        },
      ]
    }
  }
}
