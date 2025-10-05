
bind = "unix:/run/gunicorn_megano.sock"
workers = 3
timeout = 30
accesslog = "/var/log/gunicorn/megano_access.log"
errorlog = "/var/log/gunicorn/megano_error.log"
loglevel = "warning"
