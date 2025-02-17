DEV_TAG=?
VERSION=$(shell cat VERSION)

build-dev:
	docker build . -t radasam/autotrade:$(VERSION)-$(DEV_TAG)

build:
	docker build --platform linux/amd64 . -t radasam/autotrade:$(VERSION)

push:
	docker push radasam/autotrade:$(VERSION)

build_and_push:
	docker build --platform linux/amd64 . -t radasam/autotrade:$(VERSION)
	docker push radasam/autotrade:$(VERSION)

run-dev:
	make build-dev
	docker run -it \
	--cpus 2 \
	-e AWS_DEFAULT_REGION -e AWS_SECRET_ACCESS_KEY -e AWS_ACCESS_KEY \
	-e API_KEY_PATH=./api_key -e SECRET_KEY_PATH=./api_secret \
	-p 8000:8000 \
	--volume ./test_config.json:/test_config.json \
	--volume /Users/samradage/Documents/coinbase/.key2:/api_key \
	--volume /Users/samradage/Documents/coinbase/.secret2:/api_secret \
    --rm radasam/autotrade:$(VERSION)-$(DEV_TAG) 