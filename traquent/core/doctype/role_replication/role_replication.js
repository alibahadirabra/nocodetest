// Copyright (c) 2024, traquent Technologies and contributors
// For license information, please see license.txt

traquent.ui.form.on("Role Replication", {
	refresh(frm) {
		frm.disable_save();
		frm.page.set_primary_action(__("Replicate"), ($btn) => {
			$btn.text(__("Replicating..."));
			traquent.run_serially([
				() => traquent.dom.freeze("Replicating..."),
				() => frm.call("replicate_role"),
				() => traquent.dom.unfreeze(),
				() => traquent.msgprint(__("Replication completed.")),
				() => $btn.text(__("Replicate")),
			]);
		});
	},
});
