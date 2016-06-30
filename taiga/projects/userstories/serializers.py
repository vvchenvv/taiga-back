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

from collections import ChainMap

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from taiga.base.api import serializers
from taiga.base.api.utils import get_object_or_404
from taiga.base.neighbors import NeighborsSerializerMixin
from taiga.base.utils import json

from taiga.mdrender.service import render as mdrender
from taiga.projects.attachments.serializers import ListBasicAttachmentsInfoSerializerMixin
from taiga.projects.milestones.validators import MilestoneExistsValidator
from taiga.projects.mixins.serializers import ListOwnerExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import ListAssignedToExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import ListStatusExtraInfoSerializerMixin
from taiga.projects.models import Project, UserStoryStatus
from taiga.projects.notifications.mixins import WatchedResourceModelSerializer
from taiga.projects.serializers import BasicUserStoryStatusSerializer
from taiga.projects.userstories.validators import UserStoryExistsValidator
from taiga.projects.validators import ProjectExistsValidator, UserStoryStatusExistsValidator
from taiga.projects.votes.mixins.serializers import VoteResourceSerializerMixin

from taiga.users.serializers import UserBasicInfoSerializer
from taiga.users.serializers import ListUserBasicInfoSerializer
from taiga.users.services import get_photo_or_gravatar_url
from taiga.users.services import get_big_photo_or_gravatar_url

from . import models

import serpy


class ListOriginIssueSerializer(serializers.LightSerializer):
    id = serpy.Field()
    ref = serpy.Field()
    subject = serpy.Field()

    def to_value(self, instance):
        if instance is None:
            return None

        return super().to_value(instance)


class UserStoryListSerializer(VoteResourceSerializerMixin, WatchedResourceModelSerializer,
        ListOwnerExtraInfoSerializerMixin, ListAssignedToExtraInfoSerializerMixin,
        ListStatusExtraInfoSerializerMixin, ListBasicAttachmentsInfoSerializerMixin,
        serializers.LightSerializer):

    id = serpy.Field()
    ref = serpy.Field()
    milestone = serpy.Field(attr="milestone_id")
    milestone_slug = serpy.MethodField()
    milestone_name = serpy.MethodField()
    project = serpy.Field(attr="project_id")
    is_closed = serpy.Field()
    points = serpy.MethodField()
    backlog_order = serpy.Field()
    sprint_order = serpy.Field()
    kanban_order = serpy.Field()
    created_date = serpy.Field()
    modified_date = serpy.Field()
    finish_date = serpy.Field()
    subject = serpy.Field()
    client_requirement = serpy.Field()
    team_requirement = serpy.Field()
    generated_from_issue = serpy.Field(attr="generated_from_issue_id")
    external_reference = serpy.Field()
    tribe_gig = serpy.Field()
    version = serpy.Field()
    watchers = serpy.Field()
    is_blocked = serpy.Field()
    blocked_note = serpy.Field()
    tags = serpy.Field()
    total_points = serpy.MethodField()
    comment = serpy.MethodField("get_comment")
    origin_issue = ListOriginIssueSerializer(attr="generated_from_issue")

    tasks = serpy.MethodField()

    def get_milestone_slug(self, obj):
        return obj.milestone.slug if obj.milestone else None

    def get_milestone_name(self, obj):
        return obj.milestone.name if obj.milestone else None

    def get_total_points(self, obj):
        assert hasattr(obj, "total_points_attr"), "instance must have a total_points_attr attribute"
        return obj.total_points_attr

    def get_points(self, obj):
        assert hasattr(obj, "role_points_attr"), "instance must have a role_points_attr attribute"
        if obj.role_points_attr is None:
            return {}

        return obj.role_points_attr

    def get_comment(self, obj):
        return ""

    def get_tasks(self, obj):
        include_tasks = getattr(obj, "include_tasks", False)

        if include_tasks:
            assert hasattr(obj, "tasks_attr"), "instance must have a tasks_attr attribute"

        if not include_tasks or obj.tasks_attr is None:
            return []

        return obj.tasks_attr


class UserStorySerializer(UserStoryListSerializer):
    comment = serpy.MethodField()
    origin_issue = serpy.MethodField()
    blocked_note_html = serpy.MethodField()
    description_html = serpy.MethodField()

    def get_comment(self, obj):
        # NOTE: This method and field is necessary to historical comments work
        return ""

    def get_origin_issue(self, obj):
        if obj.generated_from_issue:
            return {
                "id": obj.generated_from_issue.id,
                "ref": obj.generated_from_issue.ref,
                "subject": obj.generated_from_issue.subject,
            }
        return None

    def get_blocked_note_html(self, obj):
        return mdrender(obj.project, obj.blocked_note)

    def get_description_html(self, obj):
        return mdrender(obj.project, obj.description)


class UserStoryNeighborsSerializer(NeighborsSerializerMixin, UserStorySerializer):
    def serialize_neighbor(self, neighbor):
        if neighbor:
            return NeighborUserStorySerializer(neighbor).data
        return None


class NeighborUserStorySerializer(serializers.LightSerializer):
    id = serpy.Field()
    ref = serpy.Field()
    subject = serpy.Field()


class UserStoriesBulkSerializer(ProjectExistsValidator, UserStoryStatusExistsValidator,
                                serializers.Serializer):
    project_id = serializers.IntegerField()
    status_id = serializers.IntegerField(required=False)
    bulk_stories = serializers.CharField()


## Order bulk serializers

class _UserStoryOrderBulkSerializer(UserStoryExistsValidator, serializers.Serializer):
    us_id = serializers.IntegerField()
    order = serializers.IntegerField()


class UpdateUserStoriesOrderBulkSerializer(ProjectExistsValidator, UserStoryStatusExistsValidator,
                                           serializers.Serializer):
    project_id = serializers.IntegerField()
    bulk_stories = _UserStoryOrderBulkSerializer(many=True)


## Milestone bulk serializers

class _UserStoryMilestoneBulkSerializer(UserStoryExistsValidator, serializers.Serializer):
    us_id = serializers.IntegerField()


class UpdateMilestoneBulkSerializer(ProjectExistsValidator, MilestoneExistsValidator, serializers.Serializer):
    project_id = serializers.IntegerField()
    milestone_id = serializers.IntegerField()
    bulk_stories = _UserStoryMilestoneBulkSerializer(many=True)

    def validate(self, data):
        """
        All the userstories and the milestone are from the same project
        """
        user_story_ids = [us["us_id"] for us in data["bulk_stories"]]
        project = get_object_or_404(Project, pk=data["project_id"])

        if project.user_stories.filter(id__in=user_story_ids).count() != len(user_story_ids):
            raise serializers.ValidationError("all the user stories must be from the same project")

        if project.milestones.filter(id=data["milestone_id"]).count() != 1:
            raise serializers.ValidationError("the milestone isn't valid for the project")

        return data
