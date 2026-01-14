# README: NLP Project: Challenges of Using LLM for Chess Move Prediction
Sofia Torgovezky      Yaron Kiselman

In this project, we demonstrate the challenges large language models (LLMs) face when playing chess, particularly in 
selecting high quality moves. Classical chess engines rely on search: they construct a game tree, look ahead at possible
continuations, and evaluate them using an internal scoring function. In contrast, LLMs operate differently: they predict
the next word or token based on textual context. This creates a fundamental gap- a move that is common in chess 
commentary or human discourse is not necessarily a strong move, and in some cases may not even be legal.

Due to these differences, we hypothesize that an LLM will exhibit weaker performance compared to a dedicated chess engine. 
This README explains how to generate the dataset and run the evaluation scripts. 

## To set up and run this project, follow the steps below:

### Prerequisites
- Python libraries: `python-chess`, `numpy`, `re`, `json`, `requests`, `io`, `time`, `os`  
- Stockfish chess engine (included in the zip)  
- Google Gemini generative AI model (or any other LLM)  
- A valid API key for the chosen AI model  

### 1. Generating the Dataset
Run `generate_data.py` to create a dataset of chess positions from Grandmaster Magnus Carlsen’s games. 
Positions are analyzed with Stockfish and categorized by difficulty:

- **Easy**: Multiple moves with similar scores (gap >= 0.0 and <0.5)  
- **Normal**: One clearly best move, alternatives slightly worse (gap >= 0.5 and <1.0)  
- **Hard**: One significantly better move (gap >= 1.0)  

The dataset is saved in`.jsonl` formats.


### 2. Running the Evaluation
The `run_eval.py` script evaluates the performance of the LLM by predicting moves for the generated chess 
positions and then scoring them using the move_normalized_score function from evaluation.py. 

Before running the evaluation, you must configure the `run_eval.py` script by making the following changes:

Set your API Key: Configure your Gemini API key on line 10: 
   - API_KEY = "YOUR_API_KEY_HERE". 

Change the AI model to the wanted one (we used gemini flash) in line 18:
   - model = genai.GenerativeModel("gemini-1.5-flash")

Select the Difficulty: Change the variable dif=1 in line 84 accordingly to the difficulty you want to test:
   - 1 = easy  
   - 2 = normal
   - 3 = hard

Reset Scores and Start Index: Ensure the `sum_score` and `start` variables are set to 0 (lines 111-112):
   - sum_score = 0
   - start = 0

Adjust Inner Loop: Ensure the inner loop on line 98 reads `for j in range(1, 4)` to run the evaluation on
all dataset formats.

## IMPORTANT NOTE! Thread Handling
The AI engine operates with internal threads that cannot be directly controlled. As a result, once the evaluation 
finishes, after scores have been generated for the entire dataset at the current difficulty level, the process must 
be terminated manually to ensure a clean exit. Please stop the code when you see the final print:
        `final avg score in date format verbel {score}`
        `final avg in date format board {score}`
        `final avg in date format history {score}`

## Getting final result
The `run_eval.py` script prints the current average score for each round in the dataset (see lines 159-160):
        `print("round",i)
        print("avg score in game "+str(sum_score/(i+1-start)) + " in this format " + txt)`
and in lines 163-164 prints the final scores:
        `final avg score in date format verbel {score}`
        `final avg in date format board {score}`0
        `final avg in date format history {score}`

## Project Files Explained
### generate_data.py
This script generates the chess dataset by downloading games in PGN format from the Chess.com API. 
Positions are classified as "easy," "normal," or "hard" according to a custom evaluation gap metric (explained below).

### evaluation.py: 
This script contains the `move_normalized_score` function, which is the core of the evaluation process. 
It takes a chess board and a move as input, uses Stockfish to evaluate all legal moves, and returns a normalized score 
between 0 and 1 for the given move.

### run_eval.py: 
This is the main evaluation script. It interacts with the Gemini model to get move predictions for 
positions from the dataset. The prompt sent to the AI engine appears at line 142:
`prompt="What would you play in this position just what move make sure it legal move: "+prompt`
Including this message is essential—without it, the engine will only provide an explanation of the current position 
rather than suggesting the next move.
After retrieving the prediction, the script calls `evaluation.py` to compute a normalized score for the move and then 
calculates the average performance across the dataset.

## Custom Metrics
This project uses two key metrics to classify and evaluate chess moves:

Difficulty Classification: The difficulty of a position is determined by a custom metric called the 
evaluation gap, which is the sum of the score differences between the best move and the next two best 
moves: abs(moves[0] - moves[2]) + abs(moves[0] - moves[1]).

   - Easy: Small gap (>=0.0 and <=0.5). Multiple good choices with similar scores.
   - Normal: Medium gap (>=0.5 and <=1.0). A clear best move, but other acceptable options exist.
   - Hard: Large gap (>=1.0). One significantly better move, indicating a forced line of play.

Move Normalized Score: 
The move_normalized_score function returns a value between 0 and 1, where 1 indicates the move is as good
as the best legal move, and 0 indicates it is the worst. This score provides a precise way to measure the
quality of an LLM's move prediction relative to a powerful chess engine.


```python

```
