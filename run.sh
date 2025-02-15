	make build-dev
	docker run -it \
	--cpus 1 \
	-e AWS_DEFAULT_REGION -e AWS_SECRET_ACCESS_KEY -e AWS_ACCESS_KEY \
	-e API_KEY_PATH=./.key -e SECRET_KEY_PATH=./.secret \
	-p 8000:8000 \
	--volume .test_config.json:/test_config.json \
	--volume .key:/.key \
	--volume .secret:/.secret \
    --rm docker.io/radasam/autotrade:0.0.1    