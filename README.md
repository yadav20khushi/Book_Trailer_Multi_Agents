# Follow these instructions to create a setup in your system:

1. git clone https://github.com/yadav20khushi/Book_Trailer_Multi_Agents.git
2. git pull origin main
2. pip install -r requirements.txt
3. Create a .env file
4. To put the book title name, in the agents.py;

       if __name__ == "__main__":
       result = crew.kickoff(inputs={"book_title": "Dune"}) <---- Enter book title here
       print("######################")
       print(result)

5. Finally, in your terminal do 'python agents.py'

You will see the agents running and what decisions they are taking and what task is being executed in the terminal,
at the end you will see in yellow (if pycharm) feedback agent asking for your feedback
once you give the feedback, you will finally see the result viz the veo3 prompt in json.
Afer this the script will terminate

NOTE: When you want to run again, do python agents.py again and *remember to put the new book title above* and **Keep feedback concise; the system is optimized for short, high‑signal inputs.**

Letta_Memory: https://app.letta.com/projects/genesis-pre-mvp/agents/agent-f6f422c4-9c75-4f19-b345-288d05b4fe87 
Here, you will see the agent storing all the decisions and feedback, storing in its respective memory blocks.
I have already ran it for the book 'DUNE' so now when you run the script for a different book, the agents will
first ask letta to give them personalized feedback using 'memory_fetch' and letta will analyze what has been stored
in memory and generate a feedback for the agents (only applicable for book_specialist, creative_dir, producer agent)

