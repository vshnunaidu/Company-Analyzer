"""Claude AI service for analysis and chat."""

import os
import time
import logging
from typing import AsyncGenerator, Optional
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class ClaudeError(Exception):
    """Base exception for Claude-related errors."""
    pass


class ClaudeClient:
    """Client for Claude AI API."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ClaudeError("ANTHROPIC_API_KEY environment variable not set")
        self.client = AsyncAnthropic(api_key=api_key)
        # Use Sonnet 4.5 for both analysis and chat
        self.fast_model = "claude-sonnet-4-5-20250929"
        self.chat_model = "claude-sonnet-4-5-20250929"

    async def analyze_filing(
        self,
        sections: list[dict],
        company_info: dict,
        financial_data: Optional[dict] = None
    ) -> dict:
        """Analyze a 10-K filing and generate an audit report."""
        start_time = time.time()

        # Limit to 3 most important sections with 4000 chars each for speed
        sections_text = "\n\n---\n\n".join([
            f"## {s['name']}\n{s['content'][:4000]}"
            for s in sections[:3]
        ])

        logger.info(f"Preparing Claude analysis with {len(sections_text)} chars")

        # Helper functions for safe formatting
        def format_currency(value):
            return f"${value:,.0f}" if value is not None else "N/A"

        def format_percentage(value):
            return f"{value:.1%}" if value is not None else "N/A"

        def format_ratio(value):
            return f"{value:.2f}" if value is not None else "N/A"

        financial_context = ""
        if financial_data:
            financial_context = f"""
Current Financial Data:
- Market Cap: {format_currency(financial_data.get('market_cap'))}
- Revenue (TTM): {format_currency(financial_data.get('revenue'))}
- Net Income (TTM): {format_currency(financial_data.get('net_income'))}
- Gross Margin: {format_percentage(financial_data.get('gross_margin'))}
- Operating Margin: {format_percentage(financial_data.get('operating_margin'))}
- Debt to Equity: {format_ratio(financial_data.get('debt_to_equity'))}
- Current Ratio: {format_ratio(financial_data.get('current_ratio'))}
"""

        prompt = f"""Analyze this SEC 10-K filing for {company_info['name']} ({company_info['ticker']}).

{financial_context}

Filing Content:
{sections_text}

Provide a structured audit analysis with:
1. A financial health score (0-100) based on the data
2. Key financial metrics extracted from the filing
3. Top 5 risk factors with severity ratings (low/medium/high)
4. 3-5 key insights about the company's position
5. 2-3 actionable recommendations for investors

Respond in this exact JSON format:
{{
    "financial_health_score": <number 0-100>,
    "metrics": {{
        "revenue_growth": "<extracted or N/A>",
        "profit_margin": "<extracted or N/A>",
        "key_ratios": "<extracted or N/A>"
    }},
    "risk_factors": [
        {{
            "category": "<category>",
            "title": "<short title>",
            "description": "<1-2 sentence description>",
            "severity": "<low|medium|high>"
        }}
    ],
    "key_insights": [
        "<insight 1>",
        "<insight 2>"
    ],
    "recommendations": [
        "<recommendation 1>",
        "<recommendation 2>"
    ]
}}"""

        try:
            logger.info(f"Calling Claude API ({self.fast_model})...")
            api_start = time.time()

            response = await self.client.messages.create(
                model=self.fast_model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            api_elapsed = time.time() - api_start
            logger.info(f"Claude API response in {api_elapsed:.1f}s")

            # Extract JSON from response
            content = response.content[0].text

            # Try to parse JSON from the response
            import json
            import re

            # Try to find JSON in markdown code blocks first
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Fallback: Find JSON in response (it might have text before/after)
                json_start = content.find("{")
                json_end = content.rfind("}") + 1

                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                else:
                    logger.error(f"Failed to find JSON in Claude response: {content[:500]}")
                    raise ClaudeError("Failed to extract JSON from response")

            # Parse and validate JSON structure
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from Claude: {json_str[:500]}")
                raise ClaudeError(f"Failed to parse JSON response: {str(e)}")

            # Validate required fields
            required_fields = ["financial_health_score", "risk_factors", "key_insights", "recommendations"]
            missing = [f for f in required_fields if f not in result]
            if missing:
                logger.error(f"Claude response missing required fields: {missing}")
                raise ClaudeError(f"Analysis incomplete - missing: {', '.join(missing)}")

            total_elapsed = time.time() - start_time
            logger.info(f"Analysis complete in {total_elapsed:.1f}s total")
            return result

        except Exception as e:
            error_msg = str(e)
            # Provide user-friendly error messages for common issues
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                raise ClaudeError("Claude API rate limit exceeded. Please wait a moment and try again.")
            elif "authentication" in error_msg.lower() or "401" in error_msg:
                raise ClaudeError("Invalid API key. Please check your ANTHROPIC_API_KEY environment variable.")
            elif "model" in error_msg.lower() or "404" in error_msg:
                raise ClaudeError(f"Model not available. Please check your API access or contact support. Details: {error_msg}")
            else:
                raise ClaudeError(f"Analysis failed: {error_msg}")

    async def chat_stream(
        self,
        message: str,
        context: list[dict],
        history: list[dict]
    ) -> AsyncGenerator[str, None]:
        """Stream a chat response about the company."""

        context_text = "\n\n---\n\n".join([
            f"## {c['name']} (Source: {c['ticker']} {c['fiscal_year']})\n{c['content'][:5000]}"
            for c in context[:3]
        ])

        system_prompt = f"""You are a financial analyst assistant helping users understand SEC filings and company financials.

You have access to the following relevant sections from the company's 10-K filing:

{context_text}

Response Formatting Guidelines:
- Use **bold** for key terms, company names, and important figures
- Use clear section headers with ### when covering multiple topics
- Present lists with bullet points (•) for clarity
- Format financial figures clearly: **$1.5B**, **15.2%**, **$42.50/share**
- Keep paragraphs short (2-3 sentences max) for easy scanning
- Start with a brief summary sentence, then provide details
- Use line breaks between distinct points for readability

Content Guidelines:
- Base your answers on the provided filing content
- Be specific and cite which section you're referencing (e.g., "According to the Risk Factors section...")
- If information isn't in the provided context, clearly state that
- Keep responses informative but scannable - avoid walls of text
- Highlight the most important takeaways"""

        messages = []
        for msg in history[-10:]:  # Limit history
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        messages.append({"role": "user", "content": message})

        try:
            async with self.client.messages.stream(
                model=self.chat_model,
                max_tokens=1500,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            yield f"Error: {str(e)}"


# Singleton instance
_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get or create the Claude client singleton."""
    global _client
    if _client is None:
        _client = ClaudeClient()
    return _client
