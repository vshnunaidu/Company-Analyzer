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
        # Use Haiku for fast analysis, Sonnet for chat
        self.fast_model = "claude-3-5-haiku-20241022"
        self.chat_model = "claude-3-5-sonnet-20241022"

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

        financial_context = ""
        if financial_data:
            financial_context = f"""
Current Financial Data:
- Market Cap: ${financial_data.get('market_cap', 'N/A'):,.0f}
- Revenue (TTM): ${financial_data.get('revenue', 'N/A'):,.0f}
- Net Income (TTM): ${financial_data.get('net_income', 'N/A'):,.0f}
- Gross Margin: {financial_data.get('gross_margin', 'N/A'):.1%}
- Operating Margin: {financial_data.get('operating_margin', 'N/A'):.1%}
- Debt to Equity: {financial_data.get('debt_to_equity', 'N/A'):.2f}
- Current Ratio: {financial_data.get('current_ratio', 'N/A'):.2f}
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
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            api_elapsed = time.time() - api_start
            logger.info(f"Claude API response in {api_elapsed:.1f}s")

            # Extract JSON from response
            content = response.content[0].text

            # Try to parse JSON from the response
            import json

            # Find JSON in response (it might have text before/after)
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
                total_elapsed = time.time() - start_time
                logger.info(f"Analysis complete in {total_elapsed:.1f}s total")
                return result
            else:
                raise ClaudeError("Failed to extract JSON from response")

        except Exception as e:
            raise ClaudeError(f"Analysis failed: {str(e)}")

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
                max_tokens=1000,
                system=system_prompt,
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
