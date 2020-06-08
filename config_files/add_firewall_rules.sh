#!/bin/bash
firewall-cmd --add-service=http --permanent
firewall-cmd --add-service=https --permanent
firewall-cmd --reload
firewall-cmd --list-all
semanage permissive -a httpd_t
