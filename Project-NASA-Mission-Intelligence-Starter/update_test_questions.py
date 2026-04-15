#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update test_questions.json to include reference answers for enhanced evaluation"""

import json

test_questions = [
  {
    "question": "What was the objective of Apollo 11?",
    "category": "overview",
    "reference": "The objective of Apollo 11 was to land humans on the Moon and return them safely to Earth. This was accomplished when astronauts Neil Armstrong and Buzz Aldrin became the first humans to walk on the lunar surface on July 20, 1969."
  },
  {
    "question": "What caused the Apollo 13 mission emergency?",
    "category": "emergency",
    "reference": "Apollo 13 experienced an oxygen tank explosion in the Service Module two days after launch. This explosion disabled the Command Module and forced the crew to use the Lunar Module as a lifeboat to return safely to Earth."
  },
  {
    "question": "What happened during the Challenger disaster?",
    "category": "disaster",
    "reference": "The Space Shuttle Challenger experienced a catastrophic structural failure 73 seconds after launch on January 28, 1986. An O-ring failure in the right solid rocket booster allowed hot gases to escape, leading to structural failure and loss of the vehicle and all seven crew members."
  },
  {
    "question": "Who were the crew members of Apollo 11?",
    "category": "crew",
    "reference": "The Apollo 11 crew consisted of Neil Armstrong (Commander), Buzz Aldrin (Lunar Module Pilot), and Michael Collins (Command Module Pilot). Armstrong and Aldrin landed on the Moon while Collins remained in orbit around the Moon."
  },
  {
    "question": "What was the timeline of Apollo 11 mission?",
    "category": "timeline",
    "reference": "Apollo 11 was launched on July 16, 1969. The lunar module landed on July 20, 1969. Armstrong and Aldrin spent 2 hours and 31 minutes on the lunar surface. The command module splashed down on July 24, 1969 in the Pacific Ocean."
  }
]

# Write to test_questions.json
with open('test_questions.json', 'w', encoding='utf-8') as f:
    json.dump(test_questions, f, indent=2, ensure_ascii=False)

print('✅ Updated test_questions.json with reference answers for enhanced metrics')
