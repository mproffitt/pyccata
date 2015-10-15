from collections import namedtuple

class DataProviders(object):

    ###################################################################################################################
    # Data provider methods
    # =================================================================================================================
    @staticmethod
    def _get_client():
        JIRA = namedtuple('JIRA', 'search_issues projects')
        return JIRA(
            search_issues=lambda x, maxResults, fields: DataProviders._test_data_for_search_results(),
            projects=lambda: DataProviders._test_data_for_projects()
        )

    @staticmethod
    def _test_data_for_projects():
        Project = namedtuple('Project', 'key name')
        return [
            Project(key='TP', name='Test Project'),
            Project(key='ATP', name='Another test project'),
            Project(key='BB', name='Bobs Board')
        ]

    @staticmethod
    def _test_data_for_search_results():
        Project = namedtuple('Project', 'key name')
        Assignee = namedtuple('Assignee', 'name displayName')
        Field = namedtuple('Field', 'assignee project')
        Issue = namedtuple('Issue', 'key fields')
        data = [
            Issue(
                key    = 'TP-123',
                fields = Field(
                    assignee=Assignee(
                        name='bob123',
                        displayName='Bob Smith'
                    ),
                    project=Project(
                        name='Test Project',
                        key='TP'
                    )
                )
            ),
            Issue(
                key    = 'ATP-114',
                fields = Field(
                    assignee=Assignee(
                        name='bob123',
                        displayName='Bob Smith'
                    ),
                    project=Project(
                        name='Another Test Project',
                        key='ATP'
                    )
                )
            )
        ]
        return data

    @staticmethod
    def _get_config_for_test(port='8080'):
        key = 'jira'
        Config = namedtuple('Config', 'manager jira server port username password')
        Jira   = Config(
            manager  = None,
            jira     = None,
            server   = 'http://jira.local',
            port     = port,
            username = 'test',
            password = 'letmein'
        )
        return Config(
            manager  = key,
            jira     = Jira,
            server   = None,
            port     = None,
            username = None,
            password = None
        )

