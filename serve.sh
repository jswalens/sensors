#!/bin/bash
gunicorn -b 0.0.0.0:8080 --access-logfile=- serve:APP |& tee -a serve.log
