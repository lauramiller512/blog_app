DATABASE_CONTAINER=blog-app-database
DATABASE_POD=blog-app-pod
PODMAN=sudo podman


WITH_APP_RUN_CONTAINER = $(PODMAN) run \
    -e https_proxy=${https_proxy} -e http_proxy=${http_proxy} \
    -v `pwd`:/workspace \
    -w /workspace \
    --pod $(DATABASE_POD) \
    --rm cloudteam/blog-app

WITH_TEST_CONTAINER = $(PODMAN) run \
    -e https_proxy=${https_proxy} -e http_proxy=${http_proxy} \
    -v `pwd`:/workspace \
    -w /workspace \
    --pod $(DATABASE_POD) \
    --rm cloudteam/blog-app-test


.PHONY: app_container
app_container:
	$(PODMAN) build \
    --build-arg http_proxy --build-arg https_proxy \
    --rm -t "cloudteam/blog-app" \
    -f Containerfile.app .

.PHONY: test_container
test_container:
	$(PODMAN) build \
    --build-arg http_proxy --build-arg https_proxy \
    --rm -t "cloudteam/blog-app-test" \
    -f Containerfile.test .

.PHONY: test
test: app_container unit_test

.PHONY: unit_test
unit_test: test_container database_container
	$(WITH_TEST_CONTAINER) python3 -m unittest discover -v -s ./test

.PHONY: run_app
run_app: app_container
	$(WITH_APP_RUN_CONTAINER) /bin/bash -c \
    "FLASK_APP=app.py FLASK_ENV=development flask run --host=0.0.0.0 --port=8080"

.PHONY: psql
psql:
	$(PODMAN) exec -it -e PGPASSWORD=lantern_rouge $(DATABASE_CONTAINER) psql -U blog-app-user blog-app-db

.PHONY: container_network
container_network:
	@$(PODMAN) pod exists $(DATABASE_POD) > /dev/null 2>&1 || \
		$(PODMAN) pod create --name $(DATABASE_POD) -p 8080:8080

.PHONY: database_container_build
database_container_build:
	@$(PODMAN) kill $(DATABASE_CONTAINER) > /dev/null 2>&1 || :
	@$(PODMAN) rm $(DATABASE_CONTAINER) > /dev/null 2>&1 || :
	$(PODMAN) build \
		--build-arg http_proxy --build-arg https_proxy \
		--rm -t "cloudteam/blog-app-database" \
		-f Containerfile.db

.PHONY: database_container
database_container: database_container_build container_network # depends on these targets
	@echo "Running a postgres container in the background"
	$(PODMAN) run -d \
		-e https_proxy=${https_proxy} -e http_proxy=${http_proxy} \
		--rm \
		--name $(DATABASE_CONTAINER) \
		--pod $(DATABASE_POD) \
		cloudteam/blog-app-database -c max_connections=50
