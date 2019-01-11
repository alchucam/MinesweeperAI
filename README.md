# MinesweeperAI
CS 271P AI Project <br/>
AI agent that solves classic Minesweeper game.

## Description

This is a school project about AI (Artificial Intelligence).
There are three different difficulty modes (worlds):
- Beginner: 8 x 8 tiles with 10 mines. The AI agent can solve it with 86.6%
- Intermediate: 16 x 16 tiles with 40 mines. The AI agent can solve it with 82.6%
- Expert: 16 x 30 tiles with 99 mines. The AI agent can solve it with 30.3%
The success rates are determined by testing with 1000 random boards for each difficulty.

<img src="/images/image.JPG" width="80%">

## How it works

MinesweeperAI works its logic in three phases. <br/>
- First phase: Solves the obvious one (i.e. a tile with one unopened neighbor tile with one mine left to discover) in a BFS manner <br/>
- Second phase: assumption. Once there are no obvious ones to solve, then the AI will sort the boundary opened tiles by the minimum remaining values (MRV), and propagate from each possible pattern for each sorted tiles. At the end, such propagation will reveal a consistent results for certain tiles even in all different possible pattern for the sorted tile. <br/>
- Third phase: guess. When even the assumption does not work, the most likely being non-bomb tile will be uncovered. The function finds the tile that has the lowest remaining bomb per unopened tile ratio. <br/>
Afterwards, the AI will repeat from the first phase to third phase again. <br/>

## Setup

In the worldGenerator/ folder, run the following command to create 1000 random boards for each three different difficulty.
```
./generateTournament.sh
```
<br/>

In the Minesweeper_Python/src/ folder, run the following command to run the AI agent on the boards previously created. After the run, it will show you the final score of how AI agent performs on each diffficulty.
```
python3 Main.py -f ../../WorldGenerator/Problems/ -v
```
<br/>

## Conclusion & Remarks

The AI agent performs well overall; however, the difficulty of the performance appears when the agent is in a situation to make an inevitable 'guess'. The agent's performance can be enhancecd by calculating the detailed probability with every possible cases. Nevertheless, I believe the agent demonstrates its true aspect of being AI in this project. <br/>

## Programming Language
Python

## Tools/IDE
Emacs
