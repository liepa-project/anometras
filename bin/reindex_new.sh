#!/bin/bash

process_file() {
  TIMESTAMP=`date -r $1 '+%Y-%m-%dT%H:%M:%S%z'`
  batch_code=$2
  annotation_record_type=$3
  file_path=/records/$annotation_record_type/$1
  echo "$file_path   $TIMESTAMP"


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


batch_code=`echo batch_$(date  '+%Y%m%dT%H%M%S')`
echo "Scanning: path - $path"
echo "annotation_record_type=$type"
echo "batch_code=$batch_code"

db_filename="/tmp/anometras_db_${type}_${batch_code}.txt"
local_filename="/tmp/anometras_local_${type}_${batch_code}.txt"
added_filename="/tmp/anometras_added_${type}_${batch_code}.txt"

# echo -e "\nIn db: "

curl -s "http://localhost:8002/elan-file/files/record_types/$type/paths" > $db_filename
sed -i "s|/records/annot1/||g" $db_filename
sed -i "s|/records/org/||g" $db_filename

#cat /tmp/db.txt 

#echo -e "\nLocal: "

#find $path -type f -printf "%T@ %p\n" | sort -nr | cut -d\  -f2- > /tmp/local_$batch_code.txt
(cd $path; find -L ./ -type f -name "*.eaf" -printf "%p\n" | sort) > $local_filename
sed -i 's|../speech/annot_repo||g' $local_filename
sed -i 's|../speech/org_repo||g' $local_filename

diff -c -w $db_filename $local_filename
comm -1 -3 $db_filename $local_filename > $added_filename

num_lines=`wc -l < $added_filename`

echo -e "\nNew records saved in file $added_filename.  New lines: $num_lines \n\n"
#cat $added_filename


while IFS= read -r pp; do
    # echo "File: $pp"
    #(cd $path; find -L ./ -path  "*${pp}" -print0)
    (cd $path; find -L ./ -path  "*${pp}" -exec /bin/bash  -c "process_file \"\$0\" \"$batch_code\" \"$type\" " {} \;)
done < $added_filename