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
                if "exception" in event_dict:
                    exceptions = event_dict["exception"]["values"]

                    stacktrace = ""
                    for i in range(len(exceptions)):
                        exception = exceptions[i]
                        current = ""
                        if i < len(exceptions) - 1:
                            current = " ---> "

                        current = current + "%s: %s" % (exception["type"], exception["value"])
                        if i > 0:
                            current = current + "\n"

                        stacktrace = current + stacktrace

                    for i in range(len(exceptions)):
                        exception = exceptions[i]

                        if i > 0:
                            stacktrace = stacktrace + "\n   --- End of inner exception stack trace ---"

                        raw_stacktrace = exception.get("stacktrace")
                        if raw_stacktrace is not None:
                            stacktrace = stacktrace + "\n" + self.format_stackframes(raw_stacktrace["frames"])
                elif "threads" in event_dict:
                    for value in event_dict["threads"]["values"]:
                        if value.get("current", False):
                            raw_stacktrace = value.get("stacktrace")
                            if raw_stacktrace is not None:
                                stacktrace = self.format_stackframes(raw_stacktrace["frames"])
                            break
            except:
                traceback.print_exc()
                # print event_dict

                stacktrace = None

        ret = {
            "level": event_dict["level"],
            "datetime": event_dict["datetime"],
        }

        tags = event_dict.get("tags")
        if tags is not None:
            tags = { tag[0] : tag[1] for tag in tags }
            if "client-version" in tags:
                ret["client"] = "[client:%s_%s_%s]" % (tags["player-id"], tags["player-name"], tags["client-version"])
            elif "node-id" in tags:
                service_handle = tags.get("service-handle", 0)
                service_name = tags.get("service-name", "")
                ret["server"] = "[%s:%d_%s]" % (tags["node-id"], service_handle, service_name)

        if stacktrace is not None:
            ret["message"] = event_dict["message"] + "\n" + stacktrace
        else:
            ret["message"] = event_dict["message"],

        return ret

    def format_stackframes(self, frames):
        formatted_frames = ""
        for i in range(len(frames)):
            raw_frame = frames[i]
            module = raw_frame.get("module")
            function = raw_frame.get("function")
            abs_path = raw_frame.get("abs_path")
            lineno = raw_frame.get("lineno")

            frame = ""

            if module is not None and function is not None:
                frame = "   at %s.%s" % (module, function)
            if abs_path is not None and lineno is not None:
                frame = frame + " in %s:line %d" % (abs_path, lineno)

            if i > 0:
                frame = frame + "\n"

            formatted_frames = frame + formatted_frames

        return formatted_frames

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
