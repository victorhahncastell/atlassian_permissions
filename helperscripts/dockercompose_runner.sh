#!/bin/bash

# remove old reports to prevent them from getting republished in case anything goes wrong
rm -f permissions.html
rm -f changes.html
rm -f mailbody.html

# create a plain old regular permissions report
docker-compose build
docker-compose run --name atlassian_permissions_run atlassian_permissions -S status.pickle --html -o permissions.html -u $username -p $password "$@"
docker cp atlassian_permissions_run:/permissions.html ./permissions.html
docker cp atlassian_permissions_run:/status.pickle ./status.pickle
docker rm atlassian_permissions_run

# if we have a previous state, produce a diff
if [ -f ./oldstatus.pickle ]; then
	docker-compose build
	docker-compose run --name atlassian_permissions_run atlassian_permissions -L /opt/atlassian_permissions/status.pickle -cmp /opt/atlassian_permissions/oldstatus.pickle --html -o changes.html --diff
	docker cp atlassian_permissions_run:/changes.html ./changes.html
	docker rm atlassian_permissions_run
	cp changes.html mailbody.html      # use change report for mail notification
	rm oldstatus.pickle
else
	cp permissions.html mailbody.html  # no change report available, mail full permission report
fi

mv status.pickle oldstatus.pickle
