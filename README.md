# tech-bros-ai-projects

Repository for all AI-related projects developed by TechBros consulting.

Each project lives under `projects/<project-name>/` and is self-contained: its
own `README.md`, `requirements.txt`, and `.env.example`, so it can be cloned
and installed independently of the rest of the portfolio.

## Projects

- [`asistente_ventas_inmobiliario`](projects/asistente_ventas_inmobiliario/README.md) —
  conversational bot (Telegram/Discord) that answers natural-language questions
  about apartment availability, backed by a scraping/ETL pipeline that feeds a
  SQLite database.

- [`empleabilidad-ia`](projects/empleabilidad-ia/README.md) —
  labour-market study measuring AI skill demand in Peru. Scrapes real job
  postings, structures them with an LLM into a skills taxonomy, and classifies
  each posting as an AI-native role, a traditional role that now requires AI, or
  neither. 544 postings, 269 companies.
