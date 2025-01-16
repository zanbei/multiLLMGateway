docker run -d \
    -v $(pwd)/litellm_config.yaml:/app/config.yaml \
    -p 4000:4000 \
    ghcr.io/berriai/litellm:main-v1.58.2 \
    --config /app/config.yaml --detailed_debug