#! /bin/bash
REPOSITORY_ID="cim"
GRAPHDB_URI="http://localhost:7200/"

echo -e "\nUsing GraphDB: ${GRAPHDB_URI}"

function startGraphDB {
 echo -e "\nStarting GraphDB..."
 exec /opt/graphdb/dist/bin/graphdb
}

function waitGraphDBStart {
  echo -e "\nWaiting GraphDB to start..."
  for _ in $(seq 1 5); do
    CHECK_RES=$(curl --silent --write-out '%{http_code}' --output /dev/null ${GRAPHDB_URI}/rest/repositories)
    if [ "${CHECK_RES}" = '200' ]; then
        echo -e "\nUp and running"
        break
    fi
    sleep 30s
    echo "CHECK_RES: ${CHECK_RES}"
  done
}

function loadData {
  echo -e "\nImporting statements.ttl"
  curl -X POST -H "Content-Type: application/x-turtle" -T /statements.ttl ${GRAPHDB_URI}/repositories/${REPOSITORY_ID}/statements
}

function computeRdfRank {
  echo -e "\nTriggering the computation of the RDF rank"
  curl -X POST -H "Content-Type: application/x-www-form-urlencoded" -d 'update=INSERT DATA { _:b1 <http://www.ontotext.com/owlim/RDFRank#compute> _:b2. }' "${GRAPHDB_URI}/repositories/${REPOSITORY_ID}/statements"
}

function enableAutocompleteIndex {
  echo -e "\nEnable autocomplete index"
  curl -X POST -H "Content-Type: application/x-www-form-urlencoded" -d 'update=INSERT DATA { _:s  <http://www.ontotext.com/plugins/autocomplete#enabled> true . }' "${GRAPHDB_URI}/repositories/${REPOSITORY_ID}/statements"
}

startGraphDB &
waitGraphDBStart
loadData
computeRdfRank
enableAutocompleteIndex
wait
