start:
	docker compose up -d

clean:
	docker compose stop
	sudo rm -rf volumes

reindex:
	# bash -x ./bin/reindex.sh -t annot1 -p ../speech/annot_repo/
	./bin/reindex.sh -t annot1 -p ../speech/annot_repo/
	./bin/reindex.sh -t org -p ../speech/org_repo/
