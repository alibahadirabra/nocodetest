import traquent
from traquent import _
from traquent.utils import cstr
from traquent.website.page_renderers.template_page import TemplatePage


class NotPermittedPage(TemplatePage):
	def __init__(self, path=None, http_status_code=None, exception=""):
		traquent.local.message = cstr(exception)
		super().__init__(path=path, http_status_code=http_status_code)
		self.http_status_code = 403

	def can_render(self):
		return True

	def render(self):
		action = f"/login?redirect-to={traquent.request.path}"
		if traquent.request.path.startswith("/app/") or traquent.request.path == "/app":
			action = "/login"
		traquent.local.message_title = _("Not Permitted")
		traquent.local.response["context"] = dict(
			indicator_color="red", primary_action=action, primary_label=_("Login"), fullpage=True
		)
		self.set_standard_path("message")
		return super().render()
