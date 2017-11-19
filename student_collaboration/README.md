How to install this module for existing users ?

python manage.py runscript StudentCollaboratorCreator

Run the tests

python manage.py test student_collaboration

Sources for celery

https://pythad.github.io/articles/2016-12/how-to-run-celery-as-a-daemon-in-production
http://docs.celeryproject.org/en/latest/userguide/daemonizing.html#init-script-celerybeat
http://docs.celeryproject.org/en/latest/getting-started/brokers/rabbitmq.html

/etc/init.d/celeryd {start|stop|restart}
/etc/init.d/celerybeat {start|stop|restart}

$ sudo rabbitmqctl add_user oscar oscar
$ sudo rabbitmqctl add_vhost oscarRabbit
$ sudo rabbitmqctl set_user_tags oscar administrator
$ sudo rabbitmqctl set_permissions -p oscarRabbit oscar ".*" ".*" ".*"

Run in background
sudo rabbitmq-server -detached

Stop
sudo rabbitmqctl stop