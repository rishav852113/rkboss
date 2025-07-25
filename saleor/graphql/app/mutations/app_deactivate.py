import graphene

from ....app import models
from ....permission.enums import AppPermission
from ....webhook.event_types import WebhookEventAsyncType
from ...core.mutations import DeprecatedModelMutation
from ...core.types import AppError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import App


class AppDeactivate(DeprecatedModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of app to deactivate.", required=True)

    class Meta:
        description = "Deactivate the app."
        model = models.App
        object_type = App
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.APP_STATUS_CHANGED,
                description="An app was deactivated.",
            ),
        ]

    @classmethod
    def perform_mutation(cls, _root, info, /, *, id):  # type: ignore[override]
        qs = models.App.objects.filter(removed_at__isnull=True)
        app = cls.get_instance(
            info,
            id=id,
            qs=qs,
        )
        app.is_active = False
        cls.save(info, app, None)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.app_status_changed, app)
        return cls.success_response(app)
