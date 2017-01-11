#!/usr/bin/python3
import os
import sys
import socket

if __name__ == "__main__":
    hostname = socket.gethostname()
    host_settings = os.path.join('htsworkflow/settings', hostname + '.py')
    if os.path.exists(host_settings):
        module = hostname
    else:
        module = 'local'
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "htsworkflow.settings.{}".format(module))

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
