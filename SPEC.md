# Goal
I want to build complete personal analytics system, that collects data from all areas of my life, including physical activity, finances, health, productivity, learning, and entertainment and allows for deep analysis of trends, promblems, risks, achievements and opportunities. I should be able to build charts and graphs interactively on web interface to visualize the data and insights. This system should help me to improve myself in all areas of my life. The system should be self-hosted and run on my local machine for now. I want to have full control over my data.

# Features
- Collecting data from all areas of my life with APIs from the corresponding services where possible and questionaires for other areas
- Analyzing data and generating insights
- Visualizing data and insights
- Setting goals and tracking progress

# The data to collect
- My subjective experience of the day on a scale of 1-10, this will be collected via a questionnaire on a daily basis. I should be able to write a free form text in addition to strict numerical value, so later I can do NLP analysis of my entries, wordings and find correlations between my mood and other factors.
- Tracking of physical activity: steps, any workouts, sport snacks. This should be collected via questionaires for now and later there should be report on how can I automate this process with API usage.
- Tracking of global metrics: VO2max, Heart Rate Variability, Weight, IQ, psychological test results (like MBTI and Big Five, and others). This should be collected via questionaires only since updates are gonna be rare.
- Tracking of finances: how much money I spent and on what, how many saving I do have.
- Tracking of learning: what I learned, how much I learned, how much I practiced
- Tracking of work: how much I worked and how much I was productive
# Format
The system should be represented as a Web-application (web-site), which I can run on local machine and access via browser. It should have clean intuitive and very interactive interface. The application should have following parts:
- Main page: a section for daily input (questionnaire) and recent outputs with short charts and insights.
- Global view: overview of all areas of life with key metrics and recent changes, where charts and graphs should be interactive.
- Page for each area of life: dedicated sections for each area of my life with inputs, charts and graphs. These pages should be interactive, allowing me to explore the data in different ways.
- Advanced features page: a section for advanced features, such as goal setting and progress tracking. I should be able to set goals for each area of my life and track my progress towards them.

# Tech stack
- FastAPI
- Streamlit
- Python
- PostgreSQL
- SQLite
- Git   

# The conditions and constraints
- The system should be self-hosted and run on my local machine for now.
- I should have full control over my data.
- The system should be secure and private.
- The system should be easy to use and maintain.
- The system should be scalable and extensible.
- The database should be backuped regularly.
- The right approach to data we collect: the more, the better and what is not measured cannot be improved.
- I should be able to export my data in a format that I can use with other tools.
- Finally, after reading this SPEC you should ask me as many questions as needed to fully understand my vision and requirements, and you should create a more detailed SPEC document with user stories, database schema, and API design. After that you should create a project structure and start implementing the project. BUT, before starting implementation, you should always ask for my approval.