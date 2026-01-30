# Gemini Model Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install `langchain-google-genai==2.0.8` for Gemini support.

### 2. Add API Key to .env

Create or edit your `.env` file:

```bash
# OpenAI (for GPT models)
OPENAI_API_KEY=sk-your-openai-key-here

# Google Gemini (for Gemini models)
GOOGLE_API_KEY=AIzaSyBKzORKgtvcCI2vwhYuzCqgToItYwTf5oY
```

**Note:** You can use either `GOOGLE_API_KEY` or `GEMINI_API_KEY`.

### 3. Get Your Gemini API Key

If you don't have a key yet:
1. Visit https://aistudio.google.com/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file

## Available Gemini Models

### Latest (Gemini 3)
- **gemini-3-pro-preview** - 1M context, $2-4/$12-18 per 1M tokens
- **gemini-3-flash-preview** - 1M context, $0.50/$3 per 1M tokens (FASTEST & CHEAPEST)

### Stable (Gemini 2.5)
- **gemini-2.5-flash** - Stable flash model
- **gemini-2.5-pro** - Stable pro model

### Latest Aliases (Auto-updating)
- **gemini-flash-latest** - Always points to latest flash
- **gemini-pro-latest** - Always points to latest pro

### Previous Generation (Gemini 1.5)
- **gemini-1.5-pro** - Proven, stable pro model
- **gemini-1.5-flash** - Proven, stable flash model

## Usage Examples

### CLI (Original)

```bash
python main.py \
  --input my_prd.md \
  --title "My Feature" \
  --max-iterations 3 \
  --model gemini-3-flash-preview
```

### Web Dashboard

1. Start server:
```bash
python run_api.py
```

2. Open http://localhost:8000

3. Select a Gemini model from the "Primary Model" dropdown

4. Choose "Diverse (Mix Models)" for model strategy to use multiple providers

## Model Strategy Options

### Uniform (Use Primary)
All critics use the same model you selected.

Example: If you select `gemini-3-flash-preview`, all 3 critics use Gemini 3 Flash.

### Diverse (Mix Models)
Critics rotate through a mix of providers for diverse perspectives:

1. Critic 1: `gpt-5.2`
2. Critic 2: `gemini-3-pro-preview`
3. Critic 3: `gpt-5.2-pro`
4. Critic 4 (if 4+ participants): `gemini-3-flash-preview`
5. Critic 5: `claude-3-5-sonnet-20240620`
6. And so on...

This gives you the benefit of different models' strengths.

## Cost Optimization

For cost-effective refinement:
- **Primary model:** `gemini-3-flash-preview` ($0.50/$3 per 1M tokens)
- **Strategy:** Uniform

For maximum quality:
- **Primary model:** `gpt-5.2` or `gemini-3-pro-preview`
- **Strategy:** Diverse (mix of top models)

## Pricing Comparison

| Model | Input (per 1M) | Output (per 1M) | Context |
|-------|----------------|-----------------|---------|
| gemini-3-flash-preview | $0.50 | $3.00 | 1M |
| gemini-3-pro-preview | $2-4 | $12-18 | 1M |
| gpt-4-turbo | ~$10 | ~$30 | 128K |
| claude-3-5-sonnet | $3 | $15 | 200K |

**Gemini 3 Flash is the most cost-effective option!**

## Technical Notes

- Gemini models don't support system messages - automatically converted to human messages
- Gemini supports 1M token context (vs 128K-200K for GPT/Claude)
- Preview models may have rate limits
- Latest aliases auto-update with 2-week notice

## Troubleshooting

### "GOOGLE_API_KEY not found"
Make sure your `.env` file contains `GOOGLE_API_KEY` and is in the project root.

### "langchain-google-genai not installed"
Run: `pip install langchain-google-genai`

### Rate limit errors
Gemini preview models may have stricter rate limits. Try:
- Reducing number of participants
- Using stable models (`gemini-1.5-pro` instead of preview)
- Adding delays between iterations

### API key invalid
Verify your key at https://aistudio.google.com/apikey

## Support

For issues with:
- **Gemini API:** https://ai.google.dev/gemini-api/docs
- **This integration:** See CLAUDE.md or create an issue
