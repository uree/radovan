FLASK_CONTAINER = "radovan_api"
TEST_NAME ?=

run-tests:
	docker exec $(FLASK_CONTAINER) \
	python -m pytest tests

run-int-tests-endpoints:
	docker exec $(FLASK_CONTAINER) \
	python -m pytest tests/integration/test_endpoints.py

run-int-tests-providers:
	docker exec $(FLASK_CONTAINER) \
	python -m pytest tests/integration/test_providers.py$(if $(TEST_NAME),::$(TEST_NAME))
