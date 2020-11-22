#!/bin/bash
sudo cp filedaemon/daemon.conf /etc/supervisor/conf.d/daemon.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start filedaemon
