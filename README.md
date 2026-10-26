# AI Travel Planner

This project is a command-line and FastAPI AI travel planner that uses live location, weather, map, and Google Gemini content generation to create travel plans with start and destination points. It produces both Markdown and PDF reports.

## Architecture

- OpenStreetMap and Open-Meteo provide live location and weather context.
- Google Gemini powers the travel-planning content generation when a valid GEMINI_API_KEY is configured.
- The CLI entrypoint and FastAPI app collect user input and write reports to the outputs directory.

## Project Structure

- crew/: planning flow and report generation
- services/: location, weather, maps, Gemini, Markdown, PDF, and budgeting services
- database/: optional trip history storage
- outputs/: generated reports

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Add your Gemini API key to the project-root `.env` file:
   ```env
   GEMINI_API_KEY=your_key_here
   GEMINI_MODEL=gemini-2.0-flash
   GEMINI_TIMEOUT_SECONDS=30
   DEFAULT_CURRENCY=INR
   ```
4. Run the planner:
   ```bash
   python main.py --start "Bangalore" --destination "Mysore" --days 3 --budget 15000 --travelers 2 --travel-style standard --preferences heritage,food
   ```

## Output

The planner writes:

- outputs/travel_plan.md
- outputs/travel_plan.pdf

## Notes

- The app uses live location and weather-style data sources by default.
- Gemini is the only supported AI provider in this project.
- Trip history can be enabled or disabled via the .env file.
