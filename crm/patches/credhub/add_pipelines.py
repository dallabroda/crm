import frappe

from crm.install import add_default_pipeline, add_pipeline_indexes


def execute():
	"""Move existing stages, cards and stage history into the first pipeline."""
	pipeline = add_default_pipeline()
	frappe.db.sql(
		"update `tabCRM Deal Status` set pipeline = %s where ifnull(pipeline, '') = ''",
		pipeline,
	)
	frappe.db.sql("update `tabCRM Deal` set pipeline = %s where ifnull(pipeline, '') = ''", pipeline)
	frappe.db.sql(
		"""update `tabCRM Status Change Log` log
		join `tabCRM Deal Status` stage on stage.name = log.`from`
		set log.pipeline = stage.pipeline
		where log.parenttype = 'CRM Deal' and ifnull(log.pipeline, '') = ''"""
	)
	add_pipeline_indexes()
