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

from django.utils.translation import ugettext as _

from taiga.base.api import serializers
from taiga.base.fields import PgArrayField
from taiga.base.fields import PickledObjectField
from taiga.projects.notifications.mixins import EditableWatchedResourceModelSerializer
from taiga.projects.notifications.validators import WatchersValidator
from taiga.projects.tagging.fields import TagsAndTagsColorsField

from . import models


class UserStoryExistsValidator:
    def validate_us_id(self, attrs, source):
        value = attrs[source]
        if not models.UserStory.objects.filter(pk=value).exists():
            msg = _("There's no user story with that id")
            raise serializers.ValidationError(msg)
        return attrs


class RolePointsField(serializers.WritableField):
    def to_native(self, obj):
        return {str(o.role.id): o.points.id for o in obj.all()}

    def from_native(self, obj):
        if isinstance(obj, dict):
            return obj
        return json.loads(obj)


class UserStoryValidator(WatchersValidator, EditableWatchedResourceModelSerializer, serializers.ModelSerializer):
    tags = TagsAndTagsColorsField(default=[], required=False)
    external_reference = PgArrayField(required=False)
    points = RolePointsField(source="role_points", required=False)
    tribe_gig = PickledObjectField(required=False)

    class Meta:
        model = models.UserStory
        depth = 0
        read_only_fields = ('created_date', 'modified_date', 'owner')
