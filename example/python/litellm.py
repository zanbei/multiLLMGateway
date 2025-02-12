curl 'https:///key/generate' \
--header 'Authorization: ' \
--header 'Content-Type: application/json' \
--data-raw '{"models": ["bedrock-nova-v1", "deepseek-chat"], "user_id": "AK", "metadata": {"user": "test@test.com"}}'


curl -X POST 'https:///chat/completions' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer ' \
-d '{
  "model": "bedrock-nova-v1",
  "messages": [
    {
      "role": "user",
      "content": "What'\''s the weather like in Boston today?"
    }
  ],
  "temperature": 0.7,
  "top_p": 1,
  "top_k": 20
  }'