from __future__ import annotations

from crewai import Agent

from crew.tools import BudgetTool, GeminiTool, LocationTool, WeatherTool


def build_agents() -> list[Agent]:
    gemini_tool = GeminiTool()
    weather_tool = WeatherTool()
    budget_tool = BudgetTool()
    location_tool = LocationTool()

    planner_agent = Agent(
        role="Travel Planner",
        goal="Create a detailed day-wise itinerary with a practical route and travel tips.",
        backstory="You are a senior travel planner who designs efficient itineraries for diverse traveler profiles.",
        tools=[gemini_tool],
        verbose=True,
        allow_delegation=False,
    )

    researcher_agent = Agent(
        role="Travel Researcher",
        goal="Research destination-specific hotels, restaurants, attractions, transportation, and nearby places.",
        backstory="You are a meticulous travel researcher who curates reliable destination information.",
        tools=[gemini_tool, location_tool],
        verbose=True,
        allow_delegation=False,
    )

    budget_agent = Agent(
        role="Budget Analyst",
        goal="Estimate total travel expenses and optimize costs for the chosen travel style.",
        backstory="You are a seasoned budget analyst with experience creating realistic cost models.",
        tools=[gemini_tool, budget_tool],
        verbose=True,
        allow_delegation=False,
    )

    advisor_agent = Agent(
        role="Travel Advisor",
        goal="Provide packing, weather, safety, customs, and emergency guidance tailored to the trip.",
        backstory="You are a practical travel advisor focused on comfort, safety, and preparedness.",
        tools=[gemini_tool, weather_tool],
        verbose=True,
        allow_delegation=False,
    )

    return [planner_agent, researcher_agent, budget_agent, advisor_agent]
