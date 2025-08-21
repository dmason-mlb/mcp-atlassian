Cloud

Jira Cloud platform / Reference / REST API v3

This resource represents issue comments. Use it to:

*   get, create, update, and delete a comment from an issue.
*   get all comments from issue.
*   get a list of comments by comment ID.

Returns a [paginated](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#pagination) list of comments specified by a list of comment IDs.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Comments are returned where the user:

*   has _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project containing the comment.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.
*   If the comment has visibility restrictions, belongs to the group or has the role visibility is restricted to.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`delete:comment.property:jira`, `read:avatar:jira`, `read:comment:jira`, `read:group:jira`, `read:project-role:jira` ...(Show more)

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

#### Request bodyapplication/json

The list of comment IDs.

**ids**

array<integer>

Required

Returned if the request is successful.

#### application/json

PageBeanComment

A page of items.

POST/rest/api/3/comment/list

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "ids": [ 1, 2, 5, 10 ] }`; const response = await requestJira(`/rest/api/3/comment/list`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46` `{ "isLast": true, "maxResults": 1048576, "startAt": 0, "total": 1, "values": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "body": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper." } ] } ] }, "created": "2021-01-17T12:34:00.000+0000", "id": "10000", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000", "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } } ] }`

Returns all comments for an issue.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:** Comments are included in the response where the user has:

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project containing the comment.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.
*   If the comment has visibility restrictions, belongs to the group or has the role visibility is role visibility is restricted to.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:comment:jira`, `read:comment.property:jira`, `read:group:jira`, `read:project:jira`, `read:project-role:jira` ...(Show more)

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

**issueIdOrKey**

string

Required

Returned if the request is successful.

#### application/json

PageOfComments

A page of comments.

GET/rest/api/3/issue/{issueIdOrKey}/comment

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/comment`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45` `{ "comments": [ { "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "body": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper." } ] } ] }, "created": "2021-01-17T12:34:00.000+0000", "id": "10000", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000", "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } } ], "maxResults": 1, "startAt": 0, "total": 1 }`

Adds a comment to an issue.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ and _Add comments_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue containing the comment is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`read:comment:jira`, `read:comment.property:jira`, `read:group:jira`, `read:project:jira`, `read:project-role:jira` ...(Show more)

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

**issueIdOrKey**

string

Required

#### Request bodyapplication/json

**properties**

array<EntityProperty>

Returned if the request is successful.

#### application/json

POST/rest/api/3/issue/{issueIdOrKey}/comment

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "body": { "content": [ { "content": [ { "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper.", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } }`; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/comment`, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38` `{ "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "body": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper." } ] } ] }, "created": "2021-01-17T12:34:00.000+0000", "id": "10000", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000", "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } }`

Returns a comment.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project containing the comment.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.
*   If the comment has visibility restrictions, the user belongs to the group or has the role visibility is restricted to.

##### Scopes

**Classic**RECOMMENDED:`read:jira-work`

**Granular**:`read:comment:jira`, `read:comment.property:jira`, `read:group:jira`, `read:project:jira`, `read:project-role:jira` ...(Show more)

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `READ`

**issueIdOrKey**

string

Required

Returned if the request is successful.

#### application/json

GET/rest/api/3/issue/{issueIdOrKey}/comment/{id}

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/comment/{id}`, { headers: { 'Accept': 'application/json' } }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38` `{ "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "body": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper." } ] } ] }, "created": "2021-01-17T12:34:00.000+0000", "id": "10000", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000", "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } }`

Updates a comment.

This operation can be accessed anonymously.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue containing the comment is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.
*   _Edit all comments_ [project permission](https://confluence.atlassian.com/x/yodKLg) to update any comment or _Edit own comments_ to update comment created by the user.
*   If the comment has visibility restrictions, the user belongs to the group or has the role visibility is restricted to.

**WARNING:** Child comments inherit visibility from their parent comment. Attempting to update a child comment's visibility will result in a 400 (Bad Request) error.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`read:comment:jira`, `read:comment.property:jira`, `read:group:jira`, `read:project:jira`, `read:project-role:jira` ...(Show more)

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `WRITE`

**issueIdOrKey**

string

Required

**overrideEditableFlag**

boolean

#### Request bodyapplication/json

**properties**

array<EntityProperty>

Returned if the request is successful.

#### application/json

PUT/rest/api/3/issue/{issueIdOrKey}/comment/{id}

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; var bodyData = `{ "body": { "content": [ { "content": [ { "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper.", "type": "text" } ], "type": "paragraph" } ], "type": "doc", "version": 1 }, "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } }`; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/comment/{id}`, { method: 'PUT', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: bodyData }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.json());``

`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38` `{ "author": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "body": { "type": "doc", "version": 1, "content": [ { "type": "paragraph", "content": [ { "type": "text", "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper." } ] } ] }, "created": "2021-01-17T12:34:00.000+0000", "id": "10000", "self": "https://your-domain.atlassian.net/rest/api/3/issue/10010/comment/10000", "updateAuthor": { "accountId": "5b10a2844c20165700ede21g", "active": false, "displayName": "Mia Krystof", "self": "https://your-domain.atlassian.net/rest/api/3/user?accountId=5b10a2844c20165700ede21g" }, "updated": "2021-01-18T23:45:00.000+0000", "visibility": { "identifier": "Administrators", "type": "role", "value": "Administrators" } }`

Deletes a comment.

**[Permissions](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#permissions) required:**

*   _Browse projects_ [project permission](https://confluence.atlassian.com/x/yodKLg) for the project that the issue containing the comment is in.
*   If [issue-level security](https://confluence.atlassian.com/x/J4lKLg) is configured, issue-level security permission to view the issue.
*   _Delete all comments_ [project permission](https://confluence.atlassian.com/x/yodKLg) to delete any comment or _Delete own comments_ to delete comment created by the user,
*   If the comment has visibility restrictions, the user belongs to the group or has the role visibility is restricted to.

##### Scopes

**Classic**RECOMMENDED:`write:jira-work`

**Granular**:`delete:comment:jira`, `delete:comment.property:jira`

**[Connect app scope](https://developer.atlassian.com/cloud/jira/platform/scopes) required**: `DELETE`

**issueIdOrKey**

string

Required

Returned if the request is successful.

DEL/rest/api/3/issue/{issueIdOrKey}/comment/{id}

Forge

curl

Node.js

Java

Python

PHP

`1 2 3 4 5 6 7 8 9 10` ``// This sample uses Atlassian Forge // https://developer.atlassian.com/platform/forge/ import { requestJira } from "@forge/bridge"; const response = await requestJira(`/rest/api/3/issue/{issueIdOrKey}/comment/{id}`, { method: 'DELETE' }); console.log(`Response: ${response.status} ${response.statusText}`); console.log(await response.text());``
