start:
	docker compose up -d --build

clean:
	docker compose stop
	sudo rm -rf volumes

reindex:
	# bash -x ./bin/reindex.sh -t annot1 -p ../speech/annot_repo/
	./bin/reindex_new.sh -t annot1 -p ../speech/annot_repo/
	./bin/reindex_new.sh -t org -p ../speech/org_repo/

wer_reindex: ### Reindex word error rates info
	./bin/wer_reindex_new.sh