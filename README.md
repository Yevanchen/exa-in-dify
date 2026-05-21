## exa

**Author:** yevanchen
**Version:** 0.0.1
**Type:** tool


### Contact
![Exa Logo](./_assets/image%20copy.png)


### Description

Exa is an AI-powered search tool that enables semantic search and content retrieval using Exa's advanced API.

![Exa Logo](./_assets/image.png)

## Tools

### 1. Exa Search (`exa_search`)

The search endpoint lets you intelligently search the web and extract contents from the results.

#### Parameters:

- **query** (string, required): The search query to find relevant information on the web.
- **search_type** (select, optional, default: "auto"): 
  - Options: "auto", "fast", "deep"
  - Auto is recommended for most queries
- **num_results** (number, optional, default: 10): Maximum number of search results (1-100)
- **include_domains** (string, optional): Comma-separated list of domains to include in results
- **exclude_domains** (string, optional): Comma-separated list of domains to exclude from results
- **start_published_date** (string, optional): Only include results published after this date (YYYY-MM-DD)
- **end_published_date** (string, optional): Only include results published before this date (YYYY-MM-DD)
- **max_age_hours** (number, optional): Freshness control. 0 = always crawl, -1 = cache only, 24 = cache if less than 24h old
- **include_highlights** (boolean, optional, default: true): Return query-relevant excerpts from each result
- **highlights_max_characters** (number, optional): Maximum characters per highlight excerpt
- **include_text** (boolean, optional, default: false): Return full page text (opt-in)
- **category** (select, optional): Focus on specific data categories
  - Options: "company", "people", "research paper", "news", "personal site", "financial report"
- **includeText** (string, optional): Text that must be present in results (up to 5 words)
- **excludeText** (string, optional): Text that must not be present in results (up to 5 words)

### 2. Exa URL Contents (`exa_contents`)

Get the full page contents, summaries, and metadata for a list of URLs.

Returns results from Exa's cache, with automatic live crawling as fallback for uncached pages.

#### Parameters:

- **urls** (string, required): Comma-separated list of URLs to extract content from
- **max_age_hours** (number, optional): Freshness control. 0 = always crawl, -1 = cache only, 24 = cache if less than 24h old
- **include_highlights** (boolean, optional, default: true): Return query-relevant excerpts from each page
- **highlights_max_characters** (number, optional): Maximum characters per highlight excerpt
- **full_page_text** (boolean, optional, default: false): Return full page text (opt-in)
- **number_of_subpages** (number, optional, default: 1): Number of subpages to include in content extraction
- **return_links** (number, optional, default: 1): Number of links to return from each webpage

## Acknowledgements



Special thanks to [@ExaAILabs](https://x.com/ExaAILabs) for providing the powerful API that powers this plugin.



