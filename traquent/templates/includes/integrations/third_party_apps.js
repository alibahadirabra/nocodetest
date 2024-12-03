traquent.ready(() => {
	$(".btn-delete-app").on("click", function(event) {
		traquent.call({
			method:"traquent.www.third_party_apps.delete_client",
			args: {"client_id": $(this).data("client_id"),
			}
		}).done(r => location.href="/third_party_apps");
	});
});
