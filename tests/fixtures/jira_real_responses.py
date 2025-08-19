"""Real JIRA API responses captured for mock testing.

These responses were captured from actual JIRA API calls to ensure
mock tests accurately reflect real API behavior.

Generated: 2025-08-17T23:57:51.530062
"""

# Issue Operations
REAL_ISSUE_CREATE_RESPONSE = {
    "id": "1166230",
    "key": "FTEST-120",
    "summary": "Response Capture Test - 20250817_235744",
    "url": "https://baseball.atlassian.net/rest/api/3/issue/1166230",
    "description": {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Test issue for capturing API responses"}
                ],
            }
        ],
    },
    "status": {"name": "To Do", "category": "To Do", "color": "blue-gray"},
    "issue_type": {"name": "Task"},
    "priority": {"name": "None"},
    "project": {
        "key": "FTEST",
        "name": "Frameworks Testing",
        "category": "Client Engineering",
        "avatar_url": "https://baseball.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/25819",
    },
    "worklog": {"startAt": 0, "maxResults": 20, "total": 0, "worklogs": []},
    "assignee": {
        "display_name": "Douglas Mason",
        "name": "Douglas Mason",
        "email": "douglas.mason@mlb.com",
        "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
    },
    "reporter": {
        "display_name": "Douglas Mason",
        "name": "Douglas Mason",
        "email": "douglas.mason@mlb.com",
        "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
    },
    "created": "2025-08-18T01:57:45.698-0400",
    "updated": "2025-08-18T01:57:45.782-0400",
}

REAL_ISSUE_GET_RESPONSE = {
    "id": "1166230",
    "key": "FTEST-120",
    "summary": "Response Capture Test - 20250817_235744",
    "description": {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Test issue for capturing API responses"}
                ],
            }
        ],
    },
    "status": {"name": "To Do", "category": "To Do", "color": "blue-gray"},
    "priority": {"name": "None"},
    "assignee": {
        "display_name": "Douglas Mason",
        "name": "Douglas Mason",
        "email": "douglas.mason@mlb.com",
        "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
    },
}

REAL_ISSUE_UPDATE_RESPONSE = {
    "id": "1166230",
    "key": "FTEST-120",
    "summary": "UPDATED - ",
    "url": "https://baseball.atlassian.net/rest/api/3/issue/1166230",
    "description": {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Test issue for capturing API responses"}
                ],
            }
        ],
    },
    "status": {"name": "To Do", "category": "To Do", "color": "blue-gray"},
    "issue_type": {"name": "Task"},
    "priority": {"name": "None"},
    "project": {
        "key": "FTEST",
        "name": "Frameworks Testing",
        "category": "Client Engineering",
        "avatar_url": "https://baseball.atlassian.net/rest/api/3/universal_avatar/view/type/project/avatar/25819",
    },
    "worklog": {"startAt": 0, "maxResults": 20, "total": 0, "worklogs": []},
    "assignee": {
        "display_name": "Douglas Mason",
        "name": "Douglas Mason",
        "email": "douglas.mason@mlb.com",
        "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
    },
    "reporter": {
        "display_name": "Douglas Mason",
        "name": "Douglas Mason",
        "email": "douglas.mason@mlb.com",
        "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
    },
    "created": "2025-08-18T01:57:45.698-0400",
    "updated": "2025-08-18T01:57:46.861-0400",
}

REAL_ISSUE_COMMENT_RESPONSE = {
    "id": "3238025",
    "body": "{'type': 'doc', 'version': 1, 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Test comment for response capture'}]}]}",
    "created": "2025-08-18 01:57:47.434000-04:00",
    "author": "Douglas Mason",
}

REAL_ISSUE_TRANSITIONS = [
    {
        "id": "21",
        "name": "To Do",
        "to": {
            "self": "https://baseball.atlassian.net/rest/api/3/status/21000",
            "description": "",
            "iconUrl": "https://baseball.atlassian.net/",
            "name": "To Do",
            "id": "21000",
            "statusCategory": {
                "self": "https://baseball.atlassian.net/rest/api/3/statuscategory/2",
                "id": 2,
                "key": "new",
                "colorName": "blue-gray",
                "name": "To Do",
            },
        },
        "hasScreen": False,
        "isGlobal": True,
        "isInitial": False,
        "isAvailable": True,
        "isConditional": False,
        "isLooped": False,
    },
    {
        "id": "41",
        "name": "Done",
        "to": {
            "self": "https://baseball.atlassian.net/rest/api/3/status/21002",
            "description": "",
            "iconUrl": "https://baseball.atlassian.net/",
            "name": "Done",
            "id": "21002",
            "statusCategory": {
                "self": "https://baseball.atlassian.net/rest/api/3/statuscategory/3",
                "id": 3,
                "key": "done",
                "colorName": "green",
                "name": "Done",
            },
        },
        "hasScreen": False,
        "isGlobal": True,
        "isInitial": False,
        "isAvailable": True,
        "isConditional": False,
        "isLooped": False,
    },
    {
        "id": "2",
        "name": "Start Work",
        "to": {
            "self": "https://baseball.atlassian.net/rest/api/3/status/21001",
            "description": "",
            "iconUrl": "https://baseball.atlassian.net/",
            "name": "In Progress",
            "id": "21001",
            "statusCategory": {
                "self": "https://baseball.atlassian.net/rest/api/3/statuscategory/4",
                "id": 4,
                "key": "indeterminate",
                "colorName": "yellow",
                "name": "In Progress",
            },
        },
        "hasScreen": False,
        "isGlobal": False,
        "isInitial": False,
        "isAvailable": True,
        "isConditional": False,
        "isLooped": False,
    },
]

# Search Operations
REAL_SEARCH_RESPONSE = {
    "total": 74,
    "start_at": -1,
    "max_results": -1,
    "issues": [
        {
            "id": "1166230",
            "key": "FTEST-120",
            "summary": "UPDATED - ",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Test issue for capturing API responses",
                            }
                        ],
                    }
                ],
            },
            "status": {"name": "To Do", "category": "To Do", "color": "blue-gray"},
            "priority": {"name": "None"},
            "assignee": {
                "display_name": "Douglas Mason",
                "name": "Douglas Mason",
                "email": "douglas.mason@mlb.com",
                "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
            },
            "reporter": {
                "display_name": "Douglas Mason",
                "name": "Douglas Mason",
                "email": "douglas.mason@mlb.com",
                "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
            },
            "created": "2025-08-18T01:57:45.698-0400",
            "updated": "2025-08-18T01:57:47.434-0400",
        },
        {
            "id": "1166229",
            "key": "FTEST-119",
            "summary": "UPDATED - ",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Test issue for capturing API responses",
                            }
                        ],
                    }
                ],
            },
            "status": {"name": "To Do", "category": "To Do", "color": "blue-gray"},
            "priority": {"name": "None"},
            "assignee": {
                "display_name": "Douglas Mason",
                "name": "Douglas Mason",
                "email": "douglas.mason@mlb.com",
                "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
            },
            "reporter": {
                "display_name": "Douglas Mason",
                "name": "Douglas Mason",
                "email": "douglas.mason@mlb.com",
                "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
            },
            "created": "2025-08-18T01:52:20.695-0400",
            "updated": "2025-08-18T01:52:22.548-0400",
        },
        {
            "id": "1166228",
            "key": "FTEST-118",
            "summary": "UPDATED - ",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Test issue for capturing API responses",
                            }
                        ],
                    }
                ],
            },
            "status": {"name": "To Do", "category": "To Do", "color": "blue-gray"},
            "priority": {"name": "None"},
            "assignee": {
                "display_name": "Douglas Mason",
                "name": "Douglas Mason",
                "email": "douglas.mason@mlb.com",
                "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
            },
            "reporter": {
                "display_name": "Douglas Mason",
                "name": "Douglas Mason",
                "email": "douglas.mason@mlb.com",
                "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
            },
            "created": "2025-08-18T01:51:05.529-0400",
            "updated": "2025-08-18T01:51:07.441-0400",
        },
    ],
}

REAL_FIELDS_RESPONSE = [
    {
        "id": "priority",
        "key": "priority",
        "name": "Priority",
        "custom": False,
        "orderable": True,
        "navigable": True,
        "searchable": True,
        "clauseNames": ["priority"],
        "schema": {"type": "priority", "system": "priority"},
    },
    {
        "id": "customfield_21831",
        "key": "customfield_21831",
        "name": "Business Priority EP",
        "untranslatedName": "Business Priority EP",
        "custom": True,
        "orderable": True,
        "navigable": True,
        "searchable": True,
        "clauseNames": [
            "Business Priority EP",
            "Business Priority EP[Dropdown]",
            "cf[21831]",
        ],
        "schema": {
            "type": "option",
            "custom": "com.atlassian.jira.plugin.system.customfieldtypes:select",
            "customId": 21831,
        },
    },
    {
        "id": "customfield_10000",
        "key": "customfield_10000",
        "name": "Business Priority",
        "untranslatedName": "Business Priority",
        "custom": True,
        "orderable": True,
        "navigable": True,
        "searchable": True,
        "clauseNames": [
            "Business Priority",
            "Business Priority[Dropdown]",
            "cf[10000]",
        ],
        "schema": {
            "type": "option",
            "custom": "com.atlassian.jira.plugin.system.customfieldtypes:select",
            "customId": 10000,
        },
    },
    {
        "id": "customfield_14680",
        "key": "customfield_14680",
        "name": "Priority Points",
        "untranslatedName": "Priority Points",
        "custom": True,
        "orderable": True,
        "navigable": True,
        "searchable": True,
        "clauseNames": ["cf[14680]", "Priority Points", "Priority Points[Number]"],
        "schema": {
            "type": "number",
            "custom": "com.atlassian.jira.plugin.system.customfieldtypes:float",
            "customId": 14680,
        },
    },
    {
        "id": "customfield_10011",
        "key": "customfield_10011",
        "name": "Prioritization Notes:",
        "untranslatedName": "Prioritization Notes:",
        "custom": True,
        "orderable": True,
        "navigable": True,
        "searchable": True,
        "clauseNames": [
            "cf[10011]",
            "Prioritization Notes:",
            "Prioritization Notes:[Paragraph]",
        ],
        "schema": {
            "type": "string",
            "custom": "com.atlassian.jira.plugin.system.customfieldtypes:textarea",
            "customId": 10011,
        },
    },
]

# User Operations
REAL_USER_PROFILE = {
    "display_name": "Douglas Mason",
    "name": "Douglas Mason",
    "email": "douglas.mason@mlb.com",
    "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
}

# Project Operations
REAL_PROJECTS_LIST = []

REAL_PROJECT_VERSIONS = []

# Agile Operations
REAL_AGILE_BOARDS = []

REAL_BOARD_SPRINTS = []
