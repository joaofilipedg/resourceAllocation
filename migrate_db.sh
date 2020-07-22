#!/bin/bash
FLASK_PATH="/homelocal/resalloc_bot/.conda/envs/resalloc_env/bin/flask"

if [ -z "$1" ]
then
    echo -e "\nPlease call '$0 <argument>' to run this command!\nPossible arguments:\n\tinit\n\tmigrate\n\tupgrade\n\tdowngrade"
    exit 1
else
    if [ "$1" == "migrate" ]
    then
        if [ -z "$2" ]
        then
            sudo ${FLASK_PATH} db ${1}
        else
            sudo ${FLASK_PATH} db ${1} -m "${2}"
        fi
    else
        sudo ${FLASK_PATH} db ${1}
    fi
fi