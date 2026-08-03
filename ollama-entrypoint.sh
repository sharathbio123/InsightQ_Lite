#!/bin/sh
set -eu

ollama serve >/tmp/ollama.log 2>&1 &

for i in $(seq 1 60); do
  if ollama list >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

ollama pull llama3.2:3b >/tmp/ollama-pull.log 2>&1 || true
ollama pull nomic-embed-text >/tmp/ollama-pull.log 2>&1 || true

wait
