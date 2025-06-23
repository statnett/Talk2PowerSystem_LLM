#! /bin/bash

set -ex

REPOSITORY_ID="qa_dataset"
GRAPHDB_URI="http://localhost:7200"

function loadData {
  echo -e "\nImporting qa_dataset.ttl"
  curl -X POST -H "Content-Type: application/x-turtle" -T qa_dataset.ttl ${GRAPHDB_URI}/repositories/${REPOSITORY_ID}/statements
}

docker build --tag graphdb .
docker compose up --wait -d
loadData
# sleep 60 seconds, so that the set-up is completed
sleep 60s
echo -e "\nFinished"
