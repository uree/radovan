FLASK_CONTAINER = "radovan_api"


run-func-tests:
	docker exec $(FLASK_CONTAINER) \
	python -m pytest tests

run-func-tests-endpoints:
	docker exec $(FLASK_CONTAINER) \
	python -m pytest tests/integration/test_endpoints.py

run-func-tests-providers:
	docker exec $(FLASK_CONTAINER) \
	python -m pytest tests/integration/test_providers.py
