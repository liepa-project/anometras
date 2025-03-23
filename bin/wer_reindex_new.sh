#!/bin/bash

curl -X 'POST' \
  'http://localhost:8002/elan-file/stats/reindex/wer' \
  -H 'accept: application/json' \