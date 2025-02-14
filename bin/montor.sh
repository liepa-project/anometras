#!/bin/bash

file_removed() {
    echo "$2 was removed from $1" &
}

file_modified() {
    TIMESTAMP=`date`
    echo "[$TIMESTAMP]: The file $1$2 was modified" 
}

file_created() {
    TIMESTAMP=`date '+%Y-%m-%dT%H:%M:%S%z'`
    echo "[$TIMESTAMP]: The file $1$2 was created" 
    
    (cd $1; curl -X POST "http://127.0.0.1:8002/elan-file/files" \
      -H 'accept: application/json' \
      -H "annotation-upload-date: $TIMESTAMP" \
      -H "annotation-record-path: $1$2" \
      -F "uploadFile=@$2;type=application/xml")
}

#inotifywait -q -m -r -e modify,delete,create $1 | while read DIRECTORY EVENT FILE; do

inotifywait -q -m -r -e modify,delete,create test_repo | while read DIRECTORY EVENT FILE; do
    case $EVENT in
        MODIFY*)
            file_modified "$DIRECTORY" "$FILE"
            ;;
        CREATE*)
            file_created "$DIRECTORY" "$FILE"
            ;;
        DELETE*)
            file_removed "$DIRECTORY" "$FILE"
            ;;
    esac
done
