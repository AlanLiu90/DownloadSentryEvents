from __future__ import absolute_import

import six
import traceback

from functools import partial
from datetime import datetime

from sentry import eventstore
from sentry.api.base import DocSection
from sentry.api.bases.project import ProjectEndpoint
from sentry.api.serializers import EventSerializer, serialize
from sentry.models import EventAttachment
from sentry.search.utils import convert_user_tag_to_query
from sentry.utils.apidocs import scenario, attach_scenarios

CRASH_FILE_TYPES = set(["event.minidump"])

def get_crash_files(events):
    event_ids = [x.event_id for x in events if x.platform == "native"]
    rv = {}
    if event_ids:
        attachments = EventAttachment.objects.filter(event_id__in=event_ids).select_related("file")
        for attachment in attachments:
            if attachment.file.type in CRASH_FILE_TYPES:
                rv[attachment.event_id] = attachment
    return rv

class SimpleEventSerializer(EventSerializer):
    """
    Simple event serializer that renders a basic outline of an event without
    most interfaces/breadcrumbs. This can be used for basic event list queries
    where we don't need the full detail. The side effect is that, if the
    serialized events are actually SnubaEvents, we can render them without
    needing to fetch the event bodies from nodestore.

    NB it would be super easy to inadvertently add a property accessor here
    that would require a nodestore lookup for a SnubaEvent serialized using
    this serializer. You will only really notice you've done this when the
    organization event search API gets real slow.
    """

    def get_attrs(self, item_list, user):
        crash_files = get_crash_files(item_list)
        return {
            event: {"crash_file": serialize(crash_files.get(event.event_id), user=user)}
            for event in item_list
        }

    def serialize(self, obj, attrs, user):
        event = eventstore.get_event_by_id(obj.project_id, obj.event_id)

        event_dict = event.as_dict()
        if isinstance(event_dict["datetime"], datetime):
            event_dict["datetime"] = event_dict["datetime"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        stacktrace = None
        if event_dict["level"] == "error":
            try:
                raw_stacktrace = None
                if "exception" in event_dict:
                    raw_stacktrace = event_dict["exception"]["values"][0]["stacktrace"]["frames"]
                elif "threads" in event_dict:
                    raw_stacktrace = event_dict["threads"]["values"][0]["stacktrace"]["frames"]

                if raw_stacktrace is not None:
                    stacktrace = []
                    for raw_frame in raw_stacktrace:
                        module = raw_frame.get("module")
                        function = raw_frame.get("function")
                        abs_path = raw_frame.get("abs_path")
                        lineno = raw_frame.get("lineno")

                        frame = {}
                        if module is not None:
                            frame["module"] = module
                        if function is not None:
                            frame["function"] = function
                        if abs_path is not None:
                            frame["abs_path"] = abs_path
                        if lineno is not None:
                            frame["lineno"] = lineno

                        stacktrace.append(frame)
            except:
                traceback.print_exc()
                stacktrace = None

        ret = {
            "level": event_dict["level"],
            # XXX for 'message' this doesn't do the proper resolution of logentry
            # etc. that _get_legacy_message_with_meta does.
            "message": event_dict["message"],
            "tags": event_dict["tags"],
            "datetime": event_dict["datetime"],
        }

        if stacktrace is not None:
            ret["stacktrace"] = stacktrace

        return ret

class SimpleProjectEventsEndpoint(ProjectEndpoint):
    doc_section = DocSection.EVENTS

    def get(self, request, project):
        """
        List a Project's Events
        ```````````````````````

        Return a list of events bound to a project.


        :pparam string organization_slug: the slug of the organization the
                                          groups belong to.
        :pparam string project_slug: the slug of the project the groups
                                     belong to.
        """
        from sentry.api.paginator import GenericOffsetPaginator

        query = request.GET.get("query")
        conditions = []
        if query:
            conditions.append(
                [["positionCaseInsensitive", ["message", "'%s'" % (query,)]], "!=", 0]
            )

        data_fn = partial(
            eventstore.get_events,
            filter=eventstore.Filter(conditions=conditions, project_ids=[project.id]),
            referrer="api.project-events",
        )

        serializer = SimpleEventSerializer()
        return self.paginate(
            request=request,
            on_results=lambda results: serialize(results, request.user, serializer),
            paginator=GenericOffsetPaginator(data_fn=data_fn),
        )
