import tiktoken
from typing import Dict, Any, Tuple
import pandas as pd

class TokenCostAnalyzer:
    DEFAULT_PROMPT_TOKENS = 1500

    def __init__(self):
        self.model_costs = {
            "llama-3.1-8b-instant": {
                "input_cost": 0.05 / 1_000_000,
                "output_cost": 0.08 / 1_000_000,
                "name": "Llama 3.1 8B Instant"
            },
            "gpt-4o": {
                "input_cost": 2.50 / 1_000_000,
                "output_cost": 1.25 / 1_000_000,
                "name": "GPT-4O"
            },
            "gpt-4o-mini": {
                "input_cost": 0.150 / 1_000_000,
                "output_cost": 0.600 / 1_000_000,
                "name": "GPT-4O Mini"
            }
        }

        # Initialize tiktoken encoder
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        if not text:
            return 0
        return len(self.encoder.encode(text))

    def analyze_article_tokens_and_costs(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze token counts and costs for a single article"""
        # Get content and summary text
        content = article.get('metadata', {}).get('content', '')
        summary = article.get('summary', {}).get('text', '')
        model_used = article.get('summary', {}).get('model_used', 'unknown')

        # Count tokens
        content_tokens = self.count_tokens(content)
        output_tokens = self.count_tokens(summary)

        # Get prompt tokens based on model
        prompt_tokens = self.DEFAULT_PROMPT_TOKENS

        # Total input tokens is content tokens plus prompt tokens
        input_tokens = content_tokens + prompt_tokens

        # Calculate costs if model is known
        model_info = self.model_costs.get(model_used, {})
        input_cost = input_tokens * model_info.get('input_cost', 0) if model_info else 0
        output_cost = output_tokens * model_info.get('output_cost', 0) if model_info else 0

        return {
            'model': model_used,
            'model_name': model_info.get('name', model_used),
            'content_tokens': content_tokens,
            'prompt_tokens': prompt_tokens,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': input_cost + output_cost,
            'article_count': 1  # Add count for aggregation
        }

    def aggregate_costs(self, articles: list) -> Dict[str, Any]:
        """Aggregate token counts and costs across all articles"""
        results = []
        for article in articles:
            analysis = self.analyze_article_tokens_and_costs(article)
            # Only include articles with known models in the results
            if analysis['model'] in self.model_costs:
                results.append(analysis)

        # Convert to DataFrame for easy aggregation
        df = pd.DataFrame(results)

        # If no valid results, return empty totals
        if df.empty:
            return {
                'total_content_tokens': 0,
                'total_prompt_tokens': 0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_input_cost': 0,
                'total_output_cost': 0,
                'total_cost': 0,
                'total_articles': 0,
                'by_model': []
            }

        # Aggregate by model
        model_summary = df.groupby(['model', 'model_name']).agg({
            'content_tokens': 'sum',
            'prompt_tokens': 'sum',
            'input_tokens': 'sum',
            'output_tokens': 'sum',
            'input_cost': 'sum',
            'output_cost': 'sum',
            'total_cost': 'sum',
            'article_count': 'sum'  # Add article count aggregation
        }).reset_index()

        # Calculate totals
        totals = {
            'total_content_tokens': df['content_tokens'].sum(),
            'total_prompt_tokens': df['prompt_tokens'].sum(),
            'total_input_tokens': df['input_tokens'].sum(),
            'total_output_tokens': df['output_tokens'].sum(),
            'total_input_cost': df['input_cost'].sum(),
            'total_output_cost': df['output_cost'].sum(),
            'total_cost': df['total_cost'].sum(),
            'total_articles': df['article_count'].sum(),
            'by_model': model_summary.to_dict('records')
        }

        return totals