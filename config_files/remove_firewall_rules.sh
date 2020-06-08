#!/bin/bash
semanage permissive -d httpd_t
firewall-cmd --remove-service=http --permanent
firewall-cmd --remove-service=https --permanent
firewall-cmd --reload
firewall-cmd --list-all
