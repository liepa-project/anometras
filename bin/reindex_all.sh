#!/bin/bash

process_file() {
  TIMESTAMP=`date -r $1 '+%Y-%m-%dT%H:%M:%S%z'`
  batch_code=$2
  annotation_record_type=$3
  file_path=/records/$annotation_record_type/$1
  echo "$file_path   $TIMESTAMP"
  
  #curl -X POST "http://127.0.0.1:8002/elan-file/files" \
  #    -H 'accept: application/json' \
  #    -H "annotation-upload-date: $TIMESTAMP" \
  #    -H "annotation-record-path: $1" \
  #    -F "uploadFile=@$1;type=application/xml"

  echo "sending: annotation_record_path=$file_path"
  # echo "sending: annotation_record_type=$annotation_record_type"
  # echo "sending: batch_code=$batch_code"
  
  curl -X POST "http://localhost:8002/elan-file/files/local" \
      -H 'accept: application/json'\
      -H 'content-type: application/x-www-form-urlencoded' \
      --data-urlencode "annotation_record_path=$file_path" \
      --data-urlencode "annotation_record_type=$annotation_record_type" \
      --data-urlencode "batch_code=$batch_code"
  echo "Done"
}

export -f process_file

#find ./test_repo/ -name "*.eaf" -printf '%TY-%Tm-%Td %TH:%TM %f\n'
#find test_repo/ -name "*.eaf" -exec /bin/bash -c 'foo "$0"' {} \;


usage() { echo "Usage: $0 [-p <path>] [-t <string>]" 1>&2; exit 1; }

while getopts ":p:t:" o; do
    case "${o}" in
        p)
            path=${OPTARG}
            ;;
        t)
            type=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${path}" ] || [ -z "${type}" ]; then
    usage
fi

# echo "type = ${type}"
# echo "path = ${path}"
batch_code=`echo batch_$(date  '+%Y%m%dT%H%M%S')`

echo "Scanning: path - $path"
echo "annotation_record_type=$type"
echo "batch_code=$batch_code"
  

#find ./test_repo/ -name "*.eaf" -printf '%TY-%Tm-%Td %TH:%TM %f\n'
(cd $path; find -L ./ -name "*.eaf" -regex ".+\/_?[A-Z][A-Z]\/.*"  -exec /bin/bash  -c "process_file \"\$0\" \"$batch_code\" \"$type\" " {} \;)
