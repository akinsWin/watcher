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
from watcher.decision_engine.model import element
from watcher.tests import base


class TestInstance(base.TestCase):

    def test_namedelement(self):
        instance = element.Instance()
        instance.state = element.InstanceState.ACTIVE
        self.assertEqual(element.InstanceState.ACTIVE, instance.state)
        instance.human_id = "human_05"
        self.assertEqual("human_05", instance.human_id)
