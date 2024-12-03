traquent.route_history_queue = [];
const routes_to_skip = ["Form", "social", "setup-wizard", "recorder"];

const save_routes = traquent.utils.debounce(() => {
	if (traquent.session.user === "Guest") return;
	const routes = traquent.route_history_queue;
	if (!routes.length) return;

	traquent.route_history_queue = [];

	traquent
		.xcall("traquent.desk.doctype.route_history.route_history.deferred_insert", {
			routes: routes,
		})
		.catch(() => {
			traquent.route_history_queue.concat(routes);
		});
}, 10000);

traquent.router.on("change", () => {
	const route = traquent.get_route();
	if (is_route_useful(route)) {
		traquent.route_history_queue.push({
			creation: traquent.datetime.now_datetime(),
			route: traquent.get_route_str(),
		});

		save_routes();
	}
});

function is_route_useful(route) {
	if (!route[1]) {
		return false;
	} else if ((route[0] === "List" && !route[2]) || routes_to_skip.includes(route[0])) {
		return false;
	} else {
		return true;
	}
}
