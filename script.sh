
sudo rm /etc/supervisor/conf.d/daemon.conf
sudo cp daemon.conf /etc/supervisor/conf.d/daemon.conf
sudo supervisorctl reread
sudo supervisorctl update
# sudo supervisorctl start filedaemon