#!/bin/bash

process_file() {
  TIMESTAMP=`date -r $1 '+%Y-%m-%dT%H:%M:%S%z'`
  file_path=/records/$1
  echo "$file_path   $TIMESTAMP"
  #curl -X POST "http://127.0.0.1:8002/elan-file/files" \
  #    -H 'accept: application/json' \
  #    -H "annotation-upload-date: $TIMESTAMP" \
  #    -H "annotation-record-path: $1" \
  #    -F "uploadFile=@$1;type=application/xml"
  
  curl -X POST "http://localhost:8002/elan-file/files/local" \
      -H 'accept: application/json'\
      -H 'content-type: application/x-www-form-urlencoded' \
      --data-urlencode "annotation_record_path=$file_path"
  echo "Done"
}

export -f process_file

#find ./test_repo/ -name "*.eaf" -printf '%TY-%Tm-%Td %TH:%TM %f\n'
#find test_repo/ -name "*.eaf" -exec /bin/bash -c 'foo "$0"' {} \;


echo "Scanning: $1"

#find ./test_repo/ -name "*.eaf" -printf '%TY-%Tm-%Td %TH:%TM %f\n'
(cd $1; find -L ./ -name "*.eaf" -regex ".+\/_?[A-Z][A-Z]\/.*"  -exec /bin/bash -c 'process_file "$0"' {} \;)
