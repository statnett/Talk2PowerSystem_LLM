FROM ontotext/graphdb:10.8.5
RUN mkdir -p /opt/graphdb/dist/data/repositories/qa_dataset
COPY config.ttl /opt/graphdb/dist/data/repositories/qa_dataset/
COPY run.sh /run.sh
ENTRYPOINT ["bash", "/run.sh"]
