#!/bin/bash
for i in /etc/profile.d/*.sh; do
    source $i
done
source activate nipypetests-2.7
nosetests --with-doctest -c ./.noserc --logging-level=DEBUG --verbosity=3 $@
