# Copyright (c) 2015
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import luigi
import unittest
from mock import Mock
from helpers import with_config


test_task_has_run = False


class TestTask(luigi.Task):
    """
    Requires a single file dependency
    """
    external_task = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super(TestTask, self).__init__(*args, **kwargs)
        global test_task_has_run
        test_task_has_run = False

    def requires(self):
        return self.external_task

    def output(self):
        mock_target = Mock(spec=luigi.Target)
        # the return is False so that this task will be scheduled
        mock_target.exists.return_value = False
        return mock_target

    def run(self):
        global test_task_has_run
        test_task_has_run = True


class WorkerExternalTaskTest(unittest.TestCase):

    def _build_mocks(self, external_task_completion):
        mock_external_task_target = Mock(spec=luigi.Target)
        mock_external_task_target.task_id = 'mock_external_task_target'
        mock_external_task_target.exists.return_value = True

        mock_external_task = Mock(spec=luigi.ExternalTask)
        mock_external_task.task_id = 'mock_external_task'
        mock_external_task.deps = lambda : []
        mock_external_task.disabled = False
        mock_external_task.complete.side_effect = external_task_completion
        mock_external_task.output.return_value = mock_external_task_target

        return mock_external_task

    @with_config({'core': {'retry-external-tasks': 'true',
                           'disable-num-failures': '2',
                           'retry-delay': '0.001'}})
    def test_external_dependency_already_complete(self):
        """
        Test that an external dependency that is not `complete` when luigi is invoked, but \
        becomes `complete` while the workflow is executing is re-evaluated.
        """
        assert luigi.configuration.get_config().getboolean('core',
                                                           'retry-external-tasks',
                                                           False) == True

        # `complete` is called twice per iteration, so duplicate each return code. The
        # following corresponds to 3 iterations - True.
        mock_external_task = self._build_mocks(external_task_completion=[True, True])

        test_task = TestTask(external_task=mock_external_task)
        luigi.build([test_task], local_scheduler=True)

        # assert mock_external_task.runnable == True
        assert test_task_has_run == True
        assert mock_external_task.complete.call_count == 2


    # @with_config({'core': {'retry-external-tasks': 'true',
    #                        'disable-num-failures': '2',
    #                        'retry-delay': '0.001'}})
    # def test_external_dependency_completes_later_successfully(self):
    #     """
    #     Test that an external dependency that is not `complete` when luigi is invoked, but \
    #     becomes `complete` while the workflow is executing is re-evaluated.
    #     """
    #     assert luigi.configuration.get_config().getboolean('core',
    #                                                        'retry-external-tasks',
    #                                                        False) == True
    #
    #     # `complete` is called twice per iteration, so duplicate each return code. The
    #     # following corresponds to 3 iterations - False, False, True.
    #     mock_external_task = self._build_mocks(external_task_completion=[False, False,
    #                                                                      False, False,
    #                                                                      True, True])
    #
    #     test_task = TestTask()
    #     luigi.build([test_task], local_scheduler=True)
    #
    #     # assert mock_external_task.runnable == True
    #     assert test_task_has_run == True
    #     assert mock_external_task.complete.call_count == 6


if __name__ == '__main__':
    unittest.main()
