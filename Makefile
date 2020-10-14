VENV_PATH=venv/$(shell uname -s)

DATABASE_CONTAINER=blog-app-database
DATABASE_POD=blog-app-pod
DKR_CMD=sudo podman

WITH_APP_BUILD_CONTAINER = $(DKR_CMD) run \
    -e https_proxy=${https_proxy} -e http_proxy=${http_proxy} \
    -v `pwd`:/workspace \
    -w /workspace \
    --rm cloudteam/blog-app-build

# WITH_APP_RUN_CONTAINER: to restrict which endpoints are tested,
# add a comma separated list in an envvar:
# -e TEST_ROUTES="/v1/environments/<environment>"

WITH_APP_RUN_CONTAINER = $(DKR_CMD) run \
    -e https_proxy=${https_proxy} -e http_proxy=${http_proxy} \
    -v `pwd`:/workspace \
    -w /workspace \
    --pod $(DATABASE_POD) \
    --rm cloudteam/blog-app


.PHONY: app_build_container
app_build_container:
	$(DKR_CMD) build \
    --quiet \
    --build-arg http_proxy --build-arg https_proxy \
    --rm -t "cloudteam/blog-app-build" \
    -f Containerfile.build .

.PHONY: app_container
app_container:
	$(DKR_CMD) build \
    --build-arg http_proxy --build-arg https_proxy \
    --rm -t "cloudteam/blog-app" \
    -f Containerfile.app .

.PHONY: test
test: app_container unit_test

.PHONY: unit_test
unit_test: app_container
	$(WITH_APP_RUN_CONTAINER) python3 -m unittest discover -v -s ./test/unit

.PHONY: run_app
run_app: app_container
	$(WITH_APP_RUN_CONTAINER) /bin/bash -c \
    "FLASK_APP=app.py FLASK_ENV=development flask run --host=0.0.0.0 --port=8080"

.PHONY: psql
psql:
	$(DKR_CMD) exec -it -e PGPASSWORD=lantern_rouge $(DATABASE_CONTAINER) psql -U blog-app-user blog-app-db

.PHONY: container_network
container_network:
	@$(DKR_CMD) pod exists $(DATABASE_POD) > /dev/null 2>&1 || \
		$(DKR_CMD) pod create --name $(DATABASE_POD) -p 8080:8080

.PHONY: database_container_build
database_container_build:
	@$(DKR_CMD) kill $(DATABASE_CONTAINER) > /dev/null 2>&1 || :
	@$(DKR_CMD) rm $(DATABASE_CONTAINER) > /dev/null 2>&1 || :
	$(DKR_CMD) build \
		--build-arg http_proxy --build-arg https_proxy \
		--rm -t "cloudteam/blog-app-database" \
		-f Containerfile.db

.PHONY: database_container
database_container: database_container_build container_network
	@echo "Running a postgres container in the background"
	$(DKR_CMD) run -d \
		-e https_proxy=${https_proxy} -e http_proxy=${http_proxy} \
		--rm \
		--name $(DATABASE_CONTAINER) \
		--pod $(DATABASE_POD) \
		cloudteam/blog-app-database -c max_connections=50

$(VENV_PATH)/test: test_requirements.txt requirements.txt
	@rm -rf $@ || :
	python3 -m venv $@
	$@/bin/pip3 install --upgrade pip setuptools wheel
	$@/bin/pip3 install -r $<
