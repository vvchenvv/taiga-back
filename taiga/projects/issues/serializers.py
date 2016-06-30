# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from taiga.base.api import serializers
from taiga.base.fields import PgArrayField
from taiga.base.neighbors import NeighborsSerializerMixin

from taiga.mdrender.service import render as mdrender
from taiga.projects.mixins.serializers import ListOwnerExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import ListAssignedToExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import ListStatusExtraInfoSerializerMixin
from taiga.projects.notifications.mixins import EditableWatchedResourceModelSerializer
from taiga.projects.notifications.mixins import WatchedResourceModelSerializer
from taiga.projects.notifications.validators import WatchersValidator
from taiga.projects.tagging.fields import TagsAndTagsColorsField
from taiga.projects.serializers import BasicIssueStatusSerializer
from taiga.projects.validators import ProjectExistsValidator
from taiga.projects.votes.mixins.serializers import VoteResourceSerializerMixin

from taiga.users.serializers import UserBasicInfoSerializer

from . import models

import serpy


class IssueListSerializer(VoteResourceSerializerMixin, WatchedResourceModelSerializer,
                          ListOwnerExtraInfoSerializerMixin, ListAssignedToExtraInfoSerializerMixin,
                          ListStatusExtraInfoSerializerMixin, serializers.LightSerializer):
    id = serpy.Field()
    ref = serpy.Field()
    severity = serpy.Field(attr="severity_id")
    priority = serpy.Field(attr="priority_id")
    type = serpy.Field(attr="type_id")
    milestone = serpy.Field(attr="milestone_id")
    project = serpy.Field(attr="project_id")
    created_date = serpy.Field()
    modified_date = serpy.Field()
    finished_date = serpy.Field()
    subject = serpy.Field()
    external_reference = serpy.Field()
    version = serpy.Field()
    watchers = serpy.Field()
    tags = serpy.Field()
    is_closed = serpy.Field()


class IssueSerializer(IssueListSerializer):
    comment = serpy.MethodField()
    generated_user_stories = serpy.MethodField()
    blocked_note_html = serpy.MethodField()
    description_html = serpy.MethodField()

    def get_comment(self, obj):
        # NOTE: This method and field is necessary to historical comments work
        return ""

    def get_generated_user_stories(self, obj):
        assert hasattr(obj, "generated_user_stories_attr"), "instance must have a generated_user_stories_attr attribute"
        return obj.generated_user_stories_attr

    def get_blocked_note_html(self, obj):
        return mdrender(obj.project, obj.blocked_note)

    def get_description_html(self, obj):
        return mdrender(obj.project, obj.description)


class IssueNeighborsSerializer(NeighborsSerializerMixin, IssueSerializer):
    def serialize_neighbor(self, neighbor):
        if neighbor:
            return NeighborIssueSerializer(neighbor).data
        return None


class NeighborIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Issue
        fields = ("id", "ref", "subject")
        depth = 0


class IssuesBulkSerializer(ProjectExistsValidator, serializers.Serializer):
    project_id = serializers.IntegerField()
    bulk_issues = serializers.CharField()
