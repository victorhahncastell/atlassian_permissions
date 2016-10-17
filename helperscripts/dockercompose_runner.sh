#!/bin/bash

# remove old reports to prevent them from getting republished in case anything goes wrong
rm -f permissions.html
rm -f changes.html
rm -f mailbody.html

docker-compose build

# create a plain old regular permissions report
docker-compose run --name atlassian_permissions_run atlassian_permissions -S status.pickle --html -o permissions.html -u $username -p $password "$@"
docker cp atlassian_permissions_run:/permissions.html ./permissions.html

# if we have a previous state, produce a diff
if [ -f ./status.pickle ]; then
	docker cp ./status.pickle atlassian_permissions:/oldstatus.pickle
	docker-compose run --name atlassian_permissions_run atlassian_permissions -L status.pickle -cmp oldstatus.pickle --html -o changes.html --diff
	docker cp atlassian_permissions_run:/changes.html ./changes.html
	cp changes.html mailbody.html      # use change report for mail notification
else
	cp permissions.html mailbody.html  # no change report available, mail full permission report
fi

# save state for next time's diff
docker cp atlassian_permissions_run:/status.pickle ./status.pickle
