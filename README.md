# AI Travel Planner

This project is a command-line AI travel planner that uses live location, live weather-style data, and DeepSeek-based content generation to create travel plans with start and destination points. It produces both Markdown and PDF reports.

## Architecture

- OpenStreetMap and Open-Meteo provide live location and weather context.
- DeepSeek powers the travel-planning content generation when a key is provided.
- The CLI entrypoint collects user input and writes reports to the outputs directory.

## Project Structure

- crew/: planning flow and report generation
- services/: location, weather, maps, DeepSeek, Markdown, PDF, and budgeting services
- database/: optional trip history storage
- outputs/: generated reports

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Add your DeepSeek API key to .env if you want AI-generated content beyond the fallback.
4. Run the planner:
   ```bash
   python main.py --start "London" --destination "Paris" --days 4 --budget 2000 --travelers 2 --travel-style standard --preferences culture
   ```

## Output

The planner writes:

- outputs/travel_plan.md
- outputs/travel_plan.pdf

## Notes

- The app uses live location and weather-style data sources by default.
- If no DeepSeek API key is present, the system falls back to offline guidance so the CLI still runs.
- Trip history can be enabled or disabled via the .env file.
