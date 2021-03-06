# -*- encoding: utf-8 -*-
# Copyright (c) 2015 b<>com
#
# Authors: Jean-Emile DARTOIS <jean-emile.dartois@b-com.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from oslo_config import cfg

from watcher.applier import manager
from watcher.common import exception
from watcher.common import service
from watcher.common import utils


CONF = cfg.CONF
CONF.register_group(manager.opt_group)
CONF.register_opts(manager.APPLIER_MANAGER_OPTS, manager.opt_group)


class ApplierAPI(service.Service):

    def __init__(self):
        super(ApplierAPI, self).__init__(ApplierAPIManager)

    def launch_action_plan(self, context, action_plan_uuid=None):
        if not utils.is_uuid_like(action_plan_uuid):
            raise exception.InvalidUuidOrName(name=action_plan_uuid)

        return self.conductor_client.call(
            context.to_dict(), 'launch_action_plan',
            action_plan_uuid=action_plan_uuid)


class ApplierAPIManager(object):

    @property
    def service_name(self):
        return None

    @property
    def api_version(self):
        return '1.0'

    @property
    def publisher_id(self):
        return CONF.watcher_applier.publisher_id

    @property
    def conductor_topic(self):
        return CONF.watcher_applier.conductor_topic

    @property
    def status_topic(self):
        return CONF.watcher_applier.status_topic

    @property
    def notification_topics(self):
        return []

    @property
    def conductor_endpoints(self):
        return []

    @property
    def status_endpoints(self):
        return []

    @property
    def notification_endpoints(self):
        return []
