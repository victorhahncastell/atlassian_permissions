# atlassian_permissions v. 0.2

This piece of software generates convenient permissions reports for your Jira, Confluence and Stash (a.k.a. Bitbucket Server) instances.

We wouldn't consider this stable yet. Use at your own risk.

## Known issues

- Confluence permission gathering will not work in newest versions as we're still using the deprecated XMLRPC API. Need to migrate to the new REST one.
- Jira and Stash permission gathering is horribly slow (about 20 times the time it takes for Confluence). This is probably because the new REST API we're using here doesn't seem to be on the quick side.
- We generally still lack error handling, for most of the problems we should definitely expect to encounter.
- Documentation is missing, too.
