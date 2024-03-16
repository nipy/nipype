if [ -e virtenv/bin/activate ]; then
    source virtenv/bin/activate
elif [ -e virtenv/Scripts/activate ]; then
    source virtenv/Scripts/activate
else
    echo Cannot activate virtual environment
    ls -R virtenv
    false
fi
