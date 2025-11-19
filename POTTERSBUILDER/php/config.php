<?php
// POTTERSBUILDER PHP frontend config
// Set PB_API_URL environment variable to override
$API_URL = getenv('PB_API_URL') ?: 'http://127.0.0.1:8000/query';

// Optionally set OPENAI API key for direct frontend synthesis (preferred via env)
// WARNING: Storing secrets in code is insecure. Prefer setting environment variable OPENAI_API_KEY.
$OPENAI_API_KEY = getenv('OPENAI_API_KEY') ?: null;

// Path to prompt template (optional)
$PROMPT_TEMPLATE = __DIR__ . '/../src/prompt_templates/colonial_prompt.txt';
