# Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import datetime

import mock
from oslo_config import cfg
from oslo_utils import timeutils
from six.moves.urllib import parse as urlparse
from wsme import types as wtypes

from watcher.api.controllers.v1 import audit_template as api_audit_template
from watcher.common import exception
from watcher.common import utils
from watcher import objects
from watcher.tests.api import base as api_base
from watcher.tests.api import utils as api_utils
from watcher.tests import base
from watcher.tests.db import utils as db_utils
from watcher.tests.objects import utils as obj_utils


def post_get_test_audit_template(**kw):
    audit_template = api_utils.audit_template_post_data(**kw)
    goal = db_utils.get_test_goal()
    strategy = db_utils.get_test_strategy(goal_id=goal['id'])
    del audit_template['uuid']
    del audit_template['goal_id']
    del audit_template['strategy_id']
    audit_template['goal_uuid'] = kw.get('goal_uuid', goal['uuid'])
    audit_template['strategy_uuid'] = kw.get('strategy_uuid', strategy['uuid'])
    return audit_template


class TestAuditTemplateObject(base.TestCase):

    def test_audit_template_init(self):
        audit_template_dict = post_get_test_audit_template()
        del audit_template_dict['name']
        audit_template = api_audit_template.AuditTemplate(
            **audit_template_dict)
        self.assertEqual(wtypes.Unset, audit_template.name)


class TestListAuditTemplate(api_base.FunctionalTest):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.fake_goal1 = obj_utils.get_test_goal(
            self.context, id=1, uuid=utils.generate_uuid(), name="DUMMY_1")
        self.fake_goal2 = obj_utils.get_test_goal(
            self.context, id=2, uuid=utils.generate_uuid(), name="DUMMY_2")
        self.fake_goal1.create()
        self.fake_goal2.create()

    def test_empty(self):
        response = self.get_json('/audit_templates')
        self.assertEqual([], response['audit_templates'])

    def _assert_audit_template_fields(self, audit_template):
        audit_template_fields = ['name', 'goal_uuid', 'host_aggregate']
        for field in audit_template_fields:
            self.assertIn(field, audit_template)

    def test_one(self):
        audit_template = obj_utils.create_test_audit_template(self.context)
        response = self.get_json('/audit_templates')
        self.assertEqual(audit_template.uuid,
                         response['audit_templates'][0]["uuid"])
        self._assert_audit_template_fields(response['audit_templates'][0])

    def test_get_one_soft_deleted_ok(self):
        audit_template = obj_utils.create_test_audit_template(self.context)
        audit_template.soft_delete()
        response = self.get_json('/audit_templates',
                                 headers={'X-Show-Deleted': 'True'})
        self.assertEqual(audit_template.uuid,
                         response['audit_templates'][0]["uuid"])
        self._assert_audit_template_fields(response['audit_templates'][0])

        response = self.get_json('/audit_templates')
        self.assertEqual([], response['audit_templates'])

    def test_get_one_by_uuid(self):
        audit_template = obj_utils.create_test_audit_template(self.context)
        response = self.get_json(
            '/audit_templates/%s' % audit_template['uuid'])
        self.assertEqual(audit_template.uuid, response['uuid'])
        self._assert_audit_template_fields(response)

    def test_get_one_by_name(self):
        audit_template = obj_utils.create_test_audit_template(self.context)
        response = self.get_json(urlparse.quote(
            '/audit_templates/%s' % audit_template['name']))
        self.assertEqual(audit_template.uuid, response['uuid'])
        self._assert_audit_template_fields(response)

    def test_get_one_soft_deleted(self):
        audit_template = obj_utils.create_test_audit_template(self.context)
        audit_template.soft_delete()
        response = self.get_json(
            '/audit_templates/%s' % audit_template['uuid'],
            headers={'X-Show-Deleted': 'True'})
        self.assertEqual(audit_template.uuid, response['uuid'])
        self._assert_audit_template_fields(response)

        response = self.get_json(
            '/audit_templates/%s' % audit_template['uuid'],
            expect_errors=True)
        self.assertEqual(404, response.status_int)

    def test_detail(self):
        audit_template = obj_utils.create_test_audit_template(self.context)
        response = self.get_json('/audit_templates/detail')
        self.assertEqual(audit_template.uuid,
                         response['audit_templates'][0]["uuid"])
        self._assert_audit_template_fields(response['audit_templates'][0])

    def test_detail_soft_deleted(self):
        audit_template = obj_utils.create_test_audit_template(self.context)
        audit_template.soft_delete()
        response = self.get_json('/audit_templates/detail',
                                 headers={'X-Show-Deleted': 'True'})
        self.assertEqual(audit_template.uuid,
                         response['audit_templates'][0]["uuid"])
        self._assert_audit_template_fields(response['audit_templates'][0])

        response = self.get_json('/audit_templates/detail')
        self.assertEqual([], response['audit_templates'])

    def test_detail_against_single(self):
        audit_template = obj_utils.create_test_audit_template(self.context)
        response = self.get_json(
            '/audit_templates/%s/detail' % audit_template['uuid'],
            expect_errors=True)
        self.assertEqual(404, response.status_int)

    def test_many(self):
        audit_template_list = []
        for id_ in range(5):
            audit_template = obj_utils.create_test_audit_template(
                self.context, id=id_,
                uuid=utils.generate_uuid(),
                name='My Audit Template {0}'.format(id_))
            audit_template_list.append(audit_template.uuid)
        response = self.get_json('/audit_templates')
        self.assertEqual(len(audit_template_list),
                         len(response['audit_templates']))
        uuids = [s['uuid'] for s in response['audit_templates']]
        self.assertEqual(sorted(audit_template_list), sorted(uuids))

    def test_many_without_soft_deleted(self):
        audit_template_list = []
        for id_ in [1, 2, 3]:
            audit_template = obj_utils.create_test_audit_template(
                self.context, id=id_, uuid=utils.generate_uuid(),
                name='My Audit Template {0}'.format(id_))
            audit_template_list.append(audit_template.uuid)
        for id_ in [4, 5]:
            audit_template = obj_utils.create_test_audit_template(
                self.context, id=id_, uuid=utils.generate_uuid(),
                name='My Audit Template {0}'.format(id_))
            audit_template.soft_delete()
        response = self.get_json('/audit_templates')
        self.assertEqual(3, len(response['audit_templates']))
        uuids = [s['uuid'] for s in response['audit_templates']]
        self.assertEqual(sorted(audit_template_list), sorted(uuids))

    def test_many_with_soft_deleted(self):
        audit_template_list = []
        for id_ in [1, 2, 3]:
            audit_template = obj_utils.create_test_audit_template(
                self.context, id=id_, uuid=utils.generate_uuid(),
                name='My Audit Template {0}'.format(id_))
            audit_template_list.append(audit_template.uuid)
        for id_ in [4, 5]:
            audit_template = obj_utils.create_test_audit_template(
                self.context, id=id_, uuid=utils.generate_uuid(),
                name='My Audit Template {0}'.format(id_))
            audit_template.soft_delete()
            audit_template_list.append(audit_template.uuid)
        response = self.get_json('/audit_templates',
                                 headers={'X-Show-Deleted': 'True'})
        self.assertEqual(5, len(response['audit_templates']))
        uuids = [s['uuid'] for s in response['audit_templates']]
        self.assertEqual(sorted(audit_template_list), sorted(uuids))

    def test_links(self):
        uuid = utils.generate_uuid()
        obj_utils.create_test_audit_template(self.context, id=1, uuid=uuid)
        response = self.get_json('/audit_templates/%s' % uuid)
        self.assertIn('links', response.keys())
        self.assertEqual(2, len(response['links']))
        self.assertIn(uuid, response['links'][0]['href'])
        for l in response['links']:
            bookmark = l['rel'] == 'bookmark'
            self.assertTrue(self.validate_link(l['href'], bookmark=bookmark))

    def test_collection_links(self):
        for id_ in range(5):
            obj_utils.create_test_audit_template(
                self.context, id=id_, uuid=utils.generate_uuid(),
                name='My Audit Template {0}'.format(id_))
        response = self.get_json('/audit_templates/?limit=3')
        self.assertEqual(3, len(response['audit_templates']))

        next_marker = response['audit_templates'][-1]['uuid']
        self.assertIn(next_marker, response['next'])

    def test_collection_links_default_limit(self):
        cfg.CONF.set_override('max_limit', 3, 'api',
                              enforce_type=True)
        for id_ in range(5):
            obj_utils.create_test_audit_template(
                self.context, id=id_, uuid=utils.generate_uuid(),
                name='My Audit Template {0}'.format(id_))
        response = self.get_json('/audit_templates')
        self.assertEqual(3, len(response['audit_templates']))

        next_marker = response['audit_templates'][-1]['uuid']
        self.assertIn(next_marker, response['next'])

    def test_filter_by_goal_uuid(self):
        for id_ in range(1, 3):
            obj_utils.create_test_audit_template(
                self.context, id=id_, uuid=utils.generate_uuid(),
                name='My Audit Template {0}'.format(id_),
                goal_id=self.fake_goal1.id)

        for id_ in range(3, 6):
            obj_utils.create_test_audit_template(
                self.context, id=id_, uuid=utils.generate_uuid(),
                name='My Audit Template {0}'.format(id_),
                goal_id=self.fake_goal2.id)

        response = self.get_json(
            '/audit_templates?goal_uuid=%s' % self.fake_goal2.uuid)
        self.assertEqual(3, len(response['audit_templates']))


class TestPatch(api_base.FunctionalTest):

    def setUp(self):
        super(TestPatch, self).setUp()
        self.audit_template = obj_utils.create_test_audit_template(
            self.context, strategy_id=None)
        self.fake_goal1 = obj_utils.get_test_goal(
            self.context, id=1, uuid=utils.generate_uuid(), name="DUMMY_1")
        self.fake_goal2 = obj_utils.get_test_goal(
            self.context, id=2, uuid=utils.generate_uuid(), name="DUMMY_2")
        self.fake_goal1.create()
        self.fake_goal2.create()
        self.fake_strategy1 = obj_utils.get_test_strategy(
            self.context, id=1, uuid=utils.generate_uuid(), name="STRATEGY_1",
            goal_id=self.fake_goal1.id)
        self.fake_strategy2 = obj_utils.get_test_strategy(
            self.context, id=2, uuid=utils.generate_uuid(), name="STRATEGY_2",
            goal_id=self.fake_goal2.id)
        self.fake_strategy1.create()
        self.fake_strategy2.create()

    @mock.patch.object(timeutils, 'utcnow')
    def test_replace_goal_uuid(self, mock_utcnow):
        test_time = datetime.datetime(2000, 1, 1, 0, 0)
        mock_utcnow.return_value = test_time

        new_goal_uuid = self.fake_goal2.uuid
        response = self.get_json(
            '/audit_templates/%s' % self.audit_template.uuid)
        self.assertNotEqual(new_goal_uuid, response['goal_uuid'])

        response = self.patch_json(
            '/audit_templates/%s' % self.audit_template.uuid,
            [{'path': '/goal_uuid', 'value': new_goal_uuid,
              'op': 'replace'}])
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_code)

        response = self.get_json(
            '/audit_templates/%s' % self.audit_template.uuid)
        self.assertEqual(new_goal_uuid, response['goal_uuid'])
        return_updated_at = timeutils.parse_isotime(
            response['updated_at']).replace(tzinfo=None)
        self.assertEqual(test_time, return_updated_at)

    @mock.patch.object(timeutils, 'utcnow')
    def test_replace_goal_uuid_by_name(self, mock_utcnow):
        test_time = datetime.datetime(2000, 1, 1, 0, 0)
        mock_utcnow.return_value = test_time

        new_goal_uuid = self.fake_goal2.uuid
        response = self.get_json(urlparse.quote(
            '/audit_templates/%s' % self.audit_template.name))
        self.assertNotEqual(new_goal_uuid, response['goal_uuid'])

        response = self.patch_json(
            '/audit_templates/%s' % self.audit_template.name,
            [{'path': '/goal_uuid', 'value': new_goal_uuid,
              'op': 'replace'}])
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_code)

        response = self.get_json(
            '/audit_templates/%s' % self.audit_template.name)
        self.assertEqual(new_goal_uuid, response['goal_uuid'])
        return_updated_at = timeutils.parse_isotime(
            response['updated_at']).replace(tzinfo=None)
        self.assertEqual(test_time, return_updated_at)

    def test_replace_non_existent_audit_template(self):
        response = self.patch_json(
            '/audit_templates/%s' % utils.generate_uuid(),
            [{'path': '/goal_uuid', 'value': self.fake_goal1.uuid,
              'op': 'replace'}],
            expect_errors=True)
        self.assertEqual(404, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertTrue(response.json['error_message'])

    def test_replace_invalid_goal(self):
        with mock.patch.object(
            self.dbapi,
            'update_audit_template',
            wraps=self.dbapi.update_audit_template
        ) as cn_mock:
            response = self.patch_json(
                '/audit_templates/%s' % self.audit_template.uuid,
                [{'path': '/goal_uuid', 'value': utils.generate_uuid(),
                  'op': 'replace'}],
                expect_errors=True)
        self.assertEqual(400, response.status_int)
        assert not cn_mock.called

    def test_add_goal_uuid(self):
        response = self.patch_json(
            '/audit_templates/%s' % self.audit_template.uuid,
            [{'path': '/goal_uuid',
              'value': self.fake_goal2.uuid,
              'op': 'add'}])
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_int)

        response = self.get_json(
            '/audit_templates/%s' % self.audit_template.uuid)
        self.assertEqual(self.fake_goal2.uuid, response['goal_uuid'])

    def test_add_strategy_uuid(self):
        response = self.patch_json(
            '/audit_templates/%s' % self.audit_template.uuid,
            [{'path': '/strategy_uuid',
              'value': self.fake_strategy1.uuid,
              'op': 'add'}])
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_int)

        response = self.get_json(
            '/audit_templates/%s' % self.audit_template.uuid)
        self.assertEqual(self.fake_strategy1.uuid, response['strategy_uuid'])

    def test_replace_strategy_uuid(self):
        response = self.patch_json(
            '/audit_templates/%s' % self.audit_template.uuid,
            [{'path': '/strategy_uuid',
              'value': self.fake_strategy2['uuid'],
              'op': 'replace'}])
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_int)

        response = self.get_json(
            '/audit_templates/%s' % self.audit_template.uuid)
        self.assertEqual(
            self.fake_strategy2['uuid'], response['strategy_uuid'])

    def test_replace_invalid_strategy(self):
        response = self.patch_json(
            '/audit_templates/%s' % self.audit_template.uuid,
            [{'path': '/strategy_uuid',
              'value': utils.generate_uuid(),  # Does not exist
              'op': 'replace'}], expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(400, response.status_int)
        self.assertTrue(response.json['error_message'])

    def test_add_non_existent_property(self):
        response = self.patch_json(
            '/audit_templates/%s' % self.audit_template.uuid,
            [{'path': '/foo', 'value': 'bar', 'op': 'add'}],
            expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(400, response.status_int)
        self.assertTrue(response.json['error_message'])

    def test_remove_strategy(self):
        audit_template = obj_utils.create_test_audit_template(
            self.context, uuid=utils.generate_uuid(),
            name="AT_%s" % utils.generate_uuid(),
            goal_id=self.fake_goal1.id,
            strategy_id=self.fake_strategy1.id)
        response = self.get_json(
            '/audit_templates/%s' % audit_template.uuid)
        self.assertIsNotNone(response['strategy_uuid'])

        response = self.patch_json(
            '/audit_templates/%s' % self.audit_template.uuid,
            [{'path': '/strategy_uuid', 'op': 'remove'}])
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(200, response.status_code)

    def test_remove_goal(self):
        response = self.get_json(
            '/audit_templates/%s' % self.audit_template.uuid)
        self.assertIsNotNone(response['goal_uuid'])

        response = self.patch_json(
            '/audit_templates/%s' % self.audit_template.uuid,
            [{'path': '/goal_uuid', 'op': 'remove'}],
            expect_errors=True)
        self.assertEqual(403, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertTrue(response.json['error_message'])

    def test_remove_uuid(self):
        response = self.patch_json(
            '/audit_templates/%s' % self.audit_template.uuid,
            [{'path': '/uuid', 'op': 'remove'}],
            expect_errors=True)
        self.assertEqual(400, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertTrue(response.json['error_message'])

    def test_remove_non_existent_property(self):
        response = self.patch_json(
            '/audit_templates/%s' % self.audit_template.uuid,
            [{'path': '/non-existent', 'op': 'remove'}],
            expect_errors=True)
        self.assertEqual(400, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertTrue(response.json['error_message'])


class TestPost(api_base.FunctionalTest):

    def setUp(self):
        super(TestPost, self).setUp()

        self.fake_goal1 = obj_utils.get_test_goal(
            self.context, id=1, uuid=utils.generate_uuid(), name="DUMMY_1")
        self.fake_goal2 = obj_utils.get_test_goal(
            self.context, id=2, uuid=utils.generate_uuid(), name="DUMMY_2")
        self.fake_goal1.create()
        self.fake_goal2.create()
        self.fake_strategy1 = obj_utils.get_test_strategy(
            self.context, id=1, uuid=utils.generate_uuid(), name="STRATEGY_1",
            goal_id=self.fake_goal1.id)
        self.fake_strategy2 = obj_utils.get_test_strategy(
            self.context, id=2, uuid=utils.generate_uuid(), name="STRATEGY_2",
            goal_id=self.fake_goal2.id)
        self.fake_strategy1.create()
        self.fake_strategy2.create()

    @mock.patch.object(timeutils, 'utcnow')
    def test_create_audit_template(self, mock_utcnow):
        audit_template_dict = post_get_test_audit_template(
            goal_uuid=self.fake_goal1.uuid,
            strategy_uuid=self.fake_strategy1.uuid)
        test_time = datetime.datetime(2000, 1, 1, 0, 0)
        mock_utcnow.return_value = test_time

        response = self.post_json('/audit_templates', audit_template_dict)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(201, response.status_int)
        # Check location header
        self.assertIsNotNone(response.location)
        expected_location = \
            '/v1/audit_templates/%s' % response.json['uuid']
        self.assertEqual(urlparse.urlparse(response.location).path,
                         expected_location)
        self.assertTrue(utils.is_uuid_like(response.json['uuid']))
        self.assertNotIn('updated_at', response.json.keys)
        self.assertNotIn('deleted_at', response.json.keys)
        self.assertEqual(self.fake_goal1.uuid, response.json['goal_uuid'])
        self.assertEqual(self.fake_strategy1.uuid,
                         response.json['strategy_uuid'])
        return_created_at = timeutils.parse_isotime(
            response.json['created_at']).replace(tzinfo=None)
        self.assertEqual(test_time, return_created_at)

    def test_create_audit_template_does_autogenerate_id(self):
        audit_template_dict = post_get_test_audit_template(
            goal_uuid=self.fake_goal1.uuid, strategy_uuid=None)
        with mock.patch.object(
            self.dbapi,
            'create_audit_template',
            wraps=self.dbapi.create_audit_template
        ) as cn_mock:
            response = self.post_json('/audit_templates', audit_template_dict)
        self.assertEqual(audit_template_dict['goal_uuid'],
                         response.json['goal_uuid'])
        # Check that 'id' is not in first arg of positional args
        self.assertNotIn('id', cn_mock.call_args[0][0])

    def test_create_audit_template_generate_uuid(self):
        audit_template_dict = post_get_test_audit_template(
            goal_uuid=self.fake_goal1.uuid, strategy_uuid=None)

        response = self.post_json('/audit_templates', audit_template_dict)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(201, response.status_int)
        self.assertTrue(utils.is_uuid_like(response.json['uuid']))

    def test_create_audit_template_with_invalid_goal(self):
        with mock.patch.object(
            self.dbapi,
            'create_audit_template',
            wraps=self.dbapi.create_audit_template
        ) as cn_mock:
            audit_template_dict = post_get_test_audit_template(
                goal_uuid=utils.generate_uuid())
            response = self.post_json('/audit_templates',
                                      audit_template_dict, expect_errors=True)
        self.assertEqual(400, response.status_int)
        assert not cn_mock.called

    def test_create_audit_template_with_invalid_strategy(self):
        with mock.patch.object(
            self.dbapi,
            'create_audit_template',
            wraps=self.dbapi.create_audit_template
        ) as cn_mock:
            audit_template_dict = post_get_test_audit_template(
                goal_uuid=self.fake_goal1['uuid'],
                strategy_uuid=utils.generate_uuid())
            response = self.post_json('/audit_templates',
                                      audit_template_dict, expect_errors=True)
        self.assertEqual(400, response.status_int)
        assert not cn_mock.called

    def test_create_audit_template_with_unrelated_strategy(self):
        with mock.patch.object(
            self.dbapi,
            'create_audit_template',
            wraps=self.dbapi.create_audit_template
        ) as cn_mock:
            audit_template_dict = post_get_test_audit_template(
                goal_uuid=self.fake_goal1['uuid'],
                strategy_uuid=self.fake_strategy2['uuid'])
            response = self.post_json('/audit_templates',
                                      audit_template_dict, expect_errors=True)
        self.assertEqual(400, response.status_int)
        assert not cn_mock.called

    def test_create_audit_template_with_uuid(self):
        with mock.patch.object(
            self.dbapi,
            'create_audit_template',
            wraps=self.dbapi.create_audit_template
        ) as cn_mock:
            audit_template_dict = post_get_test_audit_template()
            response = self.post_json('/audit_templates', audit_template_dict,
                                      expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(400, response.status_int)
        assert not cn_mock.called


class TestDelete(api_base.FunctionalTest):

    def setUp(self):
        super(TestDelete, self).setUp()
        self.audit_template = obj_utils.create_test_audit_template(
            self.context)

    @mock.patch.object(timeutils, 'utcnow')
    def test_delete_audit_template_by_uuid(self, mock_utcnow):
        test_time = datetime.datetime(2000, 1, 1, 0, 0)
        mock_utcnow.return_value = test_time
        self.delete(urlparse.quote('/audit_templates/%s' %
                                   self.audit_template.uuid))
        response = self.get_json(
            urlparse.quote('/audit_templates/%s' % self.audit_template.uuid),
            expect_errors=True)
        self.assertEqual(404, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertTrue(response.json['error_message'])

        self.assertRaises(exception.AuditTemplateNotFound,
                          objects.AuditTemplate.get_by_uuid,
                          self.context,
                          self.audit_template.uuid)

        self.context.show_deleted = True
        at = objects.AuditTemplate.get_by_uuid(self.context,
                                               self.audit_template.uuid)
        self.assertEqual(self.audit_template.name, at.name)

    @mock.patch.object(timeutils, 'utcnow')
    def test_delete_audit_template_by_name(self, mock_utcnow):
        test_time = datetime.datetime(2000, 1, 1, 0, 0)
        mock_utcnow.return_value = test_time
        self.delete(urlparse.quote('/audit_templates/%s' %
                                   self.audit_template.name))
        response = self.get_json(
            urlparse.quote('/audit_templates/%s' % self.audit_template.name),
            expect_errors=True)
        self.assertEqual(404, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertTrue(response.json['error_message'])

        self.assertRaises(exception.AuditTemplateNotFound,
                          objects.AuditTemplate.get_by_name,
                          self.context,
                          self.audit_template.name)

        self.context.show_deleted = True
        at = objects.AuditTemplate.get_by_name(self.context,
                                               self.audit_template.name)
        self.assertEqual(self.audit_template.uuid, at.uuid)

    def test_delete_audit_template_not_found(self):
        uuid = utils.generate_uuid()
        response = self.delete(
            '/audit_templates/%s' % uuid, expect_errors=True)
        self.assertEqual(404, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertTrue(response.json['error_message'])
