Cloud

Jira Cloud platform / Reference / REST API v3

## Issues

This resource represents Jira issues. Use it to:

*   create or edit issues, individually or in bulk.
*   retrieve metadata about the options for creating or editing issues.
*   delete an issue.
*   assign a user to an issue.
*   get issue changelogs.
*   send notifications about an issue.
*   get details of the transitions available for an issue.
*   transition an issue.
*   Archive issues.
*   Unarchive issues.
*   Export archived issues.

POST

## Bulk fetch changelogs

Bulk fetch changelogs for multiple issues and filter by fields

Returns a paginated list of all changelogs for given issues sorted by changelog date and issue IDs, starting from the oldest changelog and smallest issue ID.

Issues are identified by their ID or key, and optionally changelogs can be filtered by their field IDs. You can request the changelogs of up to 1000 issues and can filter them by up to 10 field IDs.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the projects that the issues are in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issues.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-meta:jira`, `read:avatar:jira`, `read:issue.changelog:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Request bodyapplication/json

A JSON object containing the bulk fetch changelog request filters such as issue IDs and field IDs.

**issueIdsOrKeys**

array<string>

Required

### Responses

Returned if the request is successful.

#### application/json

BulkChangelogResponseBean

A page of changelogs which is designed to handle multiple issues

POST/rest/api/3/changelog/bulkfetch

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "fieldIds": [ "<string>" ], "issueIdsOrKeys": [ "<string>" ], "maxResults": 46, "nextPageToken": "<string>" }`; const response = await requestJira(`/rest/api/3/changelog/bulkfetch`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64` `{ "issueChangeLogs": [ { "changeHistories": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": true, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "emailAddress": "mia@example.com", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g", "timeZone": "Australia/Sydney" }, "created": 1492070429, "id": "10001", "items": [ { "field": "fields", "fieldId": "fieldId", "fieldtype": "jira", "fromString": "old summary", "toString": "new summary" } ] }, { "author": { "accountId": "5b10a2844c20165700ede21g", "active": true, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "emailAddress": "mia@example.com", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g", "timeZone": "Australia/Sydney" }, "created": 1492071429, "id": "10002", "items": [ { "field": "fields", "fieldId": "fieldId", "fieldtype": "jira", "fromString": "old summary 2", "toString": "new summary 2" } ] } ], "issueId": "10100" } ], "nextPageToken": "UxAQBFRF" }`

GET

## Get eventsExperimental

Returns all issue events.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** _Administer Jira_ [global permission](https://confluence.atlassian.com/x/x4dKLg).

##### Scopes

**Classic**RECOMMENDED:`manage:jira-configuration`

**Granular**:`read:issue-event:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `ADMIN`

### Request

This request has no parameters.

### Responses

Returned if the request is successful.

#### application/json

array<IssueEvent>

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/events`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10` `[ { "id": 1, "name": "Issue Created" }, { "id": 2, "name": "Issue Updated" } ]`

Creates an issue or, where the option to create subtasks is enabled in Jira, a subtask. A transition may be applied, to move the issue or subtask to a workflow step other than the default start step, and issue properties set.

The content of the issue or subtask is defined using `update` and `fields`. The fields that can be set in the issue or subtask are determined using the [Get create issue metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-createmeta-get). These are the same fields that appear on the issue's create screen. Note that the `description`, `environment`, and any `textarea` type custom fields (multi-line text fields) take Atlassian Document Format content. Single line custom fields (`textfield`) accept a string and don't handle Atlassian Document Format content.

Creating a subtask differs from creating an issue as follows:

*   `issueType` must be set to a subtask issue type (use [Get create issue metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-createmeta-get) to find subtask issue types).
*   `parent` must contain the ID or key of the parent issue.

In a next-gen project any issue may be made a child providing that the parent and child are members of the same project.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** _Browse projects_ and _Create issues_ [project permissions](https://confluence.atlassian.com/x/yodKLg) for the project in which the issue or subtask is created.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`write:issue:jira`, `write:comment:jira`, `write:comment.property:jira`, `write:attachment:jira`, `read:issue:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

### Request

#### Query parameters

#### Request bodyapplication/json

**historyMetadata**

HistoryMetadata

**properties**

array<EntityProperty>

**transition**

IssueTransition

### Responses

Returned if the request is successful.

#### application/json

CreatedIssue

Details about a created issue or subtask.

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "fields": { "assignee": { "id": "5b109f2e9729b51b54dc274d" }, "components": [ { "id": "10000" } ], "customfield_10000": "09/Jun/19", "customfield_20000": "06/Jul/19 3:25 PM", "customfield_30000": [ "10000", "10002" ], "customfield_40000": { "content": [ { "content": [ { "text": "Occurs on all orders", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "customfield_50000": { "content": [ { "content": [ { "text": "Could impact day-to-day work.", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "customfield_60000": "jira-software-users", "customfield_70000": [ "jira-administrators", "jira-software-users" ], "customfield_80000": { "value": "red" }, "description": { "content": [ { "content": [ { "text": "Order entry fails when selecting supplier.", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "duedate": "2019-05-11", "environment": { "content": [ { "content": [ { "text": "UAT", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "fixVersions": [ { "id": "10001" } ], "issuetype": { "id": "10000" }, "labels": [ "bugfix", "blitz_test" ], "parent": { "key": "PROJ-123" }, "priority": { "id": "20000" }, "project": { "id": "10000" }, "reporter": { "id": "5b10a2844c20165700ede21g" }, "security": { "id": "10000" }, "summary": "Main order flow broken", "timetracking": { "originalEstimate": "10", "remainingEstimate": "5" }, "versions": [ { "id": "10000" } ] }, "update": {} }`; const response = await requestJira(`/rest/api/3/issue`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12` `{ "id": "10000", "key": "ED-24", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10000", "transition": { "status": 200, "errorCollection": { "errorMessages": [], "errors": {} } } }`

PUT

## Archive issue(s) by issue ID/keyExperimental

Enables admins to archive up to 1000 issues in a single request using issue ID/key, returning details of the issue(s) archived in the process and the errors encountered, if any.

**Note that:**

*   you can't archive subtasks directly, only through their parent issues
*   you can only archive issues from software, service management, and business projects

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Jira admin or site admin: [global permission](https://confluence.atlassian.com/x/x4dKLg)

**License required:** Premium or Enterprise

**Signed-in users only:** This API can't be accessed anonymously.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`write:issue:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

### Request

#### Request bodyapplication/json

Contains a list of issue keys or IDs to be archived.

**issueIdsOrKeys**

array<string>

### Responses

Returned if there is at least one valid issue to archive in the request. The return message will include the count of archived issues and subtasks, as well as error details for issues which failed to get archived.

#### application/json

IssueArchivalSyncResponse

Number of archived/unarchived issues and list of errors that occurred during the action, if any.

PUT/rest/api/3/issue/archive

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "issueIdsOrKeys": [ "PR-1", "1001", "PROJECT-2" ] }`; const response = await requestJira(`/rest/api/3/issue/archive`, { method: 'PUT', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40` `{ "errors": { "issueIsSubtask": { "count": 3, "issueIdsOrKeys": [ "ST-1", "ST-2", "ST-3" ], "message": "Issue is subtask." }, "issuesInArchivedProjects": { "count": 2, "issueIdsOrKeys": [ "AR-1", "AR-2" ], "message": "Issue exists in archived project." }, "issuesInUnlicensedProjects": { "count": 3, "issueIdsOrKeys": [ "UL-1", "UL-2", "UL-3" ], "message": "Issues with these IDs are in unlicensed projects." }, "issuesNotFound": { "count": 3, "issueIdsOrKeys": [ "PR-1", "PR-2", "PR-3" ], "message": "Issue not found." } }, "numberOfIssuesUpdated": 10 }`

POST

## Archive issue(s) by JQLExperimental

Enables admins to archive up to 100,000 issues in a single request using JQL, returning the URL to check the status of the submitted request.

You can use the [get task](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-tasks/#api-rest-api-3-task-taskid-get) and [cancel task](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-tasks/#api-rest-api-3-task-taskid-cancel-post) APIs to manage the request.

**Note that:**

*   you can't archive subtasks directly, only through their parent issues
*   you can only archive issues from software, service management, and business projects

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Jira admin or site admin: [global permission](https://confluence.atlassian.com/x/x4dKLg)

**License required:** Premium or Enterprise

**Signed-in users only:** This API can't be accessed anonymously.

**Rate limiting:** Only a single request per jira instance can be active at any given time.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`write:issue:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

### Request

#### Request bodyapplication/json

A JQL query specifying the issues to archive. Note that subtasks can only be archived through their parent issues.

### Responses

Returns the URL to check the status of the submitted request.

POST/rest/api/3/issue/archive

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "jql": "project = FOO AND updated < -2y" }`; const response = await requestJira(`/rest/api/3/issue/archive`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1` `"https://your-domain.atlassian.net/rest/api/3/task/1010"`

Creates upto **50** issues and, where the option to create subtasks is enabled in Jira, subtasks. Transitions may be applied, to move the issues or subtasks to a workflow step other than the default start step, and issue properties set.

The content of each issue or subtask is defined using `update` and `fields`. The fields that can be set in the issue or subtask are determined using the [Get create issue metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-createmeta-get). These are the same fields that appear on the issues' create screens. Note that the `description`, `environment`, and any `textarea` type custom fields (multi-line text fields) take Atlassian Document Format content. Single line custom fields (`textfield`) accept a string and don't handle Atlassian Document Format content.

Creating a subtask differs from creating an issue as follows:

*   `issueType` must be set to a subtask issue type (use [Get create issue metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-createmeta-get) to find subtask issue types).
*   `parent` the must contain the ID or key of the parent issue.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** _Browse projects_ and _Create issues_ [project permissions](https://confluence.atlassian.com/x/yodKLg) for the project in which each issue or subtask is created.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`write:issue:jira`, `write:comment:jira`, `write:comment.property:jira`, `write:attachment:jira`, `read:issue:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

### Request

#### Request bodyapplication/json

**issueUpdates**

array<IssueUpdateDetails>

### Responses

Returned if any of the issue or subtask creation requests were successful. A request may be unsuccessful when it:

*   is missing required fields.
*   contains invalid field values.
*   contains fields that cannot be set for the issue type.
*   is by a user who does not have the necessary permission.
*   is to create a subtype in a project different that of the parent issue.
*   is for a subtask when the option to create subtasks is disabled.
*   is invalid for any other reason.

#### application/json

CreatedIssues

Details about the issues created and the errors for requests that failed.

POST/rest/api/3/issue/bulk

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222 223 224 225 226 227 228 229 230 231 232 233 234 235 236 237 238 239 240 241 242 243 244 245 246 247 248 249 250 251 252 253 254 255 256 257 258 259 260 261 262 263 264 265 266 267 268 269 270 271 272` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "issueUpdates": [ { "fields": { "assignee": { "id": "5b109f2e9729b51b54dc274d" }, "components": [ { "id": "10000" } ], "customfield_10000": "09/Jun/19", "customfield_20000": "06/Jul/19 3:25 PM", "customfield_30000": [ "10000", "10002" ], "customfield_40000": { "content": [ { "content": [ { "text": "Occurs on all orders", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "customfield_50000": { "content": [ { "content": [ { "text": "Could impact day-to-day work.", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "customfield_60000": "jira-software-users", "customfield_70000": [ "jira-administrators", "jira-software-users" ], "customfield_80000": { "value": "red" }, "description": { "content": [ { "content": [ { "text": "Order entry fails when selecting supplier.", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "duedate": "2011-03-11", "environment": { "content": [ { "content": [ { "text": "UAT", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "fixVersions": [ { "id": "10001" } ], "issuetype": { "id": "10000" }, "labels": [ "bugfix", "blitz_test" ], "priority": { "id": "20000" }, "project": { "id": "10000" }, "reporter": { "id": "5b10a2844c20165700ede21g" }, "security": { "id": "10000" }, "summary": "Main order flow broken", "timetracking": { "originalEstimate": "10", "remainingEstimate": "5" }, "versions": [ { "id": "10000" } ] }, "update": { "worklog": [ { "add": { "started": "2019-07-05T11:05:00.000+0000", "timeSpent": "60m" } } ] } }, { "fields": { "assignee": { "id": "5b109f2e9729b51b54dc274d" }, "components": [ { "id": "10000" } ], "customfield_10000": "09/Jun/19", "customfield_20000": "06/Jul/19 3:25 PM", "customfield_30000": [ "10000", "10002" ], "customfield_40000": { "content": [ { "content": [ { "text": "Occurs on all orders", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "customfield_50000": { "content": [ { "content": [ { "text": "Could impact day-to-day work.", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "customfield_60000": "jira-software-users", "customfield_70000": [ "jira-administrators", "jira-software-users" ], "customfield_80000": { "value": "red" }, "description": { "content": [ { "content": [ { "text": "Order remains pending after approved.", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "duedate": "2019-04-16", "environment": { "content": [ { "content": [ { "text": "UAT", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "fixVersions": [ { "id": "10001" } ], "issuetype": { "id": "10000" }, "labels": [ "new_release" ], "priority": { "id": "20000" }, "project": { "id": "1000" }, "reporter": { "id": "5b10a2844c20165700ede21g" }, "security": { "id": "10000" }, "summary": "Order stuck in pending", "timetracking": { "originalEstimate": "15", "remainingEstimate": "5" }, "versions": [ { "id": "10000" } ] }, "update": {} } ] }`; const response = await requestJira(`/rest/api/3/issue/bulk`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22` `{ "issues": [ { "id": "10000", "key": "ED-24", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10000", "transition": { "status": 200, "errorCollection": { "errorMessages": [], "errors": {} } } }, { "id": "10001", "key": "ED-25", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10001" } ], "errors": [] }`

Returns the details for a set of requested issues. You can request up to 100 issues.

Each issue is identified by its ID or key, however, if the identifier doesn't match an issue, a case-insensitive search and check for moved issues is performed. If a matching issue is found its details are returned, a 302 or other redirect is **not** returned.

Issues will be returned in ascending `id` order. If there are errors, Jira will return a list of issues which couldn't be fetched along with error messages.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Issues are included in the response where the user has:

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-meta:jira`, `read:issue-security-level:jira`, `read:issue.vote:jira`, `read:issue.changelog:jira`, `read:avatar:jira` ...(Show more)

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Request bodyapplication/json

A JSON object containing the information about which issues and fields to fetch.

**issueIdsOrKeys**

array<string>

Required

### Responses

Returned if the request is successful. A response may contain both successful issues and issue errors.

#### application/json

BulkIssueResults

The list of requested issues & fields.

POST/rest/api/3/issue/bulkfetch

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "expand": [ "names" ], "fields": [ "summary", "project", "assignee" ], "fieldsByKeys": false, "issueIdsOrKeys": [ "EX-1", "EX-2", "10005" ], "properties": [] }`; const response = await requestJira(`/rest/api/3/issue/bulkfetch`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165` `{ "expand": "schema,names", "issueErrors": [], "issues": [ { "expand": "", "fields": { "summary": "My first example issue", "project": { "avatarUrls": { "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10000", "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10000", "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10000", "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10000" }, "id": "10000", "insight": { "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000", "totalIssueCount": 100 }, "key": "EX", "name": "Example", "projectCategory": { "description": "First Project Category", "id": "10000", "name": "FIRST", "self": "https://your-domain.atlassian.net/rest/api/3/projectCategory/10000" }, "self": "https://your-domain.atlassian.net/rest/api/3/project/EX", "simplified": false, "style": "classic" }, "assignee": { "accountId": "5b10a2844c20165700ede21g", "active": true, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "emailAddress": "mia@example.com", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g", "timeZone": "Australia/Sydney" } }, "id": "10002", "key": "EX-1", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10002" }, { "expand": "", "fields": { "summary": "My second example issue", "project": { "avatarUrls": { "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10001", "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10001", "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10001", "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10001" }, "id": "10001", "insight": { "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000", "totalIssueCount": 100 }, "key": "ABC", "name": "Alphabetical", "projectCategory": { "description": "First Project Category", "id": "10000", "name": "FIRST", "self": "https://your-domain.atlassian.net/rest/api/3/projectCategory/10000" }, "self": "https://your-domain.atlassian.net/rest/api/3/project/ABC", "simplified": false, "style": "classic" }, "assignee": { "accountId": "5b10a2844c20165700ede21g", "active": true, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "emailAddress": "mia@example.com", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g", "timeZone": "Australia/Sydney" } }, "id": "10005", "key": "EX-2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10003" }, { "expand": "", "fields": { "summary": "My fourth example issue", "project": { "avatarUrls": { "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10002", "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10002", "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10002", "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10002" }, "deleted": true, "deletedBy": { "accountId": "5b10a2844c20165700ede21g", "accountType": "atlassian", "active": false, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "key": "", "name": "", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "deletedDate": "2022-11-11T13:35:29.000+0000", "id": "10002", "insight": { "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000", "totalIssueCount": 100 }, "key": "MKY", "name": "Example", "projectCategory": { "description": "First Project Category", "id": "10000", "name": "FIRST", "self": "https://your-domain.atlassian.net/rest/api/3/projectCategory/10000" }, "retentionTillDate": "2023-01-10T13:35:29.000+0000", "self": "https://your-domain.atlassian.net/rest/api/3/project/MKY", "simplified": false, "style": "classic" }, "assignee": { "accountId": "5b10a2844c20165700ede21g", "active": true, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "emailAddress": "mia@example.com", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g", "timeZone": "Australia/Sydney" } }, "id": "10005", "key": "EX-4", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10005" } ] }`

Returns details of projects, issue types within projects, and, when requested, the create screen fields for each issue type for the user. Use the information to populate the requests in [Create issue](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post) and [Create issues](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-bulk-post).

Deprecated, see [Create Issue Meta Endpoint Deprecation Notice](https://developer.atlassian.com/cloud/jira/platform/changelog/#CHANGE-1304).

The request can be restricted to specific projects or issue types using the query parameters. The response will contain information for the valid projects, issue types, or project and issue type combinations requested. Note that invalid project, issue type, or project and issue type combinations do not generate errors.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** _Create issues_ [project permission](https://confluence.atlassian.com/x/yodKLg) in the requested projects.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-meta:jira`, `read:avatar:jira`, `read:field-configuration:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Query parameters

**issuetypeIds**

array<string>

**issuetypeNames**

array<string>

### Responses

Returned if the request is successful.

#### application/json

IssueCreateMetadata

The wrapper for the issue creation metadata for a list of projects.

GET/rest/api/3/issue/createmeta

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/createmeta`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38` `{ "projects": [ { "avatarUrls": { "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10000&avatarId=10011", "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10000&avatarId=10011", "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10000&avatarId=10011", "48x48": "https://your-domain.atlassian.net/secure/projectavatar?pid=10000&avatarId=10011" }, "id": "10000", "issuetypes": [ { "description": "An error in the code", "fields": { "issuetype": { "allowedValues": [ "set" ], "autoCompleteUrl": "issuetype", "hasDefaultValue": false, "key": "issuetype", "name": "Issue Type", "required": true } }, "iconUrl": "https://your-domain.atlassian.net/images/icons/issuetypes/bug.png", "id": "1", "name": "Bug", "self": "https://your-domain.atlassian.net/rest/api/3/issueType/1", "subtask": false } ], "key": "ED", "name": "Edison Project", "self": "https://your-domain.atlassian.net/rest/api/3/project/ED" } ] }`

Returns a page of issue type metadata for a specified project. Use the information to populate the requests in [Create issue](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post) and [Create issues](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-bulk-post).

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** _Create issues_ [project permission](https://confluence.atlassian.com/x/yodKLg) in the requested projects.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-meta:jira`, `read:avatar:jira`, `read:field-configuration:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Path parameters

**projectIdOrKey**

string

Required

#### Query parameters

### Responses

Returned if the request is successful.

#### application/json

PageOfCreateMetaIssueTypes

A page of CreateMetaIssueTypes.

GET/rest/api/3/issue/createmeta/{projectIdOrKey}/issuetypes

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/createmeta/{projectIdOrKey}/issuetypes`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15` `{ "issueTypes": [ { "description": "An error in the code", "iconUrl": "https://your-domain.atlassian.net/images/icons/issuetypes/bug.png", "id": "1", "name": "Bug", "self": "https://your-domain.atlassian.net/rest/api/3/issueType/1", "subtask": false } ], "maxResults": 1, "startAt": 0, "total": 1 }`

Returns a page of field metadata for a specified project and issuetype id. Use the information to populate the requests in [Create issue](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post) and [Create issues](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-bulk-post).

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** _Create issues_ [project permission](https://confluence.atlassian.com/x/yodKLg) in the requested projects.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-meta:jira`, `read:avatar:jira`, `read:field-configuration:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Path parameters

**projectIdOrKey**

string

Required

**issueTypeId**

string

Required

#### Query parameters

### Responses

Returned if the request is successful.

#### application/json

PageOfCreateMetaIssueTypeWithField

A page of CreateMetaIssueType with Field.

GET/rest/api/3/issue/createmeta/{projectIdOrKey}/issuetypes/{issueTypeId}

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/createmeta/{projectIdOrKey}/issuetypes/{issueTypeId}`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17` `{ "fields": [ { "fieldId": "assignee", "hasDefaultValue": false, "key": "assignee", "name": "Assignee", "operations": [ "set" ], "required": true } ], "maxResults": 1, "startAt": 0, "total": 1 }`

GET

## Get issue limit reportExperimental

Returns all issues breaching and approaching per-issue limits.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) is required for the project the issues are in. Results may be incomplete otherwise
*   _Administer Jira_ [global permission](https://confluence.atlassian.com/x/x4dKLg).

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:project:jira`, `read:issue:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Query parameters

### Responses

Returned if the request is successful.

#### application/json

IssueLimitReportResponseBean

GET/rest/api/3/issue/limit/report

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/limit/report?isReturningKeys={isReturningKeys}`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46` `{ "issuesApproachingLimit": { "attachment": { "15070L": 1822, "15111L": 1999 }, "comment": { "10000L": 4997, "15073L": 4999, "15110L": 5000 }, "remoteIssueLinks": { "15107L": 2000 }, "worklog": { "15101L": 10342 } }, "issuesBreachingLimit": { "attachment": { "15057L": 2005, "15116L": 2065, "15117L": 3005 }, "comment": { "15055L": 5202 }, "issuelinks": { "15058L": 2120 }, "remoteIssueLinks": { "15059L": 2094 }, "worklog": { "15056L": 10085, "15169L": 120864 } }, "limits": { "attachment": 2000, "comment": 5000, "issuelinks": 2000, "remoteIssueLinks": 2000, "worklog": 10000 } }`

PUT

## Unarchive issue(s) by issue keys/IDExperimental

Enables admins to unarchive up to 1000 issues in a single request using issue ID/key, returning details of the issue(s) unarchived in the process and the errors encountered, if any.

**Note that:**

*   you can't unarchive subtasks directly, only through their parent issues
*   you can only unarchive issues from software, service management, and business projects

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Jira admin or site admin: [global permission](https://confluence.atlassian.com/x/x4dKLg)

**License required:** Premium or Enterprise

**Signed-in users only:** This API can't be accessed anonymously.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`write:issue:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

### Request

#### Request bodyapplication/json

Contains a list of issue keys or IDs to be unarchived.

**issueIdsOrKeys**

array<string>

### Responses

Returned if there is at least one valid issue to unarchive in the request. It will return the count of unarchived issues, which also includes the count of the subtasks unarchived, and it will show the detailed errors for those issues which are not unarchived.

#### application/json

IssueArchivalSyncResponse

Number of archived/unarchived issues and list of errors that occurred during the action, if any.

PUT/rest/api/3/issue/unarchive

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "issueIdsOrKeys": [ "PR-1", "1001", "PROJECT-2" ] }`; const response = await requestJira(`/rest/api/3/issue/unarchive`, { method: 'PUT', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31` `{ "errors": { "issueIsSubtask": { "count": 3, "issueIdsOrKeys": [ "ST-1", "ST-2", "ST-3" ], "message": "Issue is subtask." }, "issuesInArchivedProjects": { "count": 2, "issueIdsOrKeys": [ "AR-1", "AR-2" ], "message": "Issue exists in archived project." }, "issuesNotFound": { "count": 3, "issueIdsOrKeys": [ "PR-1", "PR-2", "PR-3" ], "message": "Issue not found." } }, "numberOfIssuesUpdated": 10 }`

Returns the details for an issue.

The issue is identified by its ID or key, however, if the identifier doesn't match an issue, a case-insensitive search and check for moved issues is performed. If a matching issue is found its details are returned, a 302 or other redirect is **not** returned. The issue key returned in the response is the key of the issue found.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-meta:jira`, `read:issue-security-level:jira`, `read:issue.vote:jira`, `read:issue.changelog:jira`, `read:avatar:jira` ...(Show more)

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Path parameters

**issueIdOrKey**

string

Required

#### Query parameters

### Responses

Returned if the request is successful.

#### application/json

IssueBean

Details about an issue.

GET/rest/api/3/issue/{issueIdOrKey}

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222 223 224 225 226 227 228 229 230 231 232 233 234` `{ "fields": { "watcher": { "isWatching": false, "self": "https://your-domain.atlassian.net/rest/api/3/issue/EX-1/watchers", "watchCount": 1 }, "attachment": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "accountType": "atlassian", "active": false, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "key": "", "name": "", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "content": "https://your-domain.atlassian.net/jira/rest/api/3/attachment/content/10000", "created": "2022-10-06T07:32:47.000+0000", "filename": "picture.jpg", "id": 10000, "mimeType": "image/jpeg", "self": "https://your-domain.atlassian.net/rest/api/3/attachments/10000", "size": 23123, "thumbnail": "https://your-domain.atlassian.net/jira/rest/api/3/attachment/thumbnail/10000" } ], "sub-tasks": [ { "id": "10000", "outwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10003", "key": "ED-2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/ED-2" }, "type": { "id": "10000", "inward": "Parent", "name": "", "outward": "Sub-task" } } ], "description": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "Main order flow broken" } ] } ] }, "project": { "avatarUrls": { "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10000", "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10000", "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10000", "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10000" }, "id": "10000", "insight": { "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000", "totalIssueCount": 100 }, "key": "EX", "name": "Example", "projectCategory": { "description": "First Project Category", "id": "10000", "name": "FIRST", "self": "https://your-domain.atlassian.net/rest/api/3/projectCategory/10000" }, "self": "https://your-domain.atlassian.net/rest/api/3/project/EX", "simplified": false, "style": "classic" }, "comment": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "body": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper." } ] } ] }, "created": "2021-01-17T12:34:00.000+0000", "id": "10000", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000", "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } } ], "issuelinks": [ { "id": "10001", "outwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10004L", "key": "PR-2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/PR-2" }, "type": { "id": "10000", "inward": "depends on", "name": "Dependent", "outward": "is depended by" } }, { "id": "10002", "inwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10004", "key": "PR-3", "self": "https://your-domain.atlassian.net/rest/api/3/issue/PR-3" }, "type": { "id": "10000", "inward": "depends on", "name": "Dependent", "outward": "is depended by" } } ], "worklog": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "comment": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "I did some work here." } ] } ] }, "id": "100028", "issueId": "10002", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/worklog/10000", "started": "2021-01-17T12:34:00.000+0000", "timeSpent": "3h 20m", "timeSpentSeconds": 12000, "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "276f955c-63d7-42c8-9520-92d01dca0625", "type": "group", "value": "jira-developers" } } ], "updated": 1, "timetracking": { "originalEstimate": "10m", "originalEstimateSeconds": 600, "remainingEstimate": "3m", "remainingEstimateSeconds": 200, "timeSpent": "6m", "timeSpentSeconds": 400 } }, "id": "10002", "key": "ED-1", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10002" }`

Edits an issue. Issue properties may be updated as part of the edit. Please note that issue transition is not supported and is ignored here. To transition an issue, please use [Transition issue](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-post).

The edits to the issue's fields are defined using `update` and `fields`. The fields that can be edited are determined using [Get edit issue metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-editmeta-get).

The parent field may be set by key or ID. For standard issue types, the parent may be removed by setting `update.parent.set.none` to _true_. Note that the `description`, `environment`, and any `textarea` type custom fields (multi-line text fields) take Atlassian Document Format content. Single line custom fields (`textfield`) accept a string and don't handle Atlassian Document Format content.

Connect apps having an app user with _Administer Jira_ [global permission](https://confluence.atlassian.com/x/x4dKLg), and Forge apps acting on behalf of users with _Administer Jira_ [global permission](https://confluence.atlassian.com/x/x4dKLg), can override the screen security configuration using `overrideScreenSecurity` and `overrideEditableFlag`.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ and _Edit issues_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`write:issue:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

### Request

#### Path parameters

**issueIdOrKey**

string

Required

#### Query parameters

**overrideScreenSecurity**

boolean

**overrideEditableFlag**

boolean

#### Request bodyapplication/json

**historyMetadata**

HistoryMetadata

**properties**

array<EntityProperty>

**transition**

IssueTransition

### Responses

Returned if the request is successful and the `returnIssue` parameter is `true`

PUT/rest/api/3/issue/{issueIdOrKey}

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "fields": { "customfield_10000": { "content": [ { "content": [ { "text": "Investigation underway", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "customfield_10010": 1, "summary": "Completed orders still displaying in pending" }, "historyMetadata": { "activityDescription": "Complete order processing", "actor": { "avatarUrl": "http://mysystem/avatar/tony.jpg", "displayName": "Tony", "id": "tony", "type": "mysystem-user", "url": "http://mysystem/users/tony" }, "cause": { "id": "myevent", "type": "mysystem-event" }, "description": "From the order testing process", "extraData": { "Iteration": "10a", "Step": "4" }, "generator": { "id": "mysystem-1", "type": "mysystem-application" }, "type": "myplugin:type" }, "properties": [ { "key": "key1", "value": "Order number 10784" }, { "key": "key2", "value": "Order number 10923" } ], "update": { "components": [ { "set": "" } ], "labels": [ { "add": "triaged" }, { "remove": "blocker" } ], "summary": [ { "set": "Bug in business logic" } ], "timetracking": [ { "edit": { "originalEstimate": "1w 1d", "remainingEstimate": "4d" } } ] } }`; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}`, { method: 'PUT', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

Deletes an issue.

An issue cannot be deleted if it has one or more subtasks. To delete an issue with subtasks, set `deleteSubtasks`. This causes the issue's subtasks to be deleted with the issue.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ and _Delete issues_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project containing the issue.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`delete:issue:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `DELETE`

### Request

#### Path parameters

**issueIdOrKey**

string

Required

#### Query parameters

### Responses

Returned if the request is successful.

DEL/rest/api/3/issue/{issueIdOrKey}

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}`, { method: 'DELETE' }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.text());``

Assigns an issue to a user. Use this operation when the calling user does not have the _Edit Issues_ permission but has the _Assign issue_ permission for the project that the issue is in.

If `name` or `accountId` is set to:

*   `"-1"`, the issue is assigned to the default assignee for the project.
*   `null`, the issue is set to unassigned.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse Projects_ and _Assign Issues_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`write:issue:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

### Request

#### Path parameters

**issueIdOrKey**

string

Required

#### Request bodyapplication/json

The request object with the user that the issue is assigned to.

### Responses

Returned if the request is successful.

PUT/rest/api/3/issue/{issueIdOrKey}/assignee

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "accountId": "5b10ac8d82e05b22cc7d4ef5" }`; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/assignee`, { method: 'PUT', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

Returns a [paginated](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#pagination) list of all changelogs for an issue sorted by date, starting from the oldest.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-meta:jira`, `read:avatar:jira`, `read:issue.changelog:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Path parameters

**issueIdOrKey**

string

Required

#### Query parameters

### Responses

Returned if the request is successful.

#### application/json

PageBeanChangelog

A page of items.

GET/rest/api/3/issue/{issueIdOrKey}/changelog

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/changelog`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68` `{ "isLast": false, "maxResults": 2, "nextPage": "https://your-domain.atlassian.net/rest/api/3/issue/TT-1/changelog?&startAt=4&maxResults=2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/TT-1/changelog?startAt=2&maxResults=2", "startAt": 2, "total": 5, "values": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": true, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "emailAddress": "mia@example.com", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g", "timeZone": "Australia/Sydney" }, "created": "1970-01-18T06:27:50.429+0000", "id": "10001", "items": [ { "field": "fields", "fieldtype": "jira", "fieldId": "fieldId", "from": null, "fromString": "", "to": null, "toString": "label-1" } ] }, { "author": { "accountId": "5b10a2844c20165700ede21g", "active": true, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "emailAddress": "mia@example.com", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g", "timeZone": "Australia/Sydney" }, "created": "1970-01-18T06:27:51.429+0000", "id": "10002", "items": [ { "field": "fields", "fieldtype": "jira", "fieldId": "fieldId", "from": null, "fromString": "label-1", "to": null, "toString": "label-1 label-2" } ] } ] }`

POST

## Get changelogs by IDs

Returns changelogs for an issue specified by a list of changelog IDs.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-meta:jira`, `read:avatar:jira`, `read:issue.changelog:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

### Request

#### Path parameters

**issueIdOrKey**

string

Required

#### Request bodyapplication/json

**changelogIds**

array<integer>

Required

### Responses

Returned if the request is successful.

#### application/json

PageOfChangelogs

A page of changelogs.

POST/rest/api/3/issue/{issueIdOrKey}/changelog/list

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "changelogIds": [ 10001, 10002 ] }`; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/changelog/list`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65` `{ "histories": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": true, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "emailAddress": "mia@example.com", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g", "timeZone": "Australia/Sydney" }, "created": "1970-01-18T06:27:50.429+0000", "id": "10001", "items": [ { "field": "fields", "fieldtype": "jira", "fieldId": "fieldId", "from": null, "fromString": "", "to": null, "toString": "label-1" } ] }, { "author": { "accountId": "5b10a2844c20165700ede21g", "active": true, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "emailAddress": "mia@example.com", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g", "timeZone": "Australia/Sydney" }, "created": "1970-01-18T06:27:51.429+0000", "id": "10002", "items": [ { "field": "fields", "fieldtype": "jira", "fieldId": "fieldId", "from": null, "fromString": "label-1", "to": null, "toString": "label-1 label-2" } ] } ], "maxResults": 2, "startAt": 0, "total": 2 }`

Returns the edit screen fields for an issue that are visible to and editable by the user. Use the information to populate the requests in [Edit issue](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-put).

This endpoint will check for these conditions:

1.  Field is available on a field screen - through screen, screen scheme, issue type screen scheme, and issue type scheme configuration. `overrideScreenSecurity=true` skips this condition.
2.  Field is visible in the [field configuration](https://support.atlassian.com/jira-cloud-administration/docs/change-a-field-configuration/). `overrideScreenSecurity=true` skips this condition.
3.  Field is shown on the issue: each field has different conditions here. For example: Attachment field only shows if attachments are enabled. Assignee only shows if user has permissions to assign the issue.
4.  If a field is custom then it must have valid custom field context, applicable for its project and issue type. All system fields are assumed to have context in all projects and all issue types.
5.  Issue has a project, issue type, and status defined.
6.  Issue is assigned to a valid workflow, and the current status has assigned a workflow step. `overrideEditableFlag=true` skips this condition.
7.  The current workflow step is editable. This is true by default, but [can be disabled by setting](https://support.atlassian.com/jira-cloud-administration/docs/use-workflow-properties/) the `jira.issue.editable` property to `false`. `overrideEditableFlag=true` skips this condition.
8.  User has [Edit issues permission](https://support.atlassian.com/jira-cloud-administration/docs/permissions-for-company-managed-projects/).
9.  Workflow permissions allow editing a field. This is true by default but [can be modified](https://support.atlassian.com/jira-cloud-administration/docs/use-workflow-properties/) using `jira.permission.*` workflow properties.

Fields hidden using [Issue layout settings page](https://support.atlassian.com/jira-software-cloud/docs/configure-field-layout-in-the-issue-view/) remain editable.

Connect apps having an app user with _Administer Jira_ [global permission](https://confluence.atlassian.com/x/x4dKLg), and Forge apps acting on behalf of users with _Administer Jira_ [global permission](https://confluence.atlassian.com/x/x4dKLg), can return additional details using:

*   `overrideScreenSecurity` When this flag is `true`, then this endpoint skips checking if fields are available through screens, and field configuration (conditions 1. and 2. from the list above).
*   `overrideEditableFlag` When this flag is `true`, then this endpoint skips checking if workflow is present and if the current step is editable (conditions 6. and 7. from the list above).

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

Note: For any fields to be editable the user must have the _Edit issues_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the issue.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-meta:jira`, `read:field-configuration:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Path parameters

**issueIdOrKey**

string

Required

#### Query parameters

**overrideScreenSecurity**

boolean

**overrideEditableFlag**

boolean

### Responses

Returned if the request is successful.

#### application/json

IssueUpdateMetadata

A list of editable field details.

GET/rest/api/3/issue/{issueIdOrKey}/editmeta

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/editmeta`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25` `{ "fields": { "summary": { "allowedValues": [ "red", "blue" ], "defaultValue": "red", "hasDefaultValue": false, "key": "field_key", "name": "My Multi Select", "operations": [ "set", "add" ], "required": false, "schema": { "custom": "com.atlassian.jira.plugin.system.customfieldtypes:multiselect", "customId": 10001, "items": "option", "type": "array" } } } }`

POST

## Send notification for issue

Creates an email notification for an issue and adds it to the mail queue.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse Projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`send:notification:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

### Request

#### Path parameters

**issueIdOrKey**

string

Required

#### Request bodyapplication/json

The request object for the notification and recipients.

**restrict**

NotificationRecipientsRestrictions

### Responses

Returned if the email is queued for sending.

POST/rest/api/3/issue/{issueIdOrKey}/notify

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "htmlBody": "The <strong>latest</strong> test results for this ticket are now available.", "restrict": { "groupIds": [], "groups": [ { "name": "notification-group" } ], "permissions": [ { "key": "BROWSE" } ] }, "subject": "Latest test results", "textBody": "The latest test results for this ticket are now available.", "to": { "assignee": false, "groupIds": [], "groups": [ { "name": "notification-group" } ], "reporter": false, "users": [ { "accountId": "5b10a2844c20165700ede21g", "active": false } ], "voters": true, "watchers": true } }`; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/notify`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

Returns either all transitions or a transition that can be performed by the user on an issue, based on the issue's status.

Note, if a request is made for a transition that does not exist or cannot be performed on the issue, given its status, the response will return any empty transitions list.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required: A list or transition is returned only when the user has:**

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

However, if the user does not have the _Transition issues_ [project permission](https://confluence.atlassian.com/x/yodKLg) the response will not list any transitions.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue.transition:jira`, `read:status:jira`, `read:field-configuration:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Path parameters

**issueIdOrKey**

string

Required

#### Query parameters

**skipRemoteOnlyCondition**

boolean

**includeUnavailableTransitions**

boolean

**sortByOpsBarAndStatus**

boolean

### Responses

Returned if the request is successful.

#### application/json

Transitions

List of issue transitions.

GET/rest/api/3/issue/{issueIdOrKey}/transitions

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/transitions`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112` `{ "transitions": [ { "fields": { "summary": { "allowedValues": [ "red", "blue" ], "defaultValue": "red", "hasDefaultValue": false, "key": "field_key", "name": "My Multi Select", "operations": [ "set", "add" ], "required": false, "schema": { "custom": "com.atlassian.jira.plugin.system.customfieldtypes:multiselect", "customId": 10001, "items": "option", "type": "array" } } }, "hasScreen": false, "id": "2", "isAvailable": true, "isConditional": false, "isGlobal": false, "isInitial": false, "name": "Close Issue", "to": { "description": "The issue is currently being worked on.", "iconUrl": "https://your-domain.atlassian.net/images/icons/progress.gif", "id": "10000", "name": "In Progress", "self": "https://your-domain.atlassian.net/rest/api/3/status/10000", "statusCategory": { "colorName": "yellow", "id": 1, "key": "in-flight", "name": "In Progress", "self": "https://your-domain.atlassian.net/rest/api/3/statuscategory/1" } } }, { "fields": { "summary": { "allowedValues": [ "red", "blue" ], "defaultValue": "red", "hasDefaultValue": false, "key": "field_key", "name": "My Multi Select", "operations": [ "set", "add" ], "required": false, "schema": { "custom": "com.atlassian.jira.plugin.system.customfieldtypes:multiselect", "customId": 10001, "items": "option", "type": "array" } }, "colour": { "allowedValues": [ "red", "blue" ], "defaultValue": "red", "hasDefaultValue": false, "key": "field_key", "name": "My Multi Select", "operations": [ "set", "add" ], "required": false, "schema": { "custom": "com.atlassian.jira.plugin.system.customfieldtypes:multiselect", "customId": 10001, "items": "option", "type": "array" } } }, "hasScreen": true, "id": "711", "name": "QA Review", "to": { "description": "The issue is closed.", "iconUrl": "https://your-domain.atlassian.net/images/icons/closed.gif", "id": "5", "name": "Closed", "self": "https://your-domain.atlassian.net/rest/api/3/status/5", "statusCategory": { "colorName": "green", "id": 9, "key": "completed", "self": "https://your-domain.atlassian.net/rest/api/3/statuscategory/9" } } } ] }`

Performs an issue transition and, if the transition has a screen, updates the fields from the transition screen.

sortByCategory To update the fields on the transition screen, specify the fields in the `fields` or `update` parameters in the request body. Get details about the fields using [Get transitions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-get) with the `transitions.fields` expand.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ and _Transition issues_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`write:issue:jira`, `write:issue.property:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

### Request

#### Path parameters

**issueIdOrKey**

string

Required

#### Request bodyapplication/json

**historyMetadata**

HistoryMetadata

**properties**

array<EntityProperty>

**transition**

IssueTransition

### Responses

Returned if the request is successful.

POST/rest/api/3/issue/{issueIdOrKey}/transitions

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "fields": { "assignee": { "name": "bob" }, "resolution": { "name": "Fixed" } }, "historyMetadata": { "activityDescription": "Complete order processing", "actor": { "avatarUrl": "http://mysystem/avatar/tony.jpg", "displayName": "Tony", "id": "tony", "type": "mysystem-user", "url": "http://mysystem/users/tony" }, "cause": { "id": "myevent", "type": "mysystem-event" }, "description": "From the order testing process", "extraData": { "Iteration": "10a", "Step": "4" }, "generator": { "id": "mysystem-1", "type": "mysystem-application" }, "type": "myplugin:type" }, "transition": { "id": "5" }, "update": { "comment": [ { "add": { "body": { "content": [ { "content": [ { "text": "Bug has been fixed", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 } } } ] } }`; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/transitions`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

PUT

## Export archived issue(s)Experimental

Enables admins to retrieve details of all archived issues. Upon a successful request, the admin who submitted it will receive an email with a link to download a CSV file with the issue details.

Note that this API only exports the values of system fields and archival-specific fields (`ArchivedBy` and `ArchivedDate`). Custom fields aren't supported.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Jira admin or site admin: [global permission](https://confluence.atlassian.com/x/x4dKLg)

**License required:** Premium or Enterprise

**Signed-in users only:** This API can't be accessed anonymously.

**Rate limiting:** Only a single request can be active at any given time.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Request bodyapplication/json

You can filter the issues in your request by the `projects`, `archivedBy`, `archivedDate`, `issueTypes`, and `reporters` fields. All filters are optional. If you don't provide any filters, you'll get a list of up to one million archived issues.

**archivedDateRange**

DateRangeFilterRequest

### Responses

Returns the details of your export task. You can use the [get task](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-tasks/#api-rest-api-3-task-taskid-get) API to view the progress of your request.

#### application/json

ExportArchivedIssuesTaskProgressResponse

The response for status request for a running/completed export task.

PUT/rest/api/3/issues/archive/export

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "archivedBy": [ "uuid-rep-001", "uuid-rep-002" ], "archivedDate": { "dateAfter": "2023-01-01", "dateBefore": "2023-01-12" }, "archivedDateRange": { "dateAfter": "2023-01-01", "dateBefore": "2023-01-12" }, "issueTypes": [ "10001", "10002" ], "projects": [ "FOO", "BAR" ], "reporters": [ "uuid-rep-001", "uuid-rep-002" ] }`; const response = await requestJira(`/rest/api/3/issues/archive/export`, { method: 'PUT', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7` `{ "payload": "{projects=[FOO, BAR], reporters=[uuid-rep-001, uuid-rep-002], issueTypes=[10001, 10002], archivedDate={dateAfterInstant=2023-01-01, dateBeforeInstant=2023-01-12}, archivedBy=[uuid-rep-001, uuid-rep-002]}", "progress": 0, "status": "ENQUEUED", "submittedTime": 1623230887000, "taskId": "10990" }`