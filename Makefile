start:
	docker compose up -d

clean:
	docker compose stop
	sudo rm -rf volumes

reindex:
	./bin/reindex.sh /var/www/html/records
