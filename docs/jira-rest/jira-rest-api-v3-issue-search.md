Cloud

Jira Cloud platform / Reference / REST API v3

## Issue search

This resource represents various ways to search for issues. Use it to search for issues with a JQL query and find issues to populate an issue picker.

GET

## Get issue picker suggestions

Returns lists of issues matching a query string. Use this resource to provide auto-completion suggestions when the user is looking for an issue using a word or string.

This operation returns two lists:

*   `History Search` which includes issues from the user's history of created, edited, or viewed issues that contain the string in the `query` parameter.
*   `Current Search` which includes issues that match the JQL expression in `currentJQL` and contain the string in the `query` parameter.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** None.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-details:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Query parameters

### Responses

Returned if the request is successful.

#### application/json

IssuePickerSuggestions

A list of issues suggested for use in auto-completion.

GET/rest/api/3/issue/picker

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/picker?query=query`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20` `{ "sections": [ { "id": "<string>", "issues": [ { "id": 20, "img": "<string>", "key": "<string>", "keyHtml": "<string>", "summary": "<string>", "summaryText": "<string>" } ], "label": "<string>", "msg": "<string>", "sub": "<string>" } ] }`

POST

## Check issues against JQL

Checks whether one or more issues would be returned by one or more JQL queries.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** None, however, issues are only matched against JQL queries where the user has:

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-details:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Request bodyapplication/json

**issueIds**

array<integer>

Required

**jqls**

array<string>

Required

### Responses

Returned if the request is successful.

#### application/json

IssueMatches

A list of matched issues or errors for each JQL query, in the order the JQL queries were passed.

POST/rest/api/3/jql/match

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "issueIds": [ 10001, 1000, 10042 ], "jqls": [ "project = FOO", "issuetype = Bug", "summary ~ \"some text\" AND project in (FOO, BAR)" ] }`; const response = await requestJira(`/rest/api/3/jql/match`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29` `{ "matches": [ { "matchedIssues": [ 10000, 10004 ], "errors": [] }, { "matchedIssues": [ 100134, 10025, 10236 ], "errors": [] }, { "matchedIssues": [], "errors": [] }, { "matchedIssues": [], "errors": [ "Invalid JQL: broken = value" ] } ] }`

GET

## Currently being removed. Search for issues using JQL (GET)Deprecated

Endpoint is currently being removed. [More details](https://developer.atlassian.com/changelog/#CHANGE-2046)

Searches for issues using [JQL](https://confluence.atlassian.com/x/egORLQ).

If the JQL query expression is too large to be encoded as a query parameter, use the [POST](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-post) version of this resource.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Issues are included in the response where the user has:

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project containing the issue.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-details:jira`, `read:audit-log:jira`, `read:avatar:jira`, `read:field-configuration:jira`, `read:issue-meta:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Query parameters

### Responses

Returned if the request is successful.

#### application/json

SearchResults

The result of a JQL search.

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/search?jql=project%20%3D%20HSP`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222 223 224 225 226 227 228 229 230 231 232 233 234 235 236 237 238 239 240 241 242 243 244 245 246` `{ "expand": "names,schema", "issues": [ { "expand": "", "fields": { "watcher": { "isWatching": false, "self": "https://your-domain.atlassian.net/rest/api/3/issue/EX-1/watchers", "watchCount": 1 }, "attachment": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "accountType": "atlassian", "active": false, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "key": "", "name": "", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "content": "https://your-domain.atlassian.net/jira/rest/api/3/attachment/content/10000", "created": "2022-10-06T07:32:47.000+0000", "filename": "picture.jpg", "id": 10000, "mimeType": "image/jpeg", "self": "https://your-domain.atlassian.net/rest/api/3/attachments/10000", "size": 23123, "thumbnail": "https://your-domain.atlassian.net/jira/rest/api/3/attachment/thumbnail/10000" } ], "sub-tasks": [ { "id": "10000", "outwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10003", "key": "ED-2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/ED-2" }, "type": { "id": "10000", "inward": "Parent", "name": "", "outward": "Sub-task" } } ], "description": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "Main order flow broken" } ] } ] }, "project": { "avatarUrls": { "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10000", "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10000", "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10000", "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10000" }, "id": "10000", "insight": { "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000", "totalIssueCount": 100 }, "key": "EX", "name": "Example", "projectCategory": { "description": "First Project Category", "id": "10000", "name": "FIRST", "self": "https://your-domain.atlassian.net/rest/api/3/projectCategory/10000" }, "self": "https://your-domain.atlassian.net/rest/api/3/project/EX", "simplified": false, "style": "classic" }, "comment": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "body": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper." } ] } ] }, "created": "2021-01-17T12:34:00.000+0000", "id": "10000", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000", "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } } ], "issuelinks": [ { "id": "10001", "outwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10004L", "key": "PR-2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/PR-2" }, "type": { "id": "10000", "inward": "depends on", "name": "Dependent", "outward": "is depended by" } }, { "id": "10002", "inwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10004", "key": "PR-3", "self": "https://your-domain.atlassian.net/rest/api/3/issue/PR-3" }, "type": { "id": "10000", "inward": "depends on", "name": "Dependent", "outward": "is depended by" } } ], "worklog": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "comment": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "I did some work here." } ] } ] }, "id": "100028", "issueId": "10002", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/worklog/10000", "started": "2021-01-17T12:34:00.000+0000", "timeSpent": "3h 20m", "timeSpentSeconds": 12000, "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "276f955c-63d7-42c8-9520-92d01dca0625", "type": "group", "value": "jira-developers" } } ], "updated": 1, "timetracking": { "originalEstimate": "10m", "originalEstimateSeconds": 600, "remainingEstimate": "3m", "remainingEstimateSeconds": 200, "timeSpent": "6m", "timeSpentSeconds": 400 } }, "id": "10002", "key": "ED-1", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10002" } ], "maxResults": 50, "startAt": 0, "total": 1, "warningMessages": [ "The value 'bar' does not exist for the field 'foo'." ] }`

POST

## Currently being removed. Search for issues using JQL (POST)Deprecated

Endpoint is currently being removed. [More details](https://developer.atlassian.com/changelog/#CHANGE-2046)

Searches for issues using [JQL](https://confluence.atlassian.com/x/egORLQ).

There is a [GET](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-get) version of this resource that can be used for smaller JQL query expressions.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Issues are included in the response where the user has:

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project containing the issue.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-details:jira`, `read:field.default-value:jira`, `read:field.option:jira`, `read:field:jira`, `read:group:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Request bodyapplication/json

A JSON object containing the search request.

### Responses

Returned if the request is successful.

#### application/json

SearchResults

The result of a JQL search.

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "expand": [ "names", "schema", "operations" ], "fields": [ "summary", "status", "assignee" ], "fieldsByKeys": false, "jql": "project = HSP", "maxResults": 15, "startAt": 0 }`; const response = await requestJira(`/rest/api/3/search`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222 223 224 225 226 227 228 229 230 231 232 233 234 235 236 237 238 239 240 241 242 243 244 245 246` `{ "expand": "names,schema", "issues": [ { "expand": "", "fields": { "watcher": { "isWatching": false, "self": "https://your-domain.atlassian.net/rest/api/3/issue/EX-1/watchers", "watchCount": 1 }, "attachment": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "accountType": "atlassian", "active": false, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "key": "", "name": "", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "content": "https://your-domain.atlassian.net/jira/rest/api/3/attachment/content/10000", "created": "2022-10-06T07:32:47.000+0000", "filename": "picture.jpg", "id": 10000, "mimeType": "image/jpeg", "self": "https://your-domain.atlassian.net/rest/api/3/attachments/10000", "size": 23123, "thumbnail": "https://your-domain.atlassian.net/jira/rest/api/3/attachment/thumbnail/10000" } ], "sub-tasks": [ { "id": "10000", "outwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10003", "key": "ED-2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/ED-2" }, "type": { "id": "10000", "inward": "Parent", "name": "", "outward": "Sub-task" } } ], "description": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "Main order flow broken" } ] } ] }, "project": { "avatarUrls": { "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10000", "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10000", "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10000", "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10000" }, "id": "10000", "insight": { "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000", "totalIssueCount": 100 }, "key": "EX", "name": "Example", "projectCategory": { "description": "First Project Category", "id": "10000", "name": "FIRST", "self": "https://your-domain.atlassian.net/rest/api/3/projectCategory/10000" }, "self": "https://your-domain.atlassian.net/rest/api/3/project/EX", "simplified": false, "style": "classic" }, "comment": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "body": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper." } ] } ] }, "created": "2021-01-17T12:34:00.000+0000", "id": "10000", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000", "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } } ], "issuelinks": [ { "id": "10001", "outwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10004L", "key": "PR-2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/PR-2" }, "type": { "id": "10000", "inward": "depends on", "name": "Dependent", "outward": "is depended by" } }, { "id": "10002", "inwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10004", "key": "PR-3", "self": "https://your-domain.atlassian.net/rest/api/3/issue/PR-3" }, "type": { "id": "10000", "inward": "depends on", "name": "Dependent", "outward": "is depended by" } } ], "worklog": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "comment": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "I did some work here." } ] } ] }, "id": "100028", "issueId": "10002", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/worklog/10000", "started": "2021-01-17T12:34:00.000+0000", "timeSpent": "3h 20m", "timeSpentSeconds": 12000, "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "276f955c-63d7-42c8-9520-92d01dca0625", "type": "group", "value": "jira-developers" } } ], "updated": 1, "timetracking": { "originalEstimate": "10m", "originalEstimateSeconds": 600, "remainingEstimate": "3m", "remainingEstimateSeconds": 200, "timeSpent": "6m", "timeSpentSeconds": 400 } }, "id": "10002", "key": "ED-1", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10002" } ], "maxResults": 50, "startAt": 0, "total": 1, "warningMessages": [ "The value 'bar' does not exist for the field 'foo'." ] }`

POST

## Count issues using JQL

Provide an estimated count of the issues that match the [JQL](https://confluence.atlassian.com/x/egORLQ). Recent updates might not be immediately visible in the returned output. This endpoint requires JQL to be bounded.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Issues are included in the response where the user has:

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project containing the issue.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-details:jira`, `read:field.default-value:jira`, `read:field.option:jira`, `read:field:jira`, `read:group:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Request bodyapplication/json

A JSON object containing the search request.

### Responses

Returned if the request is successful.

#### application/json

POST/rest/api/3/search/approximate-count

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "jql": "project = HSP" }`; const response = await requestJira(`/rest/api/3/search/approximate-count`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

GET

## Search for issues using JQL enhanced search (GET)

Searches for issues using [JQL](https://confluence.atlassian.com/x/egORLQ). Recent updates might not be immediately visible in the returned search results. If you need [read-after-write](https://developer.atlassian.com/cloud/jira/platform/search-and-reconcile/) consistency, you can utilize the `reconcileIssues` parameter to ensure stronger consistency assurances. This operation can be accessed anonymously.

If the JQL query expression is too large to be encoded as a query parameter, use the [POST](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-post) version of this resource.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Issues are included in the response where the user has:

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project containing the issue.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-details:jira`, `read:audit-log:jira`, `read:avatar:jira`, `read:field-configuration:jira`, `read:issue-meta:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Query parameters

**reconcileIssues**

array<integer>

### Responses

Returned if the request is successful.

#### application/json

SearchAndReconcileResults

The result of a JQL search with issues reconsilation.

GET/rest/api/3/search/jql

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/search/jql?jql=project%20%3D%20HSP&nextPageToken=%3Cstring%3E&maxResults={maxResults}&fields={fields}&expand=%3Cstring%3E&reconcileIssues={reconcileIssues}`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197` `{ "isLast": true, "issues": [ { "expand": "", "fields": { "watcher": { "isWatching": false, "self": "https://your-domain.atlassian.net/rest/api/3/issue/EX-1/watchers", "watchCount": 1 }, "attachment": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "accountType": "atlassian", "active": false, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "key": "", "name": "", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "content": "https://your-domain.atlassian.net/jira/rest/api/3/attachment/content/10001", "created": "2023-06-24T19:24:50.000+0000", "filename": "debuglog.txt", "id": 10001, "mimeType": "text/plain", "self": "https://your-domain.atlassian.net/rest/api/2/attachments/10001", "size": 2460 } ], "sub-tasks": [ { "id": "10000", "outwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10003", "key": "ED-2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/ED-2" }, "type": { "id": "10000", "inward": "Parent", "name": "", "outward": "Sub-task" } } ], "description": "Main order flow broken", "project": { "avatarUrls": { "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10000", "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10000", "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10000", "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10000" }, "id": "10000", "insight": { "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000", "totalIssueCount": 100 }, "key": "EX", "name": "Example", "projectCategory": { "description": "First Project Category", "id": "10000", "name": "FIRST", "self": "https://your-domain.atlassian.net/rest/api/3/projectCategory/10000" }, "self": "https://your-domain.atlassian.net/rest/api/3/project/EX", "simplified": false, "style": "classic" }, "comment": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "body": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper.", "created": "2021-01-17T12:34:00.000+0000", "id": "10000", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000", "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } } ], "issuelinks": [ { "id": "10001", "outwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10004L", "key": "PR-2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/PR-2" }, "type": { "id": "10000", "inward": "depends on", "name": "Dependent", "outward": "is depended by" } }, { "id": "10002", "inwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10004", "key": "PR-3", "self": "https://your-domain.atlassian.net/rest/api/3/issue/PR-3" }, "type": { "id": "10000", "inward": "depends on", "name": "Dependent", "outward": "is depended by" } } ], "worklog": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "comment": "I did some work here.", "id": "100028", "issueId": "10002", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/worklog/10000", "started": "2021-01-17T12:34:00.000+0000", "timeSpent": "3h 20m", "timeSpentSeconds": 12000, "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "276f955c-63d7-42c8-9520-92d01dca0625", "type": "group", "value": "jira-developers" } } ], "updated": 1, "timetracking": { "originalEstimate": "10m", "originalEstimateSeconds": 600, "remainingEstimate": "3m", "remainingEstimateSeconds": 200, "timeSpent": "6m", "timeSpentSeconds": 400 } }, "id": "10002", "key": "ED-1", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10002" } ] }`

POST

## Search for issues using JQL enhanced search (POST)

Searches for issues using [JQL](https://confluence.atlassian.com/x/egORLQ). Recent updates might not be immediately visible in the returned search results. If you need [read-after-write](https://developer.atlassian.com/cloud/jira/platform/search-and-reconcile/) consistency, you can utilize the `reconcileIssues` parameter to ensure stronger consistency assurances. This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Issues are included in the response where the user has:

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project containing the issue.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:issue-details:jira`, `read:field.default-value:jira`, `read:field.option:jira`, `read:field:jira`, `read:group:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

### Request

#### Request bodyapplication/json

**reconcileIssues**

array<integer>

### Responses

Returned if the request is successful.

#### application/json

SearchAndReconcileResults

The result of a JQL search with issues reconsilation.

POST/rest/api/3/search/jql

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "expand": "<string>", "fields": [ "<string>" ], "fieldsByKeys": true, "jql": "<string>", "maxResults": 273, "nextPageToken": "<string>", "properties": [ "<string>" ], "reconcileIssues": [ 2154 ] }`; const response = await requestJira(`/rest/api/3/search/jql`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197` `{ "isLast": true, "issues": [ { "expand": "", "fields": { "watcher": { "isWatching": false, "self": "https://your-domain.atlassian.net/rest/api/3/issue/EX-1/watchers", "watchCount": 1 }, "attachment": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "accountType": "atlassian", "active": false, "avatarUrls": { "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16", "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24", "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32", "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48" }, "displayName": "Mia Krystof", "key": "", "name": "", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "content": "https://your-domain.atlassian.net/jira/rest/api/3/attachment/content/10001", "created": "2023-06-24T19:24:50.000+0000", "filename": "debuglog.txt", "id": 10001, "mimeType": "text/plain", "self": "https://your-domain.atlassian.net/rest/api/2/attachments/10001", "size": 2460 } ], "sub-tasks": [ { "id": "10000", "outwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10003", "key": "ED-2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/ED-2" }, "type": { "id": "10000", "inward": "Parent", "name": "", "outward": "Sub-task" } } ], "description": "Main order flow broken", "project": { "avatarUrls": { "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10000", "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10000", "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10000", "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10000" }, "id": "10000", "insight": { "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000", "totalIssueCount": 100 }, "key": "EX", "name": "Example", "projectCategory": { "description": "First Project Category", "id": "10000", "name": "FIRST", "self": "https://your-domain.atlassian.net/rest/api/3/projectCategory/10000" }, "self": "https://your-domain.atlassian.net/rest/api/3/project/EX", "simplified": false, "style": "classic" }, "comment": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "body": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper.", "created": "2021-01-17T12:34:00.000+0000", "id": "10000", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000", "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } } ], "issuelinks": [ { "id": "10001", "outwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10004L", "key": "PR-2", "self": "https://your-domain.atlassian.net/rest/api/3/issue/PR-2" }, "type": { "id": "10000", "inward": "depends on", "name": "Dependent", "outward": "is depended by" } }, { "id": "10002", "inwardIssue": { "fields": { "status": { "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png", "name": "Open" } }, "id": "10004", "key": "PR-3", "self": "https://your-domain.atlassian.net/rest/api/3/issue/PR-3" }, "type": { "id": "10000", "inward": "depends on", "name": "Dependent", "outward": "is depended by" } } ], "worklog": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "comment": "I did some work here.", "id": "100028", "issueId": "10002", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/worklog/10000", "started": "2021-01-17T12:34:00.000+0000", "timeSpent": "3h 20m", "timeSpentSeconds": 12000, "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "276f955c-63d7-42c8-9520-92d01dca0625", "type": "group", "value": "jira-developers" } } ], "updated": 1, "timetracking": { "originalEstimate": "10m", "originalEstimateSeconds": 600, "remainingEstimate": "3m", "remainingEstimateSeconds": 200, "timeSpent": "6m", "timeSpentSeconds": 400 } }, "id": "10002", "key": "ED-1", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10002" } ] }`
