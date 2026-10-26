from __future__ import annotations

from crewai import Task


def build_tasks(agents: list) -> list[Task]:
    planner, researcher, budget, advisor = agents

    itinerary_task = Task(
        description="Generate a detailed day-wise itinerary for the trip, including morning, afternoon, evening plans, travel order, duration, and daily travel tips.",
        expected_output="A structured itinerary report with day-by-day details.",
        agent=planner,
        tools=planner.tools,
    )

    research_task = Task(
        description="Research destination details including lodging, dining, attractions, transportation, nearby places, and estimated pricing.",
        expected_output="A destination research report with hotels, restaurants, attractions, and transport guidance.",
        agent=researcher,
        tools=researcher.tools,
    )

    budget_task = Task(
        description="Estimate accommodation, food, transport, activity, and miscellaneous expenses, while suggesting cost optimization ideas.",
        expected_output="A detailed budget report with cost breakdown and total estimated expenses.",
        agent=budget,
        tools=budget.tools,
    )

    guide_task = Task(
        description="Generate a practical travel guide covering packing checklist, weather summary, safety tips, emergency contacts, customs, best time to visit, and things to avoid.",
        expected_output="A polished travel guide with actionable recommendations.",
        agent=advisor,
        tools=advisor.tools,
    )

    return [itinerary_task, research_task, budget_task, guide_task]
